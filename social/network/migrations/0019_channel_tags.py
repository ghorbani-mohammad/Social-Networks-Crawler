# Generated by Django 4.0.2 on 2022-02-27 15:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0018_tag"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="channels", to="network.Tag"
            ),
        ),
    ]
