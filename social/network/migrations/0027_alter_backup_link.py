# Generated by Django 4.0.4 on 2022-05-15 17:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("network", "0026_backup"),
    ]

    operations = [
        migrations.AlterField(
            model_name="backup",
            name="link",
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
