# Generated by Django 4.0.4 on 2022-05-23 06:19

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JobPage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("url", models.URLField()),
                ("name", models.CharField(max_length=100)),
                ("enable", models.BooleanField(default=True)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
