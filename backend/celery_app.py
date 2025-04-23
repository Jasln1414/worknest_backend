# D:\Django_second_project\WorkNest\backend\celery_app.py
from __future__ import absolute_import, unicode_literals
import os
import logging
from celery import Celery 

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Create Celery app instance
app = Celery('worknest')

# Configure timezone
app.conf.enable_utc = False
app.conf.timezone = 'America/New_York'

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Initialize logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Celery worker initialized')
logger.info(f'Using broker: {app.conf.broker_url}')