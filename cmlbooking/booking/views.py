from django.shortcuts import render, redirect
from django.contrib import messages
from booking.models import Booking
from datetime import date, datetime, timedelta

def GetValidTimeslots(date):
    # Possible timeslots each day
    timeslots = [0,3,6,9,12,15,18,21]
    validtimeslots = {}

    # Loop through all timeslots
    for slot in timeslots:
        # Exclude past dates
        if(date.date() < datetime.today().date()):
            validtimeslots[slot] = 'invalid'

        # Exclude todays timeslots that has passed
        elif(date.date() == datetime.today().date()):
            if(datetime.now().hour < slot):
                validtimeslots[slot] = 'valid'
            else:
                validtimeslots[slot] = 'invalid'

        # All slots possible if date is in the future
        else:
            validtimeslots[slot] = 'valid'

    # Return all possible timeslots for date
    return validtimeslots


def GetBookedSlots(date):
    booked = []
    bookings = Booking.objects.filter(timeslot__date=date)
    
    for booking in bookings:
        booked.append(booking.timeslot.astimezone().hour)

    return booked


def GetSlotStatus(date):
    # Get all possible slots for this date
    allslots = GetValidTimeslots(date)
    bookedslots = GetBookedSlots(date)

    slotstatus = {}

    for slot,validity in allslots.items():
        if validity == 'invalid':
            slotstatus[slot] = 'invalid'
        else:
            if bookedslots.count(slot):
                slotstatus[slot] = 'booked'
            else:
                slotstatus[slot] = 'free'

    return slotstatus


def RenderCalendar(request):
    data = {}
    numberofdays = 5

    # Get data for the next X days
    for i in range(numberofdays):
        daydate = datetime.today() + timedelta(days=i)
        data[i] = {
            'dayid': i,
            'dayname': daydate.strftime("%A"),
            'daydate': daydate.strftime("%d.%m"),
            'daydatestr': daydate.strftime("%Y-%d-%m"),
            'bookingdata': GetSlotStatus(datetime.today() + timedelta(days=i)),
        }

    context = {
        'calendardata': data,
    }

    return render(request, 'booking/index.html', context)
