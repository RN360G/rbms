from celery import shared_task

@shared_task
def my_function():
    print("Running task...")
