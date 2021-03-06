# Generated by Django 2.2 on 2019-10-28 01:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('street', models.CharField(max_length=200)),
                ('zip_code', models.CharField(max_length=200)),
                ('city', models.CharField(max_length=200)),
                ('state', models.CharField(max_length=200)),
                ('country', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tmdbID', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=500)),
                ('year', models.CharField(max_length=4)),
                ('director', models.CharField(max_length=500)),
                ('producer', models.CharField(max_length=500)),
                ('runtime', models.CharField(max_length=10)),
                ('actors', models.CharField(max_length=500)),
                ('plot', models.TextField(max_length=2000)),
                ('country', models.CharField(max_length=500)),
                ('posterpath', models.CharField(max_length=100)),
                ('trailerlink', models.CharField(max_length=200)),
                ('on_netflix', models.BooleanField(default=False)),
                ('netflix_link', models.TextField(blank=True)),
                ('on_amazon', models.BooleanField(default=False)),
                ('amazon_link', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MovieNightEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('motto', models.CharField(max_length=200)),
                ('description', models.TextField(max_length=10000)),
                ('date', models.DateTimeField(verbose_name='date published')),
                ('isdraft', models.BooleanField(default=True)),
                ('isdeactivated', models.BooleanField(default=False)),
                ('MaxAttendence', models.IntegerField(default=25)),
                ('MovieList', models.ManyToManyField(blank=True, to='userhandling.Movie')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.Location')),
            ],
        ),
        migrations.CreateModel(
            name='PasswordReset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reset_key', models.CharField(blank=True, max_length=40)),
                ('reset_used', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Topping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topping', models.CharField(max_length=300)),
            ],
        ),
        migrations.CreateModel(
            name='UserAttendence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('registration_complete', models.BooleanField(default=False)),
                ('movienight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.MovieNightEvent')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VotingParameters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vote_disable_before', models.DurationField()),
                ('reminder_email_before', models.DurationField()),
                ('initial_email_after', models.DurationField()),
            ],
        ),
        migrations.CreateModel(
            name='VotePreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference', models.IntegerField(blank=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.Movie')),
                ('user_attendence', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='userhandling.UserAttendence')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True, max_length=500)),
                ('email_buffer', models.EmailField(default='', max_length=254)),
                ('location', models.CharField(blank=True, max_length=30)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('activation_key', models.CharField(blank=True, max_length=40)),
                ('key_expires', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MovienightTopping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.Topping')),
                ('user_attendence', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='userhandling.UserAttendence')),
            ],
        ),
    ]
