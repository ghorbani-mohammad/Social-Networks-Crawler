# Generated by Django 4.0.2 on 2022-02-26 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0016_channel_joined'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='imported',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
