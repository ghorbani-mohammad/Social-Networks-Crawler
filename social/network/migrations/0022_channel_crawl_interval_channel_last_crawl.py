# Generated by Django 4.0.4 on 2022-04-17 04:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0021_alter_post_category_alter_post_ner_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='crawl_interval',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name='channel',
            name='last_crawl',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]