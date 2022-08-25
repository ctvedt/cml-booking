from django.db import models
import uuid

class Booking(models.Model):
    timeslot = models.DateTimeField()
    email = models.EmailField(blank=False)
    password = models.CharField(max_length=50, default=uuid.uuid4().hex)
    cancelcode = models.CharField(max_length=50, default=uuid.uuid4().hex)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.timeslot} - {self.email}'