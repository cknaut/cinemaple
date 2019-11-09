# Generated by Django 2.2.4 on 2019-11-09 21:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userhandling', '0008_remove_locationpermission_registration_complete'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationpermission',
            name='invitor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locationpermission_invitor', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='locationpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='locationpermission_user', to=settings.AUTH_USER_MODEL),
        ),
    ]