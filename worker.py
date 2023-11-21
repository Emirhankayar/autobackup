from celery import Celery
from main import perform_backup
import os

# Create a Celery instance
celery_app = Celery('tasks', broker=os.getenv('CLOUDAMQP_URL'))

# Define a Celery task that calls the backup function
@celery_app.task
def backup_task():
    perform_backup()