# Generated by Django 4.0.4 on 2022-05-15 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('network', '0025_rename_type_channel_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('link', models.CharField(max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PROCESSING', 'PROCESSING'), ('COMPLETED', 'COMPLETED')], default='PROCESSING', max_length=15)),
                ('type', models.CharField(choices=[('RASAD_1', 'RASAD_1'), ('RASAD_2', 'RASAD_2')], default='RASAD_1', max_length=15)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
