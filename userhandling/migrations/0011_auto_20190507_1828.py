# Generated by Django 2.2 on 2019-05-07 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0010_passwordreset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='passwordreset',
            name='reset_key',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]