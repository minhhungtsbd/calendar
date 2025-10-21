"""
Telegram Bot Handler - Quản lý ghi chú qua Telegram Bot
Hỗ trợ: Thêm, xem, sửa, xóa ghi chú với inline keyboard menu
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.note import Note, CalendarType
from app.services.lunar_calendar import LunarCalendarService
from app.services.notification_service import NotificationService
from app.config import settings

logger = logging.getLogger(__name__)

# Conversation states
(
    ASKING_TITLE,
    ASKING_CONTENT,
    ASKING_DATE,
    ASKING_NOTIFICATION,
    ASKING_REPEAT_TYPE,
    ASKING_DAYS_BEFORE,
    ASKING_DELETE_CONFIRM,
    ASKING_EDIT_FIELD,
    ASKING_EDIT_VALUE,
) = range(9)


class TelegramBotHandler:
    """Handler cho Telegram Bot với menu và CRUD operations"""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.api_url = settings.telegram_api_url
        self.application = None

    def get_user_by_telegram_id(self, db: Session, telegram_id: int) -> Optional[User]:
        """Lấy user từ database theo telegram chat ID"""
        return db.query(User).filter(User.telegram_chat_id == str(telegram_id)).first()

    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Tạo menu chính với inline keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Thêm ghi chú", callback_data="add_note"),
                InlineKeyboardButton("📋 Xem tất cả", callback_data="list_notes"),
            ],
            [
                InlineKeyboardButton("⏰ Sắp tới", callback_data="upcoming_notes"),
                InlineKeyboardButton("🔍 Tìm kiếm", callback_data="search_notes"),
            ],
            [
                InlineKeyboardButton("ℹ️ Trợ giúp", callback_data="help"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho /start command"""
        user = update.effective_user
        
        welcome_message = f"""
👋 Xin chào <b>{user.first_name}</b>!

🗓️ Chào mừng đến với <b>Lịch Âm Dương Bot</b>

<i>Bot giúp bạn quản lý ghi chú và nhận thông báo nhắc nhở tự động.</i>

🔹 <b>Chức năng chính:</b>
• Thêm ghi chú mới
• Xem danh sách ghi chú
• Xem ghi chú sắp tới
• Xóa/sửa ghi chú
• Nhận thông báo tự động

📱 <b>Telegram ID:</b> <code>{user.id}</code>

⚙️ <i>Lưu ý: Bạn cần liên kết Telegram ID này với tài khoản trên website để sử dụng đầy đủ tính năng.</i>

Chọn chức năng từ menu bên dưới:
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.HTML,
            reply_markup=self.get_main_menu_keyboard(),
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho /help command"""
        help_text = """
📖 <b>Hướng dẫn sử dụng Bot</b>

<b>Commands:</b>
/start - Khởi động bot và xem menu
/help - Xem hướng dẫn này
/add - Thêm ghi chú mới
/list - Xem danh sách ghi chú
/upcoming - Xem ghi chú sắp tới
/cancel - Hủy thao tác hiện tại

<b>Thêm ghi chú:</b>
1. Nhấn "➕ Thêm ghi chú" hoặc /add
2. Nhập tiêu đề ghi chú
3. Nhập nội dung (hoặc gửi "skip" để bỏ qua)
4. Nhập ngày (định dạng: DD/MM/YYYY hoặc YYYY-MM-DD)
5. Chọn có muốn thông báo không
6. Nếu có, chọn kiểu lặp lại
7. Chọn số ngày nhắc trước

<b>Xem ghi chú:</b>
• Menu → 📋 Xem tất cả
• Menu → ⏰ Sắp tới (7 ngày tới)

<b>Sửa/Xóa ghi chú:</b>
• Chọn ghi chú từ danh sách
• Chọn "✏️ Sửa" hoặc "🗑️ Xóa"

<b>Liên kết tài khoản:</b>
1. Đăng nhập vào website: https://calendar.minhhungtsbd.me/
2. Vào Cài đặt → Thông báo
3. Nhập Telegram ID: <code>{}</code>
4. Lưu cài đặt

Cần hỗ trợ? Liên hệ: support@minhhungtsbd.me
        """
        
        telegram_id = update.effective_user.id
        
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.reply_text(
                help_text.format(telegram_id),
                parse_mode=ParseMode.HTML,
                reply_markup=self.get_main_menu_keyboard(),
            )
        else:
            await update.message.reply_text(
                help_text.format(telegram_id),
                parse_mode=ParseMode.HTML,
                reply_markup=self.get_main_menu_keyboard(),
            )

    async def main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler cho callback của main menu"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "add_note":
            return await self.start_add_note(update, context)
        elif callback_data == "list_notes":
            return await self.list_notes(update, context)
        elif callback_data == "upcoming_notes":
            return await self.upcoming_notes(update, context)
        elif callback_data == "search_notes":
            await query.message.reply_text(
                "🔍 Tính năng tìm kiếm đang được phát triển...",
                reply_markup=self.get_main_menu_keyboard(),
            )
        elif callback_data == "help":
            return await self.help_command(update, context)

    # ==================== ADD NOTE FLOW ====================
    
    async def start_add_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bắt đầu flow thêm ghi chú"""
        query = update.callback_query
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        # Kiểm tra user có liên kết tài khoản chưa
        db = SessionLocal()
        try:
            user = self.get_user_by_telegram_id(db, update.effective_user.id)
            if not user:
                await message.reply_text(
                    "❌ <b>Bạn chưa liên kết tài khoản!</b>\n\n"
                    f"📱 Telegram ID của bạn: <code>{update.effective_user.id}</code>\n\n"
                    "Vui lòng:\n"
                    "1. Đăng nhập vào website: https://calendar.minhhungtsbd.me/\n"
                    "2. Vào Cài đặt → Thông báo\n"
                    "3. Nhập Telegram ID ở trên\n"
                    "4. Lưu và quay lại bot",
                    parse_mode=ParseMode.HTML,
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return ConversationHandler.END
            
            context.user_data["user_id"] = user.id
            context.user_data["note_data"] = {}
            
        finally:
            db.close()
        
        await message.reply_text(
            "➕ <b>Thêm ghi chú mới</b>\n\n"
            "Nhập <b>tiêu đề</b> cho ghi chú của bạn:\n\n"
            "<i>Gửi /cancel để hủy</i>",
            parse_mode=ParseMode.HTML,
        )
        
        return ASKING_TITLE

    async def receive_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận tiêu đề ghi chú"""
        title = update.message.text.strip()
        
        if len(title) > 200:
            await update.message.reply_text(
                "❌ Tiêu đề quá dài (tối đa 200 ký tự).\nVui lòng nhập lại:"
            )
            return ASKING_TITLE
        
        context.user_data["note_data"]["title"] = title
        
        await update.message.reply_text(
            f"✅ Tiêu đề: <b>{title}</b>\n\n"
            "Nhập <b>nội dung</b> ghi chú:\n\n"
            "<i>Gửi 'skip' để bỏ qua</i>",
            parse_mode=ParseMode.HTML,
        )
        
        return ASKING_CONTENT

    async def receive_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận nội dung ghi chú"""
        content = update.message.text.strip()
        
        if content.lower() != "skip":
            context.user_data["note_data"]["content"] = content
        else:
            context.user_data["note_data"]["content"] = ""
        
        await update.message.reply_text(
            "📅 Nhập <b>ngày</b> cho ghi chú:\n\n"
            "Định dạng: <code>DD/MM/YYYY</code> hoặc <code>YYYY-MM-DD</code>\n"
            "Ví dụ: <code>25/12/2025</code> hoặc <code>2025-12-25</code>\n\n"
            "<i>Gửi /cancel để hủy</i>",
            parse_mode=ParseMode.HTML,
        )
        
        return ASKING_DATE

    async def receive_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận ngày ghi chú"""
        date_str = update.message.text.strip()
        
        # Parse date
        note_date = None
        for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
            try:
                note_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        
        if not note_date:
            await update.message.reply_text(
                "❌ Định dạng ngày không hợp lệ!\n\n"
                "Vui lòng nhập lại theo định dạng:\n"
                "• <code>DD/MM/YYYY</code> (ví dụ: 25/12/2025)\n"
                "• <code>YYYY-MM-DD</code> (ví dụ: 2025-12-25)",
                parse_mode=ParseMode.HTML,
            )
            return ASKING_DATE
        
        context.user_data["note_data"]["solar_date"] = note_date
        
        # Hiển thị thông tin ngày âm
        lunar_info = LunarCalendarService.get_lunar_info(note_date)
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Có", callback_data="notif_yes"),
                InlineKeyboardButton("❌ Không", callback_data="notif_no"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Ngày: <b>{note_date.strftime('%d/%m/%Y')}</b>\n"
            f"🌙 Âm lịch: <b>{lunar_info['lunar_date_str']}</b>\n\n"
            "🔔 Bạn có muốn nhận <b>thông báo nhắc nhở</b> không?",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
        
        return ASKING_NOTIFICATION

    async def receive_notification_choice(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Nhận lựa chọn có muốn thông báo không"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "notif_no":
            context.user_data["note_data"]["enable_notification"] = False
            context.user_data["note_data"]["notification_days_before"] = 0
            context.user_data["note_data"]["monthly_repeat"] = False
            context.user_data["note_data"]["yearly_repeat"] = False
            
            # Lưu ghi chú ngay
            return await self.save_note(update, context)
        else:
            context.user_data["note_data"]["enable_notification"] = True
            
            keyboard = [
                [InlineKeyboardButton("📅 Hàng tháng", callback_data="repeat_monthly")],
                [InlineKeyboardButton("🔄 Hàng năm", callback_data="repeat_yearly")],
                [InlineKeyboardButton("❌ Không lặp", callback_data="repeat_none")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "🔄 Chọn <b>kiểu lặp lại</b>:\n\n"
                "📅 <b>Hàng tháng:</b> Lặp mỗi tháng vào cùng ngày\n"
                "🔄 <b>Hàng năm:</b> Lặp mỗi năm vào cùng ngày\n"
                "❌ <b>Không lặp:</b> Chỉ thông báo 1 lần",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            
            return ASKING_REPEAT_TYPE

    async def receive_repeat_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận loại lặp lại"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "repeat_monthly":
            context.user_data["note_data"]["monthly_repeat"] = True
            context.user_data["note_data"]["yearly_repeat"] = False
            repeat_text = "📅 Lặp hàng tháng"
        elif query.data == "repeat_yearly":
            context.user_data["note_data"]["monthly_repeat"] = False
            context.user_data["note_data"]["yearly_repeat"] = True
            repeat_text = "🔄 Lặp hàng năm"
        else:
            context.user_data["note_data"]["monthly_repeat"] = False
            context.user_data["note_data"]["yearly_repeat"] = False
            repeat_text = "❌ Không lặp"
        
        keyboard = [
            [InlineKeyboardButton("1 ngày", callback_data="days_1")],
            [InlineKeyboardButton("3 ngày", callback_data="days_3")],
            [InlineKeyboardButton("5 ngày", callback_data="days_5")],
            [InlineKeyboardButton("7 ngày", callback_data="days_7")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"✅ {repeat_text}\n\n"
            "⏰ Chọn <b>số ngày nhắc trước</b>:\n\n"
            "<i>Ví dụ: Chọn '3 ngày' sẽ nhắc từ 3 ngày trước đến ngày sự kiện (tổng 4 lần)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
        
        return ASKING_DAYS_BEFORE

    async def receive_days_before(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận số ngày nhắc trước"""
        query = update.callback_query
        await query.answer()
        
        days = int(query.data.split("_")[1])
        context.user_data["note_data"]["notification_days_before"] = days
        
        return await self.save_note(update, context)

    async def save_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lưu ghi chú vào database"""
        query = update.callback_query if update.callback_query else None
        message = query.message if query else update.message
        
        note_data = context.user_data["note_data"]
        user_id = context.user_data["user_id"]
        
        db = SessionLocal()
        try:
            # Tạo note mới
            note = Note(
                user_id=user_id,
                title=note_data["title"],
                content=note_data.get("content", ""),
                solar_date=note_data["solar_date"],
                calendar_type=CalendarType.SOLAR,
                enable_notification=note_data.get("enable_notification", False),
                notification_days_before=note_data.get("notification_days_before", 0),
                monthly_repeat=note_data.get("monthly_repeat", False),
                yearly_repeat=note_data.get("yearly_repeat", False),
            )
            
            db.add(note)
            db.commit()
            db.refresh(note)
            
            # Tạo notification schedule nếu cần
            if note.enable_notification:
                notification_service = NotificationService()
                notification_service.create_notification_schedule_for_note(db, note)
            
            # Tạo thông báo thành công
            lunar_info = LunarCalendarService.get_lunar_info(note.solar_date)
            
            repeat_info = ""
            if note.monthly_repeat:
                repeat_info = "\n📅 Lặp lại hàng tháng"
            elif note.yearly_repeat:
                repeat_info = "\n🔄 Lặp lại hàng năm"
            
            notif_info = ""
            if note.enable_notification:
                notif_info = f"\n🔔 Nhắc trước {note.notification_days_before} ngày{repeat_info}"
            
            success_message = (
                "✅ <b>Đã tạo ghi chú thành công!</b>\n\n"
                f"📝 <b>Tiêu đề:</b> {note.title}\n"
                f"📄 <b>Nội dung:</b> {note.content or '<i>Không có</i>'}\n"
                f"📅 <b>Ngày dương:</b> {note.solar_date.strftime('%d/%m/%Y')}\n"
                f"🌙 <b>Ngày âm:</b> {lunar_info['lunar_date_str']}"
                f"{notif_info}"
            )
            
            await message.reply_text(
                success_message,
                parse_mode=ParseMode.HTML,
                reply_markup=self.get_main_menu_keyboard(),
            )
            
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            await message.reply_text(
                f"❌ Lỗi khi lưu ghi chú: {str(e)}",
                reply_markup=self.get_main_menu_keyboard(),
            )
        finally:
            db.close()
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END

    # ==================== LIST & VIEW NOTES ====================
    
    async def list_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Đápủng danh sách tất cả ghi chú"""
        query = update.callback_query
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        db = SessionLocal()
        try:
            user = self.get_user_by_telegram_id(db, update.effective_user.id)
            if not user:
                await message.reply_text(
                    "❌ Bạn chưa liên kết tài khoản!",
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            notes = (
                db.query(Note)
                .filter(Note.user_id == user.id, Note.is_active == True)
                .order_by(Note.solar_date.desc())
                .limit(20)
                .all()
            )
            
            if not notes:
                await message.reply_text(
                    "📝 <b>Không có ghi chú nào</b>\n\n"
                    "Bạn chưa có ghi chú nào. Hãy tạo ghi chú đầu tiên của bạn!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            message_text = f"📋 <b>Danh sách ghi chú</b> ({len(notes)} ghi chú)\n\n"
            
            keyboard = []
            for note in notes:
                lunar_info = LunarCalendarService.get_lunar_info(note.solar_date)
                
                # Icon based on notification settings
                icon = "🔔" if note.enable_notification else "📝"
                if note.monthly_repeat:
                    icon = "📅"
                elif note.yearly_repeat:
                    icon = "🔄"
                
                button_text = f"{icon} {note.title[:30]} - {note.solar_date.strftime('%d/%m/%Y')}"
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"view_note_{note.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                message_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            
        finally:
            db.close()
    
    async def upcoming_notes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Đápủng danh sách ghi chú sắp tới (7 ngày tới)"""
        query = update.callback_query
        if query:
            await query.answer()
            message = query.message
        else:
            message = update.message
        
        db = SessionLocal()
        try:
            user = self.get_user_by_telegram_id(db, update.effective_user.id)
            if not user:
                await message.reply_text(
                    "❌ Bạn chưa liên kết tài khoản!",
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            today = date.today()
            next_week = today + timedelta(days=7)
            
            notes = (
                db.query(Note)
                .filter(
                    Note.user_id == user.id,
                    Note.is_active == True,
                    Note.solar_date >= today,
                    Note.solar_date <= next_week,
                )
                .order_by(Note.solar_date)
                .all()
            )
            
            if not notes:
                await message.reply_text(
                    "⌚ <b>Không có ghi chú sắp tới</b>\n\n"
                    "Bạn không có ghi chú nào trong 7 ngày tới.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            message_text = f"⌚ <b>Ghi chú sắp tới</b> (7 ngày tới)\n\n"
            
            keyboard = []
            for note in notes:
                days_left = (note.solar_date - today).days
                
                if days_left == 0:
                    time_text = "Hôm nay"
                elif days_left == 1:
                    time_text = "Ngày mai"
                else:
                    time_text = f"Còn {days_left} ngày"
                
                icon = "🔔" if note.enable_notification else "📝"
                button_text = f"{icon} {note.title[:25]} - {time_text}"
                
                keyboard.append([
                    InlineKeyboardButton(
                        button_text,
                        callback_data=f"view_note_{note.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ Quay lại", callback_data="back_to_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                message_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            
        finally:
            db.close()
    
    async def view_note_detail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xem chi tiết một ghi chú"""
        query = update.callback_query
        await query.answer()
        
        note_id = int(query.data.split("_")[2])
        
        db = SessionLocal()
        try:
            note = db.query(Note).filter(Note.id == note_id, Note.is_active == True).first()
            if not note:
                await query.message.reply_text(
                    "❌ Không tìm thấy ghi chú!",
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            lunar_info = LunarCalendarService.get_lunar_info(note.solar_date)
            
            repeat_info = ""
            if note.monthly_repeat:
                repeat_info = "\n📅 Lặp hàng tháng"
            elif note.yearly_repeat:
                repeat_info = "\n🔄 Lặp hàng năm"
            
            notif_info = ""
            if note.enable_notification:
                notif_info = f"\n🔔 Nhắc trước {note.notification_days_before} ngày{repeat_info}"
            
            days_until = (note.solar_date - date.today()).days
            if days_until >= 0:
                if days_until == 0:
                    time_text = "\n⌚ <b>Hôm nay!</b>"
                elif days_until == 1:
                    time_text = "\n⌚ Còn 1 ngày nữa"
                else:
                    time_text = f"\n⌚ Còn {days_until} ngày nữa"
            else:
                time_text = f"\n📅 Đã qua {abs(days_until)} ngày"
            
            detail_message = (
                f"📝 <b>Chi tiết ghi chú</b>\n\n"
                f"📌 <b>Tiêu đề:</b> {note.title}\n"
                f"📝 <b>Nội dung:</b> {note.content or '<i>Không có</i>'}\n"
                f"📅 <b>Ngày dương:</b> {note.solar_date.strftime('%d/%m/%Y')}\n"
                f"🌙 <b>Ngày âm:</b> {lunar_info['lunar_date_str']}"
                f"{time_text}"
                f"{notif_info}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Sửa", callback_data=f"edit_note_{note.id}"),
                    InlineKeyboardButton("🗑️ Xóa", callback_data=f"delete_note_{note.id}"),
                ],
                [
                    InlineKeyboardButton("⬅️ Quay lại", callback_data="list_notes"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                detail_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            
        finally:
            db.close()
    
    # ==================== DELETE NOTE ====================
    
    async def confirm_delete_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xác nhận xóa ghi chú"""
        query = update.callback_query
        await query.answer()
        
        note_id = int(query.data.split("_")[2])
        context.user_data["deleting_note_id"] = note_id
        
        db = SessionLocal()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                await query.message.reply_text(
                    "❌ Không tìm thấy ghi chú!",
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Xác nhận xóa", callback_data=f"confirm_delete_{note_id}"),
                ],
                [
                    InlineKeyboardButton("❌ Hủy", callback_data=f"view_note_{note_id}"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                f"⚠️ <b>Xác nhận xóa ghi chú?</b>\n\n"
                f"📝 <b>{note.title}</b>\n"
                f"📅 {note.solar_date.strftime('%d/%m/%Y')}\n\n"
                "<i>Hành động này không thể hoàn tác!</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            
        finally:
            db.close()
    
    async def execute_delete_note(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Thực hiện xóa ghi chú"""
        query = update.callback_query
        await query.answer()
        
        note_id = int(query.data.split("_")[2])
        
        db = SessionLocal()
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                await query.message.reply_text(
                    "❌ Không tìm thấy ghi chú!",
                    reply_markup=self.get_main_menu_keyboard(),
                )
                return
            
            note_title = note.title
            
            # Soft delete
            note.is_active = False
            db.commit()
            
            # Delete notification schedule
            from app.models.notification_schedule import NotificationSchedule

            db.query(NotificationSchedule).filter(
                NotificationSchedule.note_id == note.id
            ).delete()
            db.commit()
            
            await query.message.reply_text(
                f"✅ <b>Đã xóa ghi chú thành công!</b>\n\n"
                f"📝 {note_title}",
                parse_mode=ParseMode.HTML,
                reply_markup=self.get_main_menu_keyboard(),
            )
            
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            await query.message.reply_text(
                f"❌ Lỗi khi xóa ghi chú: {str(e)}",
                reply_markup=self.get_main_menu_keyboard(),
            )
        finally:
            db.close()
    
    # ==================== COMMON HANDLERS ====================
    
    async def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quay lại menu chính"""
        query = update.callback_query
        await query.answer()
        
        await query.message.reply_text(
            "🏠 <b>Menu chính</b>\n\nChọn chức năng:",
            parse_mode=ParseMode.HTML,
            reply_markup=self.get_main_menu_keyboard(),
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy thao tác hiện tại"""
        context.user_data.clear()
        
        await update.message.reply_text(
            "❌ <b>Đã hủy</b>\n\nQuay lại menu chính:",
            parse_mode=ParseMode.HTML,
            reply_markup=self.get_main_menu_keyboard(),
        )
        
        return ConversationHandler.END
    
    # ==================== SETUP BOT ====================
    
    def setup_handlers(self, application: Application):
        """Setup tất cả handlers cho bot"""
        
        # Add note conversation handler
        add_note_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add_note, pattern="^add_note$"),
                CommandHandler("add", self.start_add_note),
            ],
            states={
                ASKING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_title)],
                ASKING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_content)],
                ASKING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_date)],
                ASKING_NOTIFICATION: [
                    CallbackQueryHandler(self.receive_notification_choice, pattern="^notif_")
                ],
                ASKING_REPEAT_TYPE: [
                    CallbackQueryHandler(self.receive_repeat_type, pattern="^repeat_")
                ],
                ASKING_DAYS_BEFORE: [
                    CallbackQueryHandler(self.receive_days_before, pattern="^days_")
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
            per_chat=True,
            per_user=True,
            per_message=False,  # Fix warning
        )
        
        application.add_handler(add_note_handler)
        
        # Commands
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("list", self.list_notes))
        application.add_handler(CommandHandler("upcoming", self.upcoming_notes))
        application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Callback handlers
        application.add_handler(CallbackQueryHandler(self.list_notes, pattern="^list_notes$"))
        application.add_handler(CallbackQueryHandler(self.upcoming_notes, pattern="^upcoming_notes$"))
        application.add_handler(CallbackQueryHandler(self.view_note_detail, pattern="^view_note_"))
        application.add_handler(CallbackQueryHandler(self.confirm_delete_note, pattern="^delete_note_"))
        application.add_handler(CallbackQueryHandler(self.execute_delete_note, pattern="^confirm_delete_"))
        application.add_handler(CallbackQueryHandler(self.back_to_menu, pattern="^back_to_menu$"))
        application.add_handler(CallbackQueryHandler(self.main_menu_callback))
        
        logger.info("✅ Bot handlers ready")
    
    async def set_bot_commands(self):
        """Thiết lập menu commands cho bot"""
        from telegram import BotCommand
        
        commands = [
            BotCommand("start", "🚀 Khởi động bot và xem menu"),
            BotCommand("add", "➕ Thêm ghi chú mới"),
            BotCommand("list", "📋 Xem danh sách ghi chú"),
            BotCommand("upcoming", "⏰ Xem ghi chú sắp tới"),
            BotCommand("help", "❓ Hướng dẫn sử dụng"),
            BotCommand("cancel", "❌ Hủy thao tác hiện tại"),
        ]
        
        await self.application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands menu ready")
    
    async def post_init(self, application: Application):
        """Callback sau khi application khởi tạo"""
        await self.set_bot_commands()
    
    def run_polling(self):
        """Chạy bot với polling mode"""
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return
        
        # Tạo application
        builder = Application.builder().token(self.bot_token)
        
        # Thử dùng proxy nếu có
        if self.api_url and "tele-api" in self.api_url:
            builder.base_url(f"{self.api_url}/bot")
        
        # Timeout
        builder.connect_timeout(30.0)
        builder.read_timeout(30.0)
        
        # Post init callback để setup commands
        builder.post_init(self.post_init)
        
        self.application = builder.build()
        
        # Setup handlers
        self.setup_handlers(self.application)
        
        # Start polling
        logger.info("✅ Bot starting...")
        self.application.run_polling()


def main():
    """Main entry point cho bot"""
    handler = TelegramBotHandler()
    handler.run_polling()
