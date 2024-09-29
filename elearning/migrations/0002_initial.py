# Generated by Django 5.0.6 on 2024-09-29 08:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('elearning', '0001_initial'),
        ('user_auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='instructor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_assignments', to='user_auth.instructor'),
        ),
        migrations.AddField(
            model_name='assignmentsubmission',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.assignment'),
        ),
        migrations.AddField(
            model_name='assignmentsubmission',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.student'),
        ),
        migrations.AddField(
            model_name='course',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='user_auth.instructor'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='coursemodule',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='elearning.course'),
        ),
        migrations.AddField(
            model_name='assignment',
            name='module',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='courseprofile',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.student'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='lessonassignment',
            name='lesson',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='elearning.lesson'),
        ),
        migrations.AddField(
            model_name='lessonassignment',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='lessonprogress',
            name='lesson',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.lesson'),
        ),
        migrations.AddField(
            model_name='lessonprogress',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='liveclassschedule',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='live_class_schedules', to='elearning.course'),
        ),
        migrations.AddField(
            model_name='liveclassschedule',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instructed_schedules', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='moduleassignment',
            name='lesson_assignment',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='module_assignment', to='elearning.lessonassignment'),
        ),
        migrations.AddField(
            model_name='moduleassignment',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='moduleassignment',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='moduleprogress',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='moduleprogress',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='useractivity',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userprogress',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.course'),
        ),
        migrations.AddField(
            model_name='userprogress',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elearning.coursemodule'),
        ),
        migrations.AddField(
            model_name='userprogress',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]