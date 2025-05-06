#!/bin/bash

if [ "$1" = "api-service" ]; then
  exec gunicorn -b 0.0.0.0:8000 core.wsgi:application --error-logfile - --access-logfile - ${@:2}
elif [ "$1" = "celery-worker" ]; then
  exec celery -A core worker --autoscale 2,2 --loglevel=info ${@:2}
elif [ "$1" = "celery-beat" ]; then
  exec celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler ${@:2}
else
    echo "Invalid command, please use one of: api-service, celery-worker, celery-beat"
    exit 1
fi

