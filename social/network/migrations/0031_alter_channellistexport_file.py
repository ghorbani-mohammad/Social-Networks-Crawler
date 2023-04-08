# Generated by Django 4.0.5 on 2022-07-04 03:22

from django.db import migrations, models
import network.models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0030_channellistexport"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channellistexport",
            name="file",
            field=models.FileField(
                blank=True, null=True, upload_to=network.models.channel_list_export_path
            ),
        ),
    ]
