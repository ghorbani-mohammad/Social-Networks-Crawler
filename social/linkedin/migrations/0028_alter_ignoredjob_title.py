# Generated by Django 4.1.7 on 2023-03-04 20:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("linkedin", "0027_alter_ignoredjob_language"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ignoredjob",
            name="title",
            field=models.CharField(max_length=200, null=True),
        ),
    ]
