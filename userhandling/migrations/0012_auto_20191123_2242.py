# Generated by Django 2.2.4 on 2019-11-24 03:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0011_auto_20191120_2240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationpermission',
            name='invitation_code',
            field=models.UUIDField(blank=True),
        ),
    ]