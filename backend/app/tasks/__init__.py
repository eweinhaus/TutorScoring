"""
Celery tasks package.
"""
from app.tasks.celery_app import celery_app

# Import tasks to register them with Celery
from app.tasks import session_processor, email_tasks

__all__ = ['celery_app']
