# Generated by Django 4.0.4 on 2022-05-08 06:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0022_channel_crawl_interval_channel_last_crawl"),
    ]

    operations = [
        migrations.AlterField(
            model_name="keyword",
            name="keyword",
            field=models.CharField(max_length=100),
        ),
    ]
