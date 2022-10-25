from django.contrib import admin
from .models import Booking, VerifiedEmail, Maintenance

class BookingAdmin(admin.ModelAdmin):
    fields = ['timeslot', 'email', 'cancelcode', 'password']

admin.site.register(Booking, BookingAdmin)

class VerifiedEmailAdmin(admin.ModelAdmin):
    fields = ['email', 'verified']

admin.site.register(VerifiedEmail, VerifiedEmailAdmin)

class MaintenanceAdmin(admin.ModelAdmin):
    fields = ['start', 'end', 'reason']

admin.site.register(Maintenance, MaintenanceAdmin)