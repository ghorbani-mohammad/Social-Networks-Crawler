# Generated by Django 4.0.5 on 2022-08-01 20:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0033_blockedkeyword'),
    ]

    operations = [
        migrations.AddField(
            model_name='keyword',
            name='ignored',
            field=models.BooleanField(default=False),
        ),
    ]