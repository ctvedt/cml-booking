from django.db import models
import uuid

def random_uuid():
    random_uuid = uuid.uuid4().hex
    return random_uuid

class Booking(models.Model):
    timeslot = models.DateTimeField()
    email = models.EmailField(blank=False)
    password = models.CharField(max_length=50, blank=True, null=True, editable=True)
    cancelcode = models.CharField(max_length=50, blank=True, null=True, editable=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.timeslot} - {self.email}'

    def save(self, *args, **kwargs):
        self.password = random_uuid()
        self.cancelcode = random_uuid()
        super(Booking, self).save(*args, **kwargs)

class VerifiedEmail(models.Model):
    email = models.EmailField(blank=False)
    verificationcode = models.CharField(max_length=50, blank=True, null=True, editable=True)
    verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.email} - {self.verified}'

    def save(self, *args, **kwargs):
        self.verificationcode = random_uuid()
        super(VerifiedEmail, self).save(*args, **kwargs)

class Maintenance(models.Model):
    start = models.DateTimeField(blank=False)
    end = models.DateTimeField(blank=False)
    reason = models.CharField(max_length=250, blank=True, null=True, editable=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Maintenance {self.start} - {self.end}'