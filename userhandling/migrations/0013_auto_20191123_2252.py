# Generated by Django 2.2.4 on 2019-11-24 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0012_auto_20191123_2242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locationpermission',
            name='invitation_code',
            field=models.UUIDField(null=True),
        ),
    ]
