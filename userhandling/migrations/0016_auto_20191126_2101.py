# Generated by Django 2.2.4 on 2019-11-27 02:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0015_auto_20191126_2007'),
    ]

    operations = [
        migrations.RenameField(
            model_name='locationpermission',
            old_name='revoced_access',
            new_name='revoked_access',
        ),
    ]