from django import forms

class BookingForm(forms.Form):
    email = forms.CharField(label='E-postadresse', max_length=256)