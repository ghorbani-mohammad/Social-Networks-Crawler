# Generated by Django 4.0.1 on 2022-01-22 06:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="publisher",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
