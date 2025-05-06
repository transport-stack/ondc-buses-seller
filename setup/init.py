import django

django.setup()


def set_up_database(testing=False):
    from setup.add_celerytasks import add_celery_tasks

    if not testing:
        add_celery_tasks()


if __name__ == "__main__":
    set_up_database()
