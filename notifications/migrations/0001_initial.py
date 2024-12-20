# Generated by Django 5.0.6 on 2024-09-29 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('chat', 'Chat'), ('live_class', 'Live Class'), ('assignment', 'Assignment'), ('submission', 'Submission'), ('transaction', 'Transaction')], max_length=20)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat', models.BooleanField(default=True)),
                ('live_class', models.BooleanField(default=True)),
                ('assignment', models.BooleanField(default=True)),
                ('submission', models.BooleanField(default=True)),
                ('transaction', models.BooleanField(default=True)),
            ],
        ),
    ]
