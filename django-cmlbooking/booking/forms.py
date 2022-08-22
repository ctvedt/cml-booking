from django import forms

class BookingForm(forms.Form):
    email = forms.EmailField(label='E-postadresse', max_length=256)