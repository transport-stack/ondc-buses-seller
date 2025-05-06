import os
import sys
import json
import django
import argparse
from celery import current_app

# Setting up Django's settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.base')
django.setup()


def read_json_from_file(file_path):
    """Read and return data from a JSON file."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def run_celery_task(task_name, json_file_path):
    # Fetch the Celery task based on the provided task name
    task = current_app.tasks.get(task_name)
    if not task:
        raise ValueError(f"No task found with name {task_name}")

    # Read data from the JSON file
    task_data = read_json_from_file(json_file_path)

    # Run the Celery task
    result = task.delay(task_data)
    print(f"Task submitted, task id: {result.id}")

    # Optionally, wait for the result
    try:
        result_value = result.get(timeout=10)  # get() is blocking and waits for the
        # result
        print(f"Task completed with result: {result_value}")
    except Exception as e:
        print(f"Error waiting for task result: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a Celery task with JSON input.')
    parser.add_argument('task_name', type=str, help='Name of the Celery task to run')
    parser.add_argument('json_file_path', type=str,
                        help='Path to the JSON file with request data')

    args = parser.parse_args()

    run_celery_task(args.task_name, args.json_file_path)
