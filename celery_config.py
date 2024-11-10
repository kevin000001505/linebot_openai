from celery import Celery
import os

def make_celery(app):
    celery = Celery(
        "stock_response",
        broker=os.environ.get('REDIS_URL'),
        backend=os.environ.get('REDIS_URL')
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery