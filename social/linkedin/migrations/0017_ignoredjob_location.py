# Generated by Django 4.1.4 on 2023-01-07 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linkedin', '0016_ignoredjob_company_ignoredjob_language_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ignoredjob',
            name='location',
            field=models.CharField(max_length=50, null=True),
        ),
    ]