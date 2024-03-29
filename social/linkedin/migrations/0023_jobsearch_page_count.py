# Generated by Django 4.1.5 on 2023-01-26 07:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("linkedin", "0022_expressionsearch_last_crawl_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobsearch",
            name="page_count",
            field=models.PositiveSmallIntegerField(
                default=1, help_text="how many pages should be crawled"
            ),
        ),
    ]
