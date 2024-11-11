# celery_config.py
from celery import Celery
import os

def make_celery(broker_url, backend_url):
    celery = Celery(
        'celery_worker',          # Name of the Celery app
        broker=broker_url,
        backend=backend_url
    )
    celery.conf.update({
        'broker_url': broker_url,
        'result_backend': backend_url,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
    })
    return celery