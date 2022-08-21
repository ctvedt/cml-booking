import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events
from django_apscheduler.models import DjangoJobExecution
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings

# Create scheduler to run in a thread inside the application process
scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG)

def delete_old_job_executions(max_age=604_800):
  """
  This job deletes APScheduler job execution entries older than `max_age` from the database.
  It helps to prevent the database from filling up with old historical records that are no
  longer useful.
  
  :param max_age: The maximum length of time to retain historical job execution records.
                  Defaults to 7 days.
  """
  DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start():
    # If DEBUG, hook into the apscheduler logger
    if settings.DEBUG:
        logging.basicConfig()
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    # Delete old scheduled jobs
    scheduler.add_job(
        delete_old_job_executions, 
        trigger=CronTrigger(day_of_week="mon", hour="00", minute="10"), 
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True
    )

    # Add the scheduled jobs to the Django admin interface
    register_events(scheduler)

    # Run the scheduler
    scheduler.start()