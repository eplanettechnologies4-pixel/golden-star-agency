import os
from celery import Celery
from decouple import config

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('golden_star_agency')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Retrieve REDIS_URL from environmental variables
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
app.conf.broker_url = REDIS_URL
app.conf.result_backend = REDIS_URL

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'expire-stale-holds': {
        'task': 'apps.airline_ticketing.tasks.expire_stale_holds',
        'schedule': 300.0,  # every 5 minutes (300 seconds)
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
