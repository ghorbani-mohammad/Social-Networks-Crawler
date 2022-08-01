# Generated by Django 4.0.5 on 2022-08-01 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0032_ignoredkeyword'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlockedKeyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('keyword', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]