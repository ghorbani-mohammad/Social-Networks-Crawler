# Generated by Django 4.1.4 on 2023-01-12 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linkedin', '0021_expressionsearch_output_channel'),
    ]

    operations = [
        migrations.AddField(
            model_name='expressionsearch',
            name='last_crawl_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
