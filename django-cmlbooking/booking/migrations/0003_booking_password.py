# Generated by Django 4.1 on 2022-08-21 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_booking_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='password',
            field=models.TextField(default='NO_PASSWORD_SET'),
        ),
    ]