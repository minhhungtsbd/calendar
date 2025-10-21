import asyncio
from telegram import Bot
from telegram.error import TelegramError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending Telegram notifications"""
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.api_url = settings.telegram_api_url
        self.bot = None

        if self.bot_token:
            # Use custom API URL instead of default api.telegram.org
            self.bot = Bot(token=self.bot_token, base_url=f"{self.api_url}/bot")
    
    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """Send a message via Telegram bot"""
        if not self.bot:
            logger.error("Telegram bot token not configured")
            return False
        
        # Use provided chat_id or default one
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.error("No chat ID provided or configured")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='HTML'
            )
            # Removed verbose log - handled by notification_service
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False
    
    def send_message_sync(self, message: str, chat_id: str = None) -> bool:
        """Synchronous wrapper for sending Telegram messages"""
        try:
            # Try to run in a new event loop to avoid "event loop already running" error
            return asyncio.run(self.send_message(message, chat_id))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # If we're in an async context, create a new thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self.send_message(message, chat_id))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)  # 30 second timeout
            else:
                logger.error(f"Error in send_message_sync: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error in send_message_sync: {e}")
            return False
    
    async def send_note_reminder(self, note_title: str, note_content: str, 
                                solar_date: str, lunar_date: str, days_before: int) -> bool:
        """Send a formatted note reminder"""
        message = f"""
🗓️ <b>Nhắc nhở ghi chú</b>

📝 <b>Tiêu đề:</b> {note_title}
📄 <b>Nội dung:</b> {note_content}

📅 <b>Ngày dương:</b> {solar_date}
🌙 <b>Ngày âm:</b> {lunar_date}

⏰ <b>Còn {days_before} ngày nữa</b>
        """.strip()
        
        return await self.send_message(message)
    
    def send_note_reminder_sync(self, note_title: str, note_content: str, 
                               solar_date: str, lunar_date: str, days_before: int) -> bool:
        """Synchronous wrapper for sending note reminders"""
        try:
            return asyncio.run(
                self.send_note_reminder(note_title, note_content, solar_date, lunar_date, days_before)
            )
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # If we're in an async context, create a new thread
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self.send_note_reminder(note_title, note_content, solar_date, lunar_date, days_before)
                        )
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)
            else:
                logger.error(f"Error in send_note_reminder_sync: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error in send_note_reminder_sync: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test Telegram bot connection"""
        if not self.bot:
            return False
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot connected: {bot_info.username}")
            return True
        except Exception as e:
            logger.error(f"Telegram bot connection test failed: {e}")
            return False
