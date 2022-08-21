import logging

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events
from django_apscheduler.models import DjangoJobExecution
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from datetime import datetime, date, timedelta
from django.utils import timezone
from booking.models import Booking
from datetime import datetime
from . import cml

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


def GetDateTimeNow(offset=0):
    # To find labs booked X hours ago for cleanup, we need to offset the time
    if offset:
        delta = timedelta(hours=(datetime.now().hour-offset))
    else:
        delta = timedelta(hours=datetime.now().hour)

    # Get datetime for slot
    datenow = datetime.combine(date.today(), datetime.min.time())
    slotnow = datenow.astimezone() + delta

    return slotnow


def SetUpLab():
    # See if there is a booked slot
    bookednow = Booking.objects.filter(timeslot=GetDateTimeNow())
    
    if(bookednow):
        # Booking exists, get first (and only...)
        booking = bookednow.first()

        # Create temporary password and send to user
        cml.CreateTempUser(booking.email, booking.password)
    else:
        print('SetUpLab: not a booked slot, no setup to be done')


def TearDownLab():
    # See if there is a booked slot
    # Offset is almost 3 hours, but since we run the scheduled task
    # right before the time is up, we need to look for booked slots
    # with 2 hour offset
    bookednow = Booking.objects.filter(timeslot=GetDateTimeNow(2))
    
    if(bookednow):
        # Booking exists, get first (and only...)
        booking = bookednow.first()

        # Clean up after booked session
        cml.CleanUp(booking.email, booking.password)
    else:
        print('TearDownLab: no booked slot, no cleanup to be done')


def start():
    # If DEBUG, hook into the apscheduler logger
    if settings.DEBUG:
        logging.basicConfig()
        logging.getLogger('apscheduler').setLevel(logging.DEBUG)

    # Tear down running labs two minutes before time is up
    scheduler.add_job(
        TearDownLab, 
        trigger=CronTrigger(minute="59"), 
        id="CML_TearDownLab", 
        max_instances=1,
        replace_existing=True
    )

    # Set up lab at the hour
    scheduler.add_job(
        SetUpLab, 
        trigger=CronTrigger(minute="00"),
        id="CML_SetUpLab", 
        max_instances=1,
        replace_existing=True
    )

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