# Generated by Django 4.1.4 on 2023-01-12 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linkedin', '0019_alter_ignoredjob_location_alter_ignoredjob_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpressionSearch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('url', models.URLField()),
                ('name', models.CharField(max_length=100)),
                ('enable', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]