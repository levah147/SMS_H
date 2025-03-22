# Generated by Django 5.1.5 on 2025-03-21 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0002_attendance_is_absent'),
    ]

    operations = [
        migrations.RenameField(
            model_name='term',
            old_name='resumption_date',
            new_name='beginning_of_term',
        ),
        migrations.AddField(
            model_name='term',
            name='end_of_term',
            field=models.DateField(blank=True, null=True),
        ),
    ]
