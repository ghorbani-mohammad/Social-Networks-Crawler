# Generated by Django 4.0.1 on 2022-01-22 06:26

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0002_publisher_description"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Publisher",
            new_name="Channel",
        ),
        migrations.RenameField(
            model_name="post",
            old_name="publisher",
            new_name="channel",
        ),
    ]
