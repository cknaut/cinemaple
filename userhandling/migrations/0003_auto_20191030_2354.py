# Generated by Django 2.2.4 on 2019-10-31 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0002_location_loc_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='location',
        ),
        migrations.AddField(
            model_name='profile',
            name='location',
            field=models.ManyToManyField(to='userhandling.Location'),
        ),
    ]
