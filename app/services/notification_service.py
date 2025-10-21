import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.note import Note
from app.models.notification_schedule import NotificationSchedule
from app.services.telegram_service import TelegramService
from app.services.lunar_calendar import LunarCalendarService
from app.services.feng_shui_service import FengShuiService
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications with new schedule-based system"""
    
    def __init__(self):
        self.telegram_service = TelegramService()
    
    def create_notification_schedule_for_note(self, db: Session, note: Note) -> NotificationSchedule:
        """Create notification schedule for a note (new system)"""
        if not note.enable_notification or not note.notification_days_before:
            return None
        
        # Check if schedule already exists
        existing_schedule = db.query(NotificationSchedule).filter(
            NotificationSchedule.note_id == note.id
        ).first()
        
        if existing_schedule:
            logger.info(f"Schedule already exists for note {note.id}")
            return existing_schedule
        
        # Calculate total notifications needed (from notification_days_before down to 0)
        total_needed = note.notification_days_before + 1  # +1 for day 0
        
        # Create schedule
        schedule = NotificationSchedule(
            note_id=note.id,
            total_notifications_needed=total_needed,
            notifications_sent=0,
            current_days_before=note.notification_days_before,
            current_year=note.solar_date.year,  # Track current year for yearly repeat
            current_month=note.solar_date.month,  # Track current month for monthly repeat
            is_completed=False
        )
        
        db.add(schedule)
        db.commit()
        
        logger.info(f"Created notification schedule for note {note.id}: {total_needed} notifications needed, starting from {note.notification_days_before} days before, year {note.solar_date.year}")
        return schedule
    
    def get_schedules_ready_for_notification(self, db: Session) -> List[NotificationSchedule]:
        """Get schedules that are ready for next notification"""
        now = datetime.now()
        
        schedules = db.query(NotificationSchedule).join(Note).filter(
            NotificationSchedule.is_completed == False,
            Note.enable_notification == True
        ).all()
        
        ready_schedules = []
        for schedule in schedules:
            note = schedule.note
            
            # Calculate the event date for current year/month
            try:
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month
                )
            except ValueError:
                # Handle invalid dates (e.g., 31st of Feb)
                from calendar import monthrange
                last_day = monthrange(schedule.current_year, schedule.current_month)[1]
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month,
                    day=min(note.solar_date.day, last_day)
                )
            
            # Calculate when this notification should be sent
            notification_date = event_date_this_period - timedelta(days=schedule.current_days_before)
            
            # Parse notification time
            try:
                time_parts = settings.notification_time.split(":")
                notification_hour = int(time_parts[0])
                notification_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            except:
                notification_hour, notification_minute = 9, 0
            
            scheduled_time = datetime.combine(
                notification_date, 
                datetime.min.time().replace(hour=notification_hour, minute=notification_minute)
            )
            
            # Check if it's time to send this notification
            if scheduled_time <= now:
                # Additional check: Don't send if already sent today
                if schedule.last_notification_sent:
                    last_sent_date = schedule.last_notification_sent.date()
                    today = now.date()
                    
                    # If we already sent today, skip (prevent duplicate on restart)
                    if last_sent_date == today:
                        continue
                
                ready_schedules.append(schedule)
                logger.info(f"📅 Schedule {schedule.id}: {note.title} ({schedule.current_days_before}d, year {schedule.current_year})")
        
        return ready_schedules
    
    def send_notification_for_schedule(self, db: Session, schedule: NotificationSchedule) -> bool:
        """Send notification for a schedule and update progress"""
        note = schedule.note
        user = note.user
        
        if not user:
            logger.error(f"No user found for note {note.id}")
            return False
        
        success_count = 0
        total_attempts = 0
        
        # Send Telegram notification if enabled
        if user.telegram_notifications and user.telegram_chat_id and settings.telegram_bot_token:
            total_attempts += 1
            if self._send_telegram_for_schedule(schedule):
                success_count += 1
        
        # Send Email notification if enabled
        if user.email_notifications and settings.smtp_username:
            total_attempts += 1
            if self._send_email_for_schedule(schedule):
                success_count += 1
        
        # Update schedule progress
        if success_count > 0:
            schedule.notifications_sent += 1
            schedule.last_notification_sent = datetime.now()
            
            # Move to next notification or complete/repeat
            if schedule.current_days_before > 0:
                schedule.current_days_before -= 1
                logger.info(f"➡️ Schedule {schedule.id}: Next {schedule.current_days_before}d")
            else:
                # Completed current cycle
                if note.monthly_repeat:
                    # Reset for next month
                    schedule.current_month += 1
                    if schedule.current_month > 12:
                        schedule.current_month = 1
                        schedule.current_year += 1
                    schedule.current_days_before = note.notification_days_before
                    schedule.notifications_sent = 0
                    schedule.is_completed = False
                    logger.info(f"🔄 Schedule {schedule.id}: Reset for {schedule.current_year}/{schedule.current_month:02d}")
                elif note.yearly_repeat:
                    # Reset for next year
                    schedule.current_year += 1
                    schedule.current_days_before = note.notification_days_before
                    schedule.notifications_sent = 0
                    schedule.is_completed = False
                    logger.info(f"🔄 Schedule {schedule.id}: Reset for year {schedule.current_year}")
                else:
                    # Mark as completed
                    schedule.is_completed = True
                    logger.info(f"✅ Schedule {schedule.id}: Completed")
            
            db.commit()
            return True
        
        return False
    
    def _send_telegram_for_schedule(self, schedule: NotificationSchedule) -> bool:
        """Send Telegram notification for schedule"""
        try:
            note = schedule.note
            user = note.user
            
            # Calculate event date for current year/month
            try:
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month
                )
            except ValueError:
                # Handle invalid dates
                from calendar import monthrange
                last_day = monthrange(schedule.current_year, schedule.current_month)[1]
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month,
                    day=min(note.solar_date.day, last_day)
                )
            
            lunar_info = LunarCalendarService.get_lunar_info(event_date_this_period)
            
            # Get personalized feng shui if user has birth date
            feng_shui_content = ""
            if user.birth_date:
                personal_feng_shui = FengShuiService.get_personal_feng_shui_advice(
                    user.birth_date, event_date_this_period
                )
                
                # Check for birthday
                birthday_msg = ""
                if personal_feng_shui.get('birthday_reminder'):
                    birthday_msg = f"\n🎉 {personal_feng_shui['birthday_reminder']['message']}"
                
                feng_shui_content = f"""🔮 Phong thủy cá nhân:
• Mệnh: {personal_feng_shui['user_info']['birth_year_element']} ({personal_feng_shui['user_info']['birth_year_desc']})
• Can Chi ngày: {personal_feng_shui['day_info']['can_chi']}
• Tương thích: {personal_feng_shui['compatibility']['level']} ({personal_feng_shui['compatibility']['score']}/100)
• Màu may mắn: {', '.join(personal_feng_shui['personal_advice']['colors'][:3])}
• Nên làm: {', '.join(personal_feng_shui['personal_advice']['activities']['recommended'][:2])}
• Lời khuyên: {personal_feng_shui['personal_advice']['overall_advice']}{birthday_msg}"""
            else:
                # General feng shui analysis
                feng_shui_analysis = FengShuiService.get_daily_feng_shui_analysis(event_date_this_period)
                feng_shui_content = f"""🔮 Phong thủy:
• Can Chi: {feng_shui_analysis['can_chi']}
• Ngũ hành: {feng_shui_analysis['element'].value}
• Màu may mắn: {', '.join(feng_shui_analysis['lucky_colors'][:3])}
• Hướng tốt: {feng_shui_analysis['lucky_direction']}
• Nên làm: {', '.join(feng_shui_analysis['lucky_activities'][:2])}"""
            
            if schedule.current_days_before == 0:
                time_msg = "⏰ Hôm nay là ngày sự kiện!"
            else:
                time_msg = f"⏰ Thông báo trước {schedule.current_days_before} ngày - Còn {schedule.current_days_before} ngày nữa!"
            
            # Add repeat info
            repeat_info = ""
            if note.monthly_repeat:
                if schedule.current_year != note.solar_date.year or schedule.current_month != note.solar_date.month:
                    repeat_info = f"\n📅 Lặp lại hàng tháng - {schedule.current_year}/{schedule.current_month:02d}"
                else:
                    repeat_info = f"\n📅 Sẽ lặp lại hàng tháng"
            elif note.yearly_repeat:
                if schedule.current_year != note.solar_date.year:
                    repeat_info = f"\n🔄 Lặp lại hàng năm - Năm {schedule.current_year}"
                else:
                    repeat_info = f"\n🔄 Sẽ lặp lại hàng năm"
            
            message = f"""🔔 Nhắc nhở: {note.title}

📝 Nội dung: {note.content or ""}

📅 Ngày dương: {event_date_this_period.strftime('%d/%m/%Y')}
🌙 Ngày âm: {lunar_info['lunar_date_str']}

{feng_shui_content}

{time_msg}{repeat_info}

📊 Tiến trình: {schedule.notifications_sent + 1}/{schedule.total_notifications_needed}"""
            
            success = self.telegram_service.send_message_sync(
                message=message,
                chat_id=user.telegram_chat_id
            )
            
            if success:
                logger.info(f"📱 Telegram → Schedule {schedule.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending Telegram for schedule {schedule.id}: {e}")
            return False
    
    def _send_email_for_schedule(self, schedule: NotificationSchedule) -> bool:
        """Send Email notification for schedule"""
        try:
            note = schedule.note
            user = note.user
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.from_email
            msg['To'] = user.email
            
            # Create subject
            if schedule.current_days_before == 0:
                subject = f"🔔 Hôm nay: {note.title}"
            else:
                subject = f"🔔 Nhắc trước {schedule.current_days_before} ngày: {note.title}"
            
            msg['Subject'] = subject
            
            # Get lunar info and feng shui analysis
            try:
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month
                )
            except ValueError:
                from calendar import monthrange
                last_day = monthrange(schedule.current_year, schedule.current_month)[1]
                event_date_this_period = note.solar_date.replace(
                    year=schedule.current_year,
                    month=schedule.current_month,
                    day=min(note.solar_date.day, last_day)
                )
            
            lunar_info = LunarCalendarService.get_lunar_info(event_date_this_period)
            
            # Get personalized feng shui if user has birth date
            feng_shui_data = None
            feng_shui_summary = ""
            
            if user.birth_date:
                personal_feng_shui = FengShuiService.get_personal_feng_shui_advice(
                    user.birth_date, event_date_this_period
                )
                feng_shui_data = personal_feng_shui
                
                # Check for birthday
                birthday_msg = ""
                if personal_feng_shui.get('birthday_reminder'):
                    birthday_msg = f"\n🎉 {personal_feng_shui['birthday_reminder']['message']}"
                
                feng_shui_summary = f"""
🔮 Phong thủy cá nhân ngày {event_date_this_period.strftime('%d/%m/%Y')}:
- Mệnh: {personal_feng_shui['user_info']['birth_year_element']} ({personal_feng_shui['user_info']['birth_year_desc']})
- Can Chi ngày: {personal_feng_shui['day_info']['can_chi']}
- Tương thích: {personal_feng_shui['compatibility']['level']} ({personal_feng_shui['compatibility']['score']}/100)
- Màu may mắn: {', '.join(personal_feng_shui['personal_advice']['colors'][:3])}
- Nên làm: {', '.join(personal_feng_shui['personal_advice']['activities']['recommended'][:2])}
- Lời khuyên: {personal_feng_shui['personal_advice']['overall_advice']}{birthday_msg}
                """.strip()
            else:
                feng_shui_analysis = FengShuiService.get_daily_feng_shui_analysis(event_date_this_period)
                feng_shui_data = feng_shui_analysis
                
                feng_shui_summary = f"""
🔮 Phong thủy ngày {event_date_this_period.strftime('%d/%m/%Y')}:
- Can Chi: {feng_shui_analysis['can_chi']}
- Ngũ hành: {feng_shui_analysis['element'].value}
- Màu may mắn: {', '.join(feng_shui_analysis['lucky_colors'][:3])}
- Hướng tốt: {feng_shui_analysis['lucky_direction']}
- Nên làm: {', '.join(feng_shui_analysis['lucky_activities'][:2])}
                """.strip()
            
            # Create plain text version
            if schedule.current_days_before == 0:
                time_msg = "Hôm nay là ngày sự kiện!"
            else:
                time_msg = f"Thông báo trước {schedule.current_days_before} ngày - Còn {schedule.current_days_before} ngày nữa!"

            text_body = f"""
Xin chào!

Đây là lời nhắc nhở về ghi chú của bạn:

Tiêu đề: {note.title}
Nội dung: {note.content or ""}

Ngày dương: {event_date_this_period.strftime('%d/%m/%Y')}
Ngày âm: {lunar_info['lunar_date_str']}

{feng_shui_summary}

{time_msg}

Tiến trình: {schedule.notifications_sent + 1}/{schedule.total_notifications_needed}

Trân trọng,
Hệ thống Calendar
            """.strip()
            
            # Create HTML version
            try:
                from jinja2 import Environment, FileSystemLoader
                import os
                
                template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'email')
                env = Environment(loader=FileSystemLoader(template_dir))
                template = env.get_template('simple_notification.html')
                
                html_body = template.render(
                    note_title=note.title,
                    note_content=note.content or "",
                    solar_date=event_date_this_period.strftime('%d/%m/%Y'),
                    lunar_date=lunar_info['lunar_date_str'],
                    days_before=schedule.current_days_before,
                    progress=f"{schedule.notifications_sent + 1}/{schedule.total_notifications_needed}",
                    feng_shui_data=feng_shui_data,
                    user_birth_date=user.birth_date
                )
                
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
            except Exception:
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            
            # Send email
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            text = msg.as_string()
            server.sendmail(settings.from_email, user.email, text)
            server.quit()
            
            logger.info(f"📧 Email → Schedule {schedule.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email for schedule {schedule.id}: {e}")
            return False
    
    def process_all_ready_schedules(self, db: Session) -> dict:
        """Process all schedules ready for notification"""
        ready_schedules = self.get_schedules_ready_for_notification(db)
        
        if not ready_schedules:
            return {"processed": 0, "failed": 0, "message": "Không có thông báo nào cần gửi"}
        
        processed = 0
        failed = 0
        
        for schedule in ready_schedules:
            try:
                if self.send_notification_for_schedule(db, schedule):
                    processed += 1
                else:
                    failed += 1
                    
                # Add delay between notifications
                import time, random
                delay = random.uniform(2.0, 4.0)
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error processing schedule {schedule.id}: {e}")
                failed += 1
        
        return {
            "processed": processed,
            "failed": failed,
            "total": len(ready_schedules),
            "message": f"Đã xử lý {processed}/{len(ready_schedules)} lịch thông báo"
        }
    
    def cleanup_old_completed_schedules(self, db: Session, days_old: int = 30) -> int:
        """Clean up completed schedules older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find old completed schedules
        old_schedules = db.query(NotificationSchedule).filter(
            NotificationSchedule.is_completed == True,
            NotificationSchedule.updated_at < cutoff_date
        ).all()
        
        count = len(old_schedules)
        
        # Delete old schedules
        for schedule in old_schedules:
            db.delete(schedule)
        
        db.commit()
        logger.info(f"🧹 Cleaned {count} old schedules")
        
        return count
    
    def get_schedule_statistics(self, db: Session, user_id: int = None) -> dict:
        """Get notification schedule statistics"""
        query = db.query(NotificationSchedule).join(Note)
        
        if user_id:
            query = query.filter(Note.user_id == user_id)
        
        all_schedules = query.all()
        
        stats = {
            "total": len(all_schedules),
            "completed": len([s for s in all_schedules if s.is_completed]),
            "active": len([s for s in all_schedules if not s.is_completed]),
            "total_notifications_sent": sum(s.notifications_sent for s in all_schedules),
            "average_progress": 0
        }
        
        if stats["total"] > 0:
            stats["average_progress"] = sum(s.progress_percentage for s in all_schedules) / stats["total"]
        
        return stats
    

