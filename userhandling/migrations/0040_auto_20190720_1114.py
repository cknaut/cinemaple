# Generated by Django 2.2 on 2019-07-20 15:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userhandling', '0039_auto_20190720_0827'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movienightevent',
            name='AttendenceList',
        ),
        migrations.RemoveField(
            model_name='movienighttopping',
            name='movienight',
        ),
        migrations.RemoveField(
            model_name='movienighttopping',
            name='registered_at',
        ),
        migrations.RemoveField(
            model_name='movienighttopping',
            name='user',
        ),
        migrations.RemoveField(
            model_name='votepreference',
            name='movienight',
        ),
        migrations.RemoveField(
            model_name='votepreference',
            name='user',
        ),
        migrations.CreateModel(
            name='UserAttendence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('movienight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.MovieNightEvent')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='movienighttopping',
            name='user_attendence',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='userhandling.UserAttendence'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='votepreference',
            name='user_attendence',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='userhandling.UserAttendence'),
            preserve_default=False,
        ),
    ]