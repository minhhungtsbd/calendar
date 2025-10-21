"""
Migration script: Thêm monthly_repeat vào bảng notes và current_month vào notification_schedules
"""
from sqlalchemy import create_engine, Column, Boolean, Integer, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Thêm monthly_repeat column vào notes table và current_month vào notification_schedules"""
    engine = create_engine(settings.database_url)
    
    with engine.connect() as connection:
        try:
            # Thêm monthly_repeat vào bảng notes
            logger.info("Adding monthly_repeat column to notes table...")
            connection.execute(text("""
                ALTER TABLE notes 
                ADD COLUMN monthly_repeat BOOLEAN DEFAULT FALSE AFTER yearly_repeat
            """))
            logger.info("✅ Added monthly_repeat column to notes")
            
            # Thêm current_month vào bảng notification_schedules
            logger.info("Adding current_month column to notification_schedules table...")
            connection.execute(text("""
                ALTER TABLE notification_schedules 
                ADD COLUMN current_month INTEGER NOT NULL DEFAULT 1 AFTER current_year
            """))
            logger.info("✅ Added current_month column to notification_schedules")
            
            # Cập nhật current_month cho các schedule hiện tại
            logger.info("Updating current_month for existing schedules...")
            connection.execute(text("""
                UPDATE notification_schedules ns
                JOIN notes n ON ns.note_id = n.id
                SET ns.current_month = MONTH(n.solar_date)
            """))
            logger.info("✅ Updated current_month for existing schedules")
            
            connection.commit()
            logger.info("🎉 Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            connection.rollback()
            raise


if __name__ == "__main__":
    migrate()
