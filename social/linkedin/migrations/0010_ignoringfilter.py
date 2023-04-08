# Generated by Django 4.1.4 on 2023-01-06 17:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("linkedin", "0009_alter_jobpage_keywords"),
    ]

    operations = [
        migrations.CreateModel(
            name="IgnoringFilter",
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
                (
                    "place",
                    models.CharField(
                        choices=[("location", "location"), ("title", "title")],
                        max_length=15,
                    ),
                ),
                ("keyword", models.TextField(null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
