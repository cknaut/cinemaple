# Generated by Django 2.2.4 on 2019-11-21 03:40

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0010_auto_20191114_2224'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationpermission',
            name='invitation_code',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='locationpermission',
            name='role',
            field=models.CharField(choices=[('HO', 'Host'), ('AM', 'Ambassador'), ('GU', 'Guest'), ('RW', 'Revoked Access')], default='GU', max_length=2),
        ),
    ]
