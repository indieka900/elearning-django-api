# utils.py
from datetime import timedelta
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Avg
from .models import CourseModule, Enrollment, Lesson, LessonProgress, UserActivity, LessonAssignment, ModuleAssignment, ModuleProgress, UserProgress
from django.db.models import Prefetch
from django.contrib.auth import get_user_model

User = get_user_model()

from django.utils import timezone

def calculate_time_spent(user, course, start_date=None, end_date=None):
    # This is an estimation based on module progress
    progress_query = ModuleProgress.objects.filter(user=user, module__course=course)
    if start_date:
        progress_query = progress_query.filter(last_updated__gte=start_date)
    if end_date:
        progress_query = progress_query.filter(last_updated__lt=end_date)
    
    # Assuming each 1% progress takes 1 minute (adjust as needed)
    total_progress = progress_query.aggregate(Sum('progress'))['progress__sum'] or 0
    return total_progress * 60  # Convert to seconds

def get_weekly_change(user, course, calculation_func):
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    this_week = calculation_func(user, course, start_date=week_ago, end_date=now)
    last_week = calculation_func(user, course, start_date=two_weeks_ago, end_date=week_ago)

    if last_week > 0:
        change = ((this_week - last_week) / last_week) * 100
    else:
        change = 100 if this_week > 0 else 0

    return round(change, 1)

def calculate_course_progress(user, course, start_date=None, end_date=None):
    progress_query = ModuleProgress.objects.filter(user=user, module__course=course)
    if start_date:
        progress_query = progress_query.filter(last_updated__gte=start_date)
    if end_date:
        progress_query = progress_query.filter(last_updated__lt=end_date)
    return progress_query.aggregate(Avg('progress'))['progress__avg'] or 0


def get_monthly_progress(user, course):
    now = timezone.now()
    six_months_ago = now - timedelta(days=180)
    monthly_progress = (
        ModuleProgress.objects.filter(
            user=user,
            module__course=course,
            last_updated__gte=six_months_ago
        )
        .annotate(month=TruncMonth('last_updated'))
        .values('month')
        .annotate(avg_progress=Avg('progress'))
        .order_by('month')
    )
    return list(monthly_progress)

def calculate_user_course_progress(user, course=None):
    base_query = ModuleProgress.objects.filter(user=user)
    
    if course:
        course_modules = CourseModule.objects.filter(course=course)
        progress_query = base_query.filter(module__in=course_modules)
        
        average_progress = progress_query.aggregate(Avg('progress'))['progress__avg'] or 0
        return average_progress


def get_user_courses_assignments(user_id):
    """
    Retrieve assignment data for all courses a user is enrolled in.
    
    :param user_id: ID of the user
    :return: Dictionary containing assignment data for each enrolled course
    """
    user = User.objects.filter(id=user_id).prefetch_related(
        Prefetch('enrollment_set', queryset=Enrollment.objects.select_related('course')),
        Prefetch('enrollment_set__course__modules', queryset=CourseModule.objects.prefetch_related(
            Prefetch('assignments', queryset=ModuleAssignment.objects.filter(user_id=user_id)),
            Prefetch('lessons', queryset=Lesson.objects.prefetch_related(
                Prefetch('assignments', queryset=LessonAssignment.objects.filter(user_id=user_id))
            ))
        ))
    ).first()

    if not user:
        return None

    courses_data = {}

    for enrollment in user.enrollment_set.all():
        course = enrollment.course
        module_assignments = []
        lesson_assignments = []
        total_assignments = 0
        completed_assignments = 0

        for module in course.modules.all():
            module_assignments.extend(list(module.assignments.all()))
            for lesson in module.lessons.all():
                lesson_assignments.extend(list(lesson.assignments.all()))

        all_assignments = module_assignments + lesson_assignments
        total_assignments = len(all_assignments)
        completed_assignments = sum(1 for a in all_assignments if a.completed)

        courses_data[course.id] = {
            # 'course_name': course.name,
            # 'module_assignments': module_assignments,
            # 'lesson_assignments': lesson_assignments,
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'completion_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
        }

    return courses_data


# def calculate_time_spent(user):
#     total_time = UserActivity.objects.filter(user=user).aggregate(total_time=Sum('duration'))
#     return total_time['total_time'] if total_time['total_time'] else timedelta()

def calculate_course_completion(user):
    # Logic to calculate course completion rate
    # Example: 
    total_enrollments = user.enrollment_set.count()
    completed_enrollments = user.enrollment_set.filter(progress=100).count()
    completion_rate = (completed_enrollments / total_enrollments) * 100 if total_enrollments != 0 else 0.00
    return completion_rate

def calculate_module_progress(user, module):
    # Calculate module progress based on user activities
    total_actions = UserActivity.objects.filter(user=user, module=module).count()
    completed_actions = UserActivity.objects.filter(user=user, module=module, action='completed').count()

    if total_actions > 0:
        progress_percentage = (completed_actions / total_actions) * 100
    else:
        progress_percentage = 0.00

    # Update or create UserProgress for this module
    user_progress, created = UserProgress.objects.get_or_create(user=user, module=module)
    user_progress.progress_percentage = progress_percentage
    user_progress.save()

    return progress_percentage

def calculate_user_progress(user, course):
    modules = CourseModule.objects.filter(course=course)
    module_progresses = []
    for module in modules:
        # Get all lessons for the module
        lessons = Lesson.objects.filter(module=module)

        # Calculate lesson completion for the user
        lesson_progress = LessonProgress.objects.filter(user=user, lesson__in=lessons)
        
        # Calculate the average lesson progress
        completed_lessons = lesson_progress.filter(completed=True).count()
        total_lessons = lessons.count()
        
        if total_lessons > 0:
            lesson_progress_percentage = (completed_lessons / total_lessons) * 100
        else:
            lesson_progress_percentage = 0

        # Record module progress
        module_progresses.append({
            'module': module.title,
            'progress': round(lesson_progress_percentage, 2),
        })

    # Calculate the average module progress
    if module_progresses:
        total_module_progress = sum(module['progress'] for module in module_progresses)
        average_module_progress = total_module_progress / len(module_progresses)
    else:
        average_module_progress = 0

    return {
        'course_progress': round(average_module_progress, 2),
        'module_progresses': module_progresses,
    }



