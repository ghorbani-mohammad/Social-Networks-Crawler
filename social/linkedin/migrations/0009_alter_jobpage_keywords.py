# Generated by Django 4.1.4 on 2022-12-30 17:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("linkedin", "0008_keyword_jobpage_keywords"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobpage",
            name="keywords",
            field=models.ManyToManyField(blank=True, to="linkedin.keyword"),
        ),
    ]
