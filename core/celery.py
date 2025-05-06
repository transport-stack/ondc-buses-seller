from __future__ import absolute_import, unicode_literals

import os
from kombu import Exchange, Queue
from celery import Celery
from celery.signals import worker_process_init
from django.db import connections
import main.tasks.tasks  #This import should not be removed as it registers the tasks in the main.tasks.tasks file

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')

app = Celery('core')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['main'])


# Signal handler to close database connections when a worker process is initialized
@worker_process_init.connect
def close_db_connections(**kwargs):
    for conn in connections.all():
        conn.close()


# Example Celery configuration
app.conf.update(
    worker_max_tasks_per_child=100,  # Restart workers after processing a number of tasks
    worker_prefetch_multiplier=1,  # Number of tasks a worker prefetches
    task_acks_late=True,  # Acknowledge tasks only after they are completed
    broker_pool_limit=None,  # Unlimited connections to the broker
    result_backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:6379/0",  # Redis as result backend
    task_queues=[
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('search1_queue', Exchange('search1_exchange'), routing_key='search1_queue'),
        Queue('search2_queue', Exchange('search2_exchange'), routing_key='search2_queue'),
        Queue('select_queue', Exchange('select_exchange'), routing_key='select_queue'),
        Queue('pass_select_queue', Exchange('pass_select_exchange'), routing_key='pass_select_queue'),
        Queue('pass_init_queue', Exchange('pass_init_exchange'), routing_key='pass_init_queue'),
        Queue('pass_confirm_queue', Exchange('pass_confirm_exchange'), routing_key='pass_confirm_queue'),
        Queue('init_queue', Exchange('init_exchange'), routing_key='init_queue'),
        Queue('confirm_queue', Exchange('confirm_exchange'), routing_key='confirm_queue'),
        Queue('update_queue', Exchange('update_exchange'), routing_key='update_queue'),
        Queue('receiver_recon_queue', Exchange('receiver_recon_exchange'), routing_key='receiver_recon_queue'),
        Queue('expire_confirmed_tickets_queue',
              Exchange('expire_confirmed_tickets_exchange'),
              routing_key='expire_confirmed_tickets_queue'),
        Queue('expire_passes_after_validity_queue',
              Exchange('expire_passes_after_validity_exchange'),
              routing_key='expire_passes_after_validity_queue'),
        Queue('task_push_txn_logs_queue', Exchange('task_push_txn_logs_exchange'), routing_key='task_push_txn_logs_queue'),
    ],
    task_routes={
        'main.tasks.on_search_all_route_stops': {'queue': 'search1_queue'},
        'main.tasks.on_search': {'queue': 'search2_queue'},
        'main.tasks.on_select': {'queue': 'select_queue'},
        'main.tasks.pass_on_select': {'queue': 'pass_select_queue'},
        'main.tasks.pass_on_init': {'queue': 'pass_init_queue'},
        'main.tasks.pass_on_confirm': {'queue': 'pass_confirm_queue'},
        'main.tasks.on_init': {'queue': 'init_queue'},
        'main.tasks.on_confirm': {'queue': 'confirm_queue'},
        'main.tasks.on_update': {'queue': 'update_queue'},
        'main.tasks.on_receiver_recon': {'queue': 'receiver_recon_queue'},
        'main.tasks.tasks.expire_previous_day_confirmed_tickets': {'queue': 'expire_confirmed_tickets_queue'},
        'main.tasks.tasks.expire_passes_after_validity': {'queue': 'expire_passes_after_validity_queue'},
        'main.tasks.task_push_txn_logs': {'queue': 'task_push_txn_logs_queue'},
    },
)

if __name__ == '__main__':
    app.start()
