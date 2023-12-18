# Generated by Django 4.2 on 2023-12-17 11:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_profile_about_me'),
        ('linkedin', '0030_delete_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobsearch',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='job_search', to='user.profile'),
        ),
    ]