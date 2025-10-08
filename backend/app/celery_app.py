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
    include=['app.tasks.email_sync']
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
    'sync-all-emails-every-minute': {
        'task': 'app.tasks.email_sync.sync_all_user_emails',
        # ⚠️ MODE DEBUG: Sync chaque minute (pour tests)
        # 🔧 PRODUCTION: Changer en crontab(minute='*/30') pour sync toutes les 30min
        'schedule': crontab(minute='*/30'),  # DEBUG: Toutes les minutes
        'options': {'queue': 'email_sync'}
    },
}

# Configuration des queues
celery_app.conf.task_routes = {
    'app.tasks.email_sync.*': {'queue': 'email_sync'},
}

