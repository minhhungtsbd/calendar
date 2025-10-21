#!/usr/bin/env python3
"""
Celery application entry point
"""

from app.tasks.notification_tasks import celery_app

if __name__ == '__main__':
    celery_app.start()
