# Generated by Django 2.2 on 2019-06-21 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userhandling', '0031_auto_20190621_1615'),
    ]

    operations = [
        migrations.AddField(
            model_name='movienightevent',
            name='isdeactivated',
            field=models.BooleanField(default=False),
        ),
    ]