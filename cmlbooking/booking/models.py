from django.db import models

class Booking(models.Model):
    timeslot = models.DateTimeField()
    email = models.EmailField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.timeslot} - {self.email}'