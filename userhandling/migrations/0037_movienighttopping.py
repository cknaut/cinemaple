# Generated by Django 2.2 on 2019-07-02 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('userhandling', '0036_delete_movienighttopping'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovienightTopping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movienight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.MovieNightEvent')),
                ('toping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userhandling.Toping')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]