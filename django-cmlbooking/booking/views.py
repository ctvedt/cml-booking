import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.formats import date_format
from booking.models import Booking
from .forms import BookingForm
from datetime import date, datetime, timedelta
from . import cml

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


def CreateNewBooking(request,day=None,slot=None):
    # Valid timeslots
    timeslots = [0,3,6,9,12,15,18,21]
       
    if request.method == 'POST':
        form = BookingForm(request.POST)

        # Check whether it's valid:
        if form.is_valid():

            # Get email and domain from POST
            email = request.POST.get('email', False)
            domain = email.split('@')[1]
            
            # Validate email domain
            if domain != 'soprasteria.com':
                messages.add_message(request, messages.WARNING, 'E-postadressen du benyttet er ugyldig. Det er kun mulig å reservere med @soprasteria.com e-postadresser.')
                return redirect(f'/booking/{day}/{slot}/')
            
            # Check if user has active booking
            elif(Booking.objects.filter(email=email,timeslot__gte=datetime.now().astimezone()-timedelta(hours=3))):
                messages.add_message(request, messages.ERROR, 'Det finnes allerede en reservasjon for e-postadresse din! For å gi alle mulighet til å bruke miljøet, er det kun mulig å ha én aktiv reservasjon per bruker.')
                return redirect(f'/booking/{day}/{slot}/')
            
            else:
                # Convert to datetime
                todaysdate = datetime.combine(date.today(), datetime.min.time())
                bookingtime = todaysdate + timedelta(days=day, hours=slot)
                
                # Create temporary password for this booking
                temp_password = uuid.uuid4().hex

                # Save data and print success-message
                Booking(timeslot=bookingtime.astimezone(), email=email, password=temp_password).save()
                messages.add_message(request, messages.SUCCESS, f'Din reservasjon for {bookingtime.date()} fra {"{:02}".format(bookingtime.hour)}-{"{:02}".format(bookingtime.hour+3)} er bekreftet! Du vil straks motta en e-post med informasjon, i tillegg til en ny e-post med brukernavn og passord når din tidsperiode starter.')
                
                # Send info email using template
                context = {
                    'booking_date': bookingtime.date(),
                    'timeslot_from': '{:02}'.format(bookingtime.hour),
                    'timeslot_to': '{:02}'.format(bookingtime.hour+3),
                }
                body = render_to_string('booking/email_info.html', context)
                cml.SendEmail(email, 'Community Network - CML reservasjon', body)

                # Return to home
                return redirect('/')
                
    else:
        # If values are set
        if(day >= 0 and day < 5 and (slot in timeslots)):
            
            # Check if timeslot is valid, else redirect to home
            if slot not in timeslots:
                return redirect('/')
            
            # Convert to datetime
            todaysdate = datetime.combine(date.today(), datetime.min.time())
            bookingtime = todaysdate + timedelta(days=day, hours=slot)
    
            # Check if booking exist for requested date
            if(Booking.objects.filter(timeslot=bookingtime)):
                messages.add_message(request, messages.ERROR, 'Det finnes allerede en reservasjon for denne datoen og tidsrommet.')
                return redirect('/')
    
            # Render form
            form = BookingForm()
            context = {
                'day': day,
                'slot': slot,
                'bookingtime': bookingtime,
                'form': form,
            }
            return render(request, 'booking/booking.html', context)

        else:
            # Redirect to home
            messages.add_message(request, messages.ERROR, 'Ugyldige verdier oppgitt.')
            return redirect('/')


def RenderCalendar(request):
    data = {}
    numberofdays = 5

    # Get data for the next X days
    for i in range(numberofdays):
        daydate = datetime.today() + timedelta(days=i)
        data[i] = {
            'dayid': i,
            'dayname': date_format(daydate, 'l'),
            'daydate': daydate.strftime("%d.%m"),
            'daydatestr': daydate.strftime("%Y-%d-%m"),
            'bookingdata': GetSlotStatus(datetime.today() + timedelta(days=i)),
        }

    context = {
        'calendardata': data,
    }

    return render(request, 'booking/index.html', context)
