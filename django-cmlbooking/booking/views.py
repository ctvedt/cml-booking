from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.formats import date_format
from django.conf import settings
from booking.models import Booking, VerifiedEmail, Maintenance
from .forms import BookingForm
from datetime import date, datetime, timedelta, time
from django.utils import timezone
from . import cml
import logging
logger = logging.getLogger(__name__)

def BlockedByMaintenance(date):
    # Check if date is in range of a maintenance
    maintenance = Maintenance.objects.filter(start__lte=date.astimezone(), end__gte=date.astimezone())
    if maintenance.count():
        return True
    else:
        return False

def GetMaintenanceMessages():
    startdate = timezone.now()
    enddate = startdate+timedelta(days=5)

    # Empty list
    messages = []

    # Check all maintenances
    maintenances = Maintenance.objects.filter(start__gte=startdate, start__lte=enddate)

    # Append to list if any
    if maintenances.count():
        for maintenance in maintenances:
            messages.append(maintenance.reason)

    # Return messages
    return messages

def BlockedByMaintenance(date):
    # Check if date is in range of a maintenance
    maintenance = Maintenance.objects.filter(start__lte=date.astimezone(), end__gte=date.astimezone())
    if maintenance.count():
        return True
    else:
        return False

def GetMaintenanceMessages():
    startdate = timezone.now()
    enddate = startdate+timedelta(days=5)

    # Empty list
    messages = []

    # Check all maintenances
    maintenances = Maintenance.objects.filter(start__gte=startdate, start__lte=enddate)

    # Append to list if any
    if maintenances.count():
        for maintenance in maintenances:
            messages.append(maintenance.reason)

    # Return messages
    return messages

def GetValidTimeslots(date):
    # Possible timeslots each day
    timeslots = [0,3,6,9,12,15,18,21]
    validtimeslots = {}

    # Loop through all timeslots
    for slot in timeslots:
        
        # Exclude slots in maintenance
        checkdate = datetime.combine(date.date(),time(slot,00))
        if BlockedByMaintenance(checkdate):
            validtimeslots[slot] = 'invalid'

        else:
            # Exclude past dates
            if(date.date() < datetime.today().date()):
                validtimeslots[slot] = 'invalid'

            # Exclude todays timeslots that has passed
            elif(date.date() == datetime.today().date()):
                # Slot later today
                if(datetime.now().hour < slot):
                    validtimeslots[slot] = 'valid'

                # Ongoing slot, 1st or 2nd hour
                elif(datetime.now().hour == slot or datetime.now().hour-1 == slot):
                    validtimeslots[slot] = 'valid'

                # Ongoing slot, 3rd hour. Booking not possible last 30 minutes
                elif(datetime.now().hour-2 == slot and datetime.now().minute < 30):
                    validtimeslots[slot] = 'valid'

                # Passed slot
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
            logger.info(f"CreateNewBooking: Started booking for {email}")

            # Invalid domain or email
            if domain != settings.BOOKING_ALLOWED_DOMAIN:
                messages.add_message(request, messages.WARNING, f'E-postadressen du benyttet er ugyldig. Det er kun mulig å reservere med @{settings.BOOKING_ALLOWED_DOMAIN} e-postadresser.')
                logger.error(f"CreateNewBooking: Invalid domain {domain}")
                return redirect(f'/booking/{day}/{slot}/')
            
            # Check if user has active booking
            elif(Booking.objects.filter(email=email,timeslot__gte=datetime.now().astimezone()-timedelta(hours=3))):
                messages.add_message(request, messages.ERROR, 'Det finnes allerede en reservasjon for e-postadresse din! For å gi alle mulighet til å bruke miljøet, er det kun mulig å ha én aktiv reservasjon per bruker.')
                logger.error(f"CreateNewBooking: User {email} already have an active booking")
                return redirect(f'/booking/{day}/{slot}/')
            
            else:
                # Check if user email has an verified email
                user = VerifiedEmail.objects.filter(email=email).first()
                verified = False
                
                if(user):
                    # User exist
                    if(user.verified):
                        # Email is verified
                        verified = True

                # User email has been verified previously, so go ahead and get this booked!
                if(verified):
                    logger.info(f"CreateNewBooking: E-mail {email} already verified")
                    # Convert to datetime
                    todaysdate = datetime.combine(date.today(), datetime.min.time())
                    bookingtime = todaysdate + timedelta(days=day, hours=slot)
    
                    # Save data and print success-message
                    booking = Booking(timeslot=bookingtime.astimezone(), email=email)
                    booking.save()
                    messages.add_message(request, messages.SUCCESS, f'Din reservasjon for {bookingtime.date()} fra {"{:02}".format(bookingtime.hour)}:00-{"{:02}".format(bookingtime.hour+3)}:00 er bekreftet! Du vil straks motta en e-post med informasjon, i tillegg til en ny e-post med brukernavn og passord når din tidsperiode starter.')
                    logger.info(f"CreateNewBooking: Booking successfully created for {email} for timeslot {bookingtime.astimezone()}")

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
                    logger.info(f"CreateNewBooking: Sending booking confirmation email to {email}")
                    cml.SendEmail(email, 'Community Network - CML reservasjon', body)
    
                    # If booking of ongoing slot, create temporary password right away as scheduler will not catch this booking
                    if(bookingtime.astimezone() <= datetime.now().astimezone()):
                        logger.info(f"CreateNewBooking: Booking is for ongoing timeslot, creating password for {booking.email}")
                        cml.CreateTempUser(booking.email, booking.password)
    
                    # Return to home
                    return redirect('/')
                
                # User not verified, so send email and redirect to homepage with warning message
                else:
                    # Check first if user has an unverified entry in database
                    logger.warning(f"CreateNewBooking: Verification needed for {email}")

                    if (user):
                        # Old unverified entry found, reusing
                        logger.info(f"CreateNewBooking: Verification code reused for unverified {email}")
                        context = {
                            'verificationcode': user.verificationcode,
                            'cml_url': settings.CML_URL,
                            'booking_url': settings.BOOKING_URL,
                        }
                        
                    else: 
                        # Create entry in verification database
                        verification = VerifiedEmail(email=email)
                        verification.save()
                        logger.info(f"CreateNewBooking: New verification code created for {email}")

                        context = {
                            'verificationcode': verification.verificationcode,
                            'cml_url': settings.CML_URL,
                            'booking_url': settings.BOOKING_URL,
                        }
                    
                    # Send verification email using template
                    logger.info(f"CreateNewBooking: Sending verification code to {email}")
                    body = render_to_string('booking/email_verification.html', context)
                    cml.SendEmail(email, 'Din e-postadresse må verifiseres!', body)

                    # Return home with warning message
                    messages.add_message(request, messages.ERROR, 'Din e-postadresse må verifiseres før du kan reservere tid! Du mottar straks en epost med instruksjoner for hvordan du verifiserer deg.')
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

            # Blocked by maintenance
            if BlockedByMaintenance(bookingtime):
                logger.error(f"CreateNewBooking: Blocked by ongoing maintenance")
                return redirect('/')
    
            # Check if booking exist for requested date
            if(Booking.objects.filter(timeslot=bookingtime.astimezone())):
                messages.add_message(request, messages.ERROR, 'Det finnes allerede en reservasjon for denne datoen og tidsrommet.')
                logger.error(f"CreateNewBooking: Already an booking for this timeslot")
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
            logger.error(f"CreateNewBooking: Invalid values provided")
            return redirect('/')

def Verification(request, verificationcode=None):
    if verificationcode:
        # Find entry with this verificationcode
        verification = VerifiedEmail.objects.filter(verificationcode=verificationcode).first()
        logger.info(f"Verification: Looking for verification with code {verificationcode}")
        
        if verification:
            # Found! Set to verified and save
            logger.info(f"Verification: Verification code {verificationcode} matching with user {verification.email}")
            verification.verified = True
            verification.save()
            logger.info(f"Verification: User {verification.email} verified")
            messages.add_message(request, messages.SUCCESS, f'Din e-postadresse er nå verifisert! Du kan nå reservere ønsket tidspunkt under.')

        else:
            # Not found. Display warning message
            messages.add_message(request, messages.WARNING, f'Det ser ikke ut til at det finnes en e-postadresse i databasen med oppgitt verifikasjonskode.')
            logger.error(f"Verification: Verification code {verificationcode} NOT found")
        
    # Redirect to home
    return redirect('/')

def CancelBooking(request, cancelcode=None):
    if cancelcode:
        # Find booking with cancellation code
        booking = Booking.objects.filter(cancelcode=cancelcode).first()
        logger.info(f"CancelBooking: Looking for booking with cancel code {cancelcode}")
        if booking:
            # Booking found
            logger.info(f"CancelBooking: Found booking {booking.timeslot.astimezone()} matching cancel code {cancelcode}")
            logger.info(f"CancelBooking: This slot is booked by {booking.email}")

            # If booking in the future
            if(booking.timeslot.astimezone() > datetime.now().astimezone()-timedelta(hours=3)):

                # If ongoing timeslot, clean up
                if(booking.timeslot.astimezone() <= datetime.now().astimezone()):
                    # Clean up
                    logger.info(f"CancelBooking: Ongoing timeslot, starting cleanup for booking {booking.timeslot.astimezone()}")
                    cml.CleanUp(booking.email, booking.password)

                # Delete ongoing or future bookings
                booking.delete()
                messages.add_message(request, messages.SUCCESS, f'Din reservasjon ble kansellert! Takk for at du kansellerte og gav andre muligheten til å reservere!')
                logger.info(f"CancelBooking: Deleted booking {booking.timeslot.astimezone()}")
            else:
                # Booking in the past
                messages.add_message(request, messages.WARNING, f'Reservasjon funnet, men det er ikke mulig å kansellere reservasjoner som er gjort i fortiden.')
                logger.warning(f"CancelBooking: Trying to cancel booking in the past, ignoring")
        else:
            # Not found, print warning
            messages.add_message(request, messages.WARNING, f'Det ser ikke ut til at det finnes en reservasjoner i databasen med den kanselleringskoden. Ingen reservasjoner ble derfor slettet.')
            logger.error(f"CancelBooking: No booking found booking with cancel code {cancelcode}")

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
        'maintenance_messages': GetMaintenanceMessages()
    }
    
    return render(request, 'booking/index.html', context)
