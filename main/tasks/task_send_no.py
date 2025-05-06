import os
import requests
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

ONDC_ANALYTICS_URL = os.getenv("ONDC_ANALYTICS_URL")
AUTH_TOKEN = os.getenv("ONDC_ANALYTICS_AUTH_TOKEN")


@shared_task(name="main.tasks.task_push_txn_logs")
def task_push_txn_logs(log_type, log_data):
    # pass

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }

    payload = {
        "type": log_type,
        "data": log_data
    }

    try:
        logger.info(f"Sending {log_type} txn logs to ONDC N.O: {payload}")
        response = requests.post(ONDC_ANALYTICS_URL, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Successfully sent {log_type} txn logs to N.O with response: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error pushing txn logs: {str(e)}")
