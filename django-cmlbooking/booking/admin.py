from django.contrib import admin
from .models import Booking

class BookingAdmin(admin.ModelAdmin):
    fields = ['timeslot', 'email', 'cancelcode', 'password']

admin.site.register(Booking, BookingAdmin)