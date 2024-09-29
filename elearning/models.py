from django.db import models
from user_auth.models import Instructor as User, Student
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


# Create your models here.
class Course(models.Model):
    """Model for course."""
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    description = models.TextField()
    duration = models.DurationField(default=timedelta())
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')

    def __str__(self) -> str:
        return self.name


class CourseProfile(models.Model):
    """Model for course profile."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    icon = models.ImageField(upload_to="static/img/elearning/courses/icons/")
    body = models.TextField()

    def __str__(self) -> str:
        return str(self.course)


class CourseModule(models.Model):
    """Model for course module."""
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    objectives = models.TextField(default='Default objective')

    def __str__(self) -> str:

        return f"{self.title} - {self.course.name}"

class Lesson(models.Model):
    """Model for lesson."""
    module = models.ForeignKey(CourseModule, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self) -> str:
        return f"{self.title} - {self.module.title}"

class SubscriptionPlan(models.Model):
    """Model for subscription plan."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    display_price = models.CharField(max_length=50, blank=True)
    upfront = models.CharField(max_length=50, blank=True)
    two_months = models.CharField(max_length=50, blank=True)
    three_months = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.course.name}"


class Enrollment(models.Model):
    """Model for enrollment."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)
    progress = models.IntegerField(default=0)  # Percentage complete
    status = models.CharField(max_length=20, default='enrolled')

    def __str__(self) -> str:
        return f'{self.student.user.username} - {self.course.name}'

class ModuleProgress(models.Model):
    """Model for tracking user progress in a module."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.user.username} - {self.module.title} - {self.progress}%'

class LessonProgress(models.Model):
    """Model for tracking user progress in a lesson."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f'{self.user.username} - {self.lesson.title} - {"Completed" if self.completed else "Incomplete"}'

class Assignment(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    posted_date = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, null=True, blank=True)
    points = models.PositiveIntegerField()
    link = models.URLField(null=True)
    file = models.FileField(upload_to="assignment_files/", null=True)
    instructor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_assignments')

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    submitted_date = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    file = models.FileField(upload_to="submission_files/", null=True)
    marks = models.PositiveIntegerField(null=True)
    private_comment = models.TextField(null=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('reviewed', 'Reviewed')])

    def __str__(self):
        return f"{self.student.user.username}'s submission for {self.assignment.title}"

    
class LessonAssignment(models.Model):
    """Model for assignments in lessons."""
    lesson = models.ForeignKey(Lesson, related_name='assignments', on_delete=models.CASCADE)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    instructions = models.TextField(default='Default instructions')
    due_date = models.DateTimeField()
    

class ModuleAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    module = models.ForeignKey(CourseModule, related_name='assignments', on_delete=models.CASCADE)
    lesson_assignment = models.OneToOneField(LessonAssignment, related_name='module_assignment', on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.lesson_assignment:
            self.title = self.lesson_assignment.title
            self.description = self.lesson_assignment.description
            self.due_date = self.lesson_assignment.due_date
            self.completed = self.lesson_assignment.completed
        super().save(*args, **kwargs)

class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, choices=[
        ('logged in', 'Logged In'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('viewed', 'Viewed'),
        ('paused', 'Paused'),
        ('resumed', 'Resumed'),
    ], default='logged in')  # Action taken by the user (e.g., 'started', 'completed', 'viewed')
    duration = models.DurationField(default=timedelta())  # Duration of the action
    
    class Meta:
        verbose_name_plural = 'User Activities'

    def __str__(self):
        return f"{self.user.username} - {self.action} {self.module} in {self.course}"

    def save(self, *args, **kwargs):
        # Calculate duration only if the object is being updated (not on initial creation)
        if self.pk:
            previous_activity = UserActivity.objects.filter(
                user=self.user, course=self.course, module=self.module
            ).order_by('-timestamp').first()

            if previous_activity:
                time_difference = self.timestamp - previous_activity.timestamp
                self.duration = max(time_difference, timedelta())  # Ensure duration is not negative

        super().save(*args, **kwargs)

class UserProgress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE)
    time_spent = models.DurationField(default=timedelta())  # Total time spent by user on this module
    completed = models.BooleanField(default=False)  # Whether the user has completed this module
    progress_percentage = models.IntegerField(default=0)  # Progress percentage (0-100)

    class Meta:
        verbose_name_plural = 'User Progress'
        
    def save(self, *args, **kwargs):
        if not self.course:
            self.course = self.module.course
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.module} in {self.course}"


class LiveClassSchedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_class_schedules')
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='instructed_schedules')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.TimeField()
    date = models.DateTimeField()
    duration = models.DurationField(default=timedelta())
    room = models.CharField(max_length=255, help_text="Zoom link or physical venue")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.course.name} - {self.title} at {self.start_time}"

    def next_occurrence(self):
        now = timezone.localtime()
        today = now.date()
        class_time = timezone.make_aware(timezone.datetime.combine(today, self.start_time))
        
        if class_time <= now:
            # If the class time has passed for today, schedule for tomorrow
            class_time += timezone.timedelta(days=1)
        
        return class_time


