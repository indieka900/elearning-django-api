# Generated by Django 5.0.6 on 2024-09-29 08:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('due_date', models.DateTimeField()),
                ('posted_date', models.DateTimeField(auto_now_add=True)),
                ('points', models.PositiveIntegerField()),
                ('link', models.URLField(null=True)),
                ('file', models.FileField(null=True, upload_to='assignment_files/')),
            ],
        ),
        migrations.CreateModel(
            name='AssignmentSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submitted_date', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField()),
                ('file', models.FileField(null=True, upload_to='submission_files/')),
                ('marks', models.PositiveIntegerField(null=True)),
                ('private_comment', models.TextField(null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('reviewed', 'Reviewed')], max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('duration', models.DurationField(default=datetime.timedelta(0))),
            ],
        ),
        migrations.CreateModel(
            name='CourseModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('objectives', models.TextField(default='Default objective')),
            ],
        ),
        migrations.CreateModel(
            name='CourseProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('icon', models.ImageField(upload_to='static/img/elearning/courses/icons/')),
                ('body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment_date', models.DateField(auto_now_add=True)),
                ('progress', models.IntegerField(default=0)),
                ('status', models.CharField(default='enrolled', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='LessonAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('instructions', models.TextField(default='Default instructions')),
                ('due_date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='LessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='LiveClassSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('start_time', models.TimeField()),
                ('date', models.DateTimeField()),
                ('duration', models.DurationField(default=datetime.timedelta(0))),
                ('room', models.CharField(help_text='Zoom link or physical venue', max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
        migrations.CreateModel(
            name='ModuleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ModuleProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_price', models.CharField(blank=True, max_length=50)),
                ('upfront', models.CharField(blank=True, max_length=50)),
                ('two_months', models.CharField(blank=True, max_length=50)),
                ('three_months', models.CharField(blank=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(choices=[('logged in', 'Logged In'), ('started', 'Started'), ('completed', 'Completed'), ('viewed', 'Viewed'), ('paused', 'Paused'), ('resumed', 'Resumed')], default='logged in', max_length=100)),
                ('duration', models.DurationField(default=datetime.timedelta(0))),
            ],
            options={
                'verbose_name_plural': 'User Activities',
            },
        ),
        migrations.CreateModel(
            name='UserProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_spent', models.DurationField(default=datetime.timedelta(0))),
                ('completed', models.BooleanField(default=False)),
                ('progress_percentage', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'User Progress',
            },
        ),
    ]