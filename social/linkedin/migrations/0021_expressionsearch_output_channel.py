# Generated by Django 4.1.4 on 2023-01-12 08:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0003_channel'),
        ('linkedin', '0020_expressionsearch'),
    ]

    operations = [
        migrations.AddField(
            model_name='expressionsearch',
            name='output_channel',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linkedin_expression_searches', to='notification.channel'),
        ),
    ]
