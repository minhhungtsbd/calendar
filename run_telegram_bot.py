#!/usr/bin/env python
"""
Script để chạy Telegram Bot
Chạy: python run_telegram_bot.py
"""
import logging
from app.services.telegram_bot_handler import TelegramBotHandler
from app.config import settings

# Setup logging - Giảm log cho gọn
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tắt httpx debug logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)


def main():
    """Main function"""
    logger.info("🚀 Starting Telegram Bot...")
    
    if not settings.telegram_bot_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN not configured in .env file!")
        logger.error("Please add TELEGRAM_BOT_TOKEN=your_token_here to .env")
        return
    
    # Create and run bot
    bot_handler = TelegramBotHandler()
    bot_handler.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
