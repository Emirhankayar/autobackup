from celery import Celery
from main import perform_backup
import os
from celery.schedules import crontab

# Create a Celery instance
celery_app = Celery('tasks', broker=os.getenv('CLOUDAMQP_URL'))

celery_app.conf.beat_schedule = {
    'run-every-5-minutes': {
        'task': 'worker.backup_task',
        'schedule': crontab(minute='*/5'),
    },
}

# Define a Celery task that calls the backup function
@celery_app.task
def backup_task():
    perform_backup()