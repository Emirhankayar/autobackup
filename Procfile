web: gunicorn -w 4 main:app
celery -A worker.celery_app worker --loglevel=info
beat: celery -A worker.celery_app beat --loglevel=info