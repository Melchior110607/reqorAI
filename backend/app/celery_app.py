"""
Configuration Celery pour les tâches asynchrones
"""
from celery import Celery
from celery.schedules import crontab
from app.database.config import settings

# Créer l'instance Celery
celery_app = Celery(
    "projectai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.tasks.webhook_renewal']  # Seulement webhook renewal, plus de polling
)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max par tâche
)

# Configuration Celery Beat (tâches périodiques)
celery_app.conf.beat_schedule = {
    # ✅ Webhook renewal tasks (critical for webhook reliability)
    'renew-gmail-watches-daily': {
        'task': 'app.tasks.webhook_renewal.renew_gmail_watches',
        'schedule': crontab(minute=0, hour=2),  # Every day at 2:00 AM UTC
        'options': {'queue': 'email_sync'}
    },
    
    'renew-outlook-subscriptions-daily': {
        'task': 'app.tasks.webhook_renewal.renew_outlook_subscriptions',
        'schedule': crontab(minute=0, hour=3),  # Every day at 3:00 AM UTC
        'options': {'queue': 'email_sync'}
    },
}

# Configuration des queues
celery_app.conf.task_routes = {
    'app.tasks.webhook_renewal.*': {'queue': 'email_sync'},
}

