from celery import Celery
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import engine
from app.services.notification_service import NotificationService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'calendar_tasks',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    # Connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Task timeout settings
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    # Beat schedule
    beat_schedule={
        'send-notifications': {
            'task': 'app.tasks.notification_tasks.send_notifications_task',
            'schedule': 60.0,  # Run every minute
        },
        'cleanup-old-schedules': {
            'task': 'app.tasks.notification_tasks.cleanup_old_schedules_task',
            'schedule': 24 * 60 * 60.0,  # Run daily
        },
    },
)

# Create database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True)
def send_notifications_task(self):
    """Celery task to process notification schedules"""
    db = None
    try:
        # Create database session with proper error handling
        db = SessionLocal()
        notification_service = NotificationService()
        
        # Process ready schedules (new system)
        result = notification_service.process_all_ready_schedules(db)
        
        # Log concise result
        if result["processed"] > 0 or result["failed"] > 0:
            logger.info(f"📊 Processed {result['processed']}/{result['total']} schedules")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in send_notifications_task: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        # Always close database session
        if db:
            try:
                db.close()
            except Exception as e:
                logger.error(f"❌ Error closing database session: {e}")


@celery_app.task(bind=True)
def cleanup_old_schedules_task(self):
    """Celery task to cleanup old completed notification schedules"""
    db = None
    try:
        # Create database session
        db = SessionLocal()
        notification_service = NotificationService()
        
        # Cleanup schedules older than 30 days
        cleaned_count = notification_service.cleanup_old_completed_schedules(db, days_old=30)
        
        result = {
            "status": "success",
            "cleaned_count": cleaned_count,
            "message": f"Cleaned up {cleaned_count} old notification schedules"
        }
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleanup: {cleaned_count} old schedules removed")
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_schedules_task: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        # Always close database session
        if db:
            try:
                db.close()
                logger.debug("Database session closed successfully")
            except Exception as e:
                logger.error(f"Error closing database session: {e}")


if __name__ == '__main__':
    celery_app.start()
