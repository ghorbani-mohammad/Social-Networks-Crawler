# Generated by Django 4.0.1 on 2022-01-22 06:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0004_remove_channel_is_channel"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="body",
            field=models.TextField(max_length=100),
        ),
    ]
