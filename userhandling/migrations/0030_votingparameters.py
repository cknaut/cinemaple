# Generated by Django 2.2 on 2019-06-21 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0029_auto_20190618_1804'),
    ]

    operations = [
        migrations.CreateModel(
            name='VotingParameters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote_disable_before', models.DurationField()),
                ('reminder_email_before', models.DurationField()),
                ('initial_email_before', models.DurationField()),
            ],
        ),
    ]