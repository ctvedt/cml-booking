from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.formats import date_format
from django.conf import settings
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

            # Get email from form
            email = form.cleaned_data['email']
            
            # Get domain from email
            domain = email.split('@')[-1]
            
            # Invalid domain or email
            if domain != settings.BOOKING_ALLOWED_DOMAIN:
                messages.add_message(request, messages.WARNING, f'E-postadressen du benyttet er ugyldig. Det er kun mulig å reservere med @{settings.BOOKING_ALLOWED_DOMAIN} e-postadresser.')
                return redirect(f'/booking/{day}/{slot}/')
            
            # Check if user has active booking
            elif(Booking.objects.filter(email=email,timeslot__gte=datetime.now().astimezone()-timedelta(hours=3))):
                messages.add_message(request, messages.ERROR, 'Det finnes allerede en reservasjon for e-postadresse din! For å gi alle mulighet til å bruke miljøet, er det kun mulig å ha én aktiv reservasjon per bruker.')
                return redirect(f'/booking/{day}/{slot}/')
            
            else:
                # Convert to datetime
                todaysdate = datetime.combine(date.today(), datetime.min.time())
                bookingtime = todaysdate + timedelta(days=day, hours=slot)

                # Save data and print success-message
                booking = Booking(timeslot=bookingtime.astimezone(), email=email)
                booking.save()
                messages.add_message(request, messages.SUCCESS, f'Din reservasjon for {bookingtime.date()} fra {"{:02}".format(bookingtime.hour)}:00-{"{:02}".format(bookingtime.hour+3)}:00 er bekreftet! Du vil straks motta en e-post med informasjon, i tillegg til en ny e-post med brukernavn og passord når din tidsperiode starter.')
                
                # Send info email using template
                context = {
                    'booking_date': bookingtime.date(),
                    'timeslot_from': '{:02}'.format(bookingtime.hour),
                    'timeslot_to': '{:02}'.format(bookingtime.hour+3),
                    'cancelcode': booking.cancelcode,
                    'cml_url': settings.CML_URL,
                    'booking_url': settings.BOOKING_URL,
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
            if(Booking.objects.filter(timeslot=bookingtime.astimezone())):
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


def CancelBooking(request, cancelcode=None):
    if cancelcode:
        # Find booking with cancellation code
        booking = Booking.objects.filter(cancelcode=cancelcode).first()
        if booking:
            # Booking found, now delete it
            booking.delete()
            messages.add_message(request, messages.SUCCESS, f'Din reservasjon ble kansellert! Takk for at du kansellerte og gav andre muligheten til å reservere!')
        else:
            # Not found, print warning
            messages.add_message(request, messages.WARNING, f'Det ser ikke ut til at det finnes en reservasjoner i databasen med den kanselleringskoden. Ingen reservasjoner ble derfor slettet.')
        
    # Redirect to home
    return redirect('/')

def RenderCalendar(request):
    data = {}
    numberofdays = 5

    # Get data for the next X days
    for i in range(numberofdays):
        daydate = datetime.today().astimezone() + timedelta(days=i)
        data[i] = {
            'dayid': i,
            'dayname': date_format(daydate, 'l'),
            'daydate': daydate.strftime("%d.%m"),
            'daydatestr': daydate.strftime("%Y-%d-%m"),
            'bookingdata': GetSlotStatus(datetime.today().astimezone() + timedelta(days=i)),
        }

    context = {
        'calendardata': data,
    }

    return render(request, 'booking/index.html', context)
