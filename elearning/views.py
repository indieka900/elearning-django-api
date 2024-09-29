from statistics import mean
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.db import transaction
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Prefetch, Case, When, F, ExpressionWrapper, TimeField, Count, Q, When
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import status
from notifications.services import NotificationService
from payments.serializers import TransactionSerializer
from payments.utils import PaymentUtils
from user_auth.models import CustomUser as User, Instructor, Student
from user_auth.utils import generate_password
from .models import (
    Assignment, AssignmentSubmission, Course, CourseModule, CourseProfile, Enrollment, Lesson, 
    LessonAssignment, LessonProgress, LiveClassSchedule, ModuleAssignment, 
    ModuleProgress, UserProgress, SubscriptionPlan,
)
from .send_mails import send_invitation_emails
from .serializers import (
    AssignmentSerializer, AssignmentSubmissionSerializer, Assignment_SubmissionSerializer,
    ModuleSerializer, CourseSerializer, CourseProfileSerializer, 
    EnrollmentSerializer, LessonAssignmentSerializer, 
    LessonProgressSerializer, LessonSerializer, 
    LiveClassScheduleSerializer, ModuleAssignmentSerializer, 
    ModuleProgressSerializer, UserProgressSerializer, CourseDetailSerializer,
    SubscriptionPlanSerializer, AssignmentMarkingSerializer, StudentAssignmentSerializer
)
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.db.models import Prefetch
from .utils import (
    calculate_course_progress, calculate_time_spent,
    calculate_module_progress, get_monthly_progress, get_weekly_change
)

class SubmissionViewSet(ModelViewSet):
    queryset = AssignmentSubmission.objects.all()
    serializer_class = Assignment_SubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        if request.user.role == 'Student':
            student = Student.objects.get(user = request.user)
            queryset = queryset.filter(student = student)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    
class CourseViewSet(ModelViewSet):
    """Viewset for course model."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['full_detail', 'assignments']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def assignments(self, request, pk=None):
        """
        Custom action to retrieve all assignments for a specific course.
        URL: /api/elearning/courses/{course_id}/assignments/
        Method: GET
        """
        course = self.get_object()
        assignments = Assignment.objects.filter(course=course)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path="course-details")
    def full_detail(self, request):
        """
        Custom action to retrieve full details of the enrolled course, or courses the instructor teaches,
        or all courses if the user is an admin.
        URL: /api/elearning/courses/course-details/
        Method: GET
        """
        user = request.user

        try:
            if user.role == 'Administrator':
                courses = Course.objects.prefetch_related('modules__lessons', 'instructor').all()
                
            elif user.role == 'Instructor':
                courses = Course.objects.prefetch_related('modules__lessons', 'instructor').filter(instructor__user=user)

            elif user.role == 'Student':
                student = Student.objects.get(user=user)
                enrollments = Enrollment.objects.filter(student=student).select_related('course')

                if not enrollments:
                    return Response({"error": "No active enrollment found for this student."}, status=status.HTTP_404_NOT_FOUND)

                course_ids = [enrollment.course.id for enrollment in enrollments]
                courses = Course.objects.prefetch_related('modules__lessons', 'instructor').filter(id__in=course_ids)

            else:
                return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = CourseDetailSerializer(courses, many=True, context={'request': request})
            return Response(serializer.data)

        except Student.DoesNotExist:
            return Response({"error": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except ObjectDoesNotExist:
            return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CourseProfileViewSet(ModelViewSet):
    """Viewset for course profile model."""

    queryset = CourseProfile.objects.all()
    serializer_class = CourseProfileSerializer
    permission_classes = [AllowAny]


class CourseModuleViewSet(ModelViewSet):
    """Viewset for course module model."""
    queryset = CourseModule.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """
        Custom action to retrieve all assignments for a specific course module.
        URL: /api/elearning/modules/{module_id}/assignments/
        Method: GET
        """
        module = self.get_object()
        assignments = Assignment.objects.filter(module=module)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

class SubscriptionPlanViewSet(ModelViewSet):
    """Viewset for subscription plan model."""
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]

class LessonViewSet(ModelViewSet):
    """Viewset for lesson model."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [AllowAny]

class LiveClassScheduleViewSet(ModelViewSet):
    queryset = LiveClassSchedule.objects.all()
    serializer_class = LiveClassScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        course = serializer.validated_data['course']
        if user.role == 'Instructor' or course.instructor is None:
            instructor = user
        else:
            instructor = course.instructor.user

        live_class = serializer.save(instructor=instructor)
        self.notify_users(live_class)

    def get_queryset(self):
        now = timezone.localtime()
        user = self.request.user
        if user.role == 'Administrator':
            queryset = LiveClassSchedule.objects.filter(is_active=True)
        elif user.role == 'Instructor':
            queryset = LiveClassSchedule.objects.filter(instructor=user, is_active=True)
        else:
            student = Student.objects.get(user=user)
            enrolled_courses = Course.objects.filter(enrollment__student=student)
            queryset = LiveClassSchedule.objects.filter(course__in=enrolled_courses, is_active=True)

        for schedule in queryset:
            schedule.next_class_time = schedule.next_occurrence()

        return sorted(queryset, key=lambda x: x.next_class_time)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = LiveClassSchedule.objects.get(pk=kwargs['pk'])  # Directly fetch without filters
        except LiveClassSchedule.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = LiveClassSchedule.objects.get(pk=kwargs['pk'])
        except LiveClassSchedule.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if user.role == 'Administrator' or (user.role == 'Instructor' and instance.instructor == user):
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise PermissionDenied("You do not have permission to delete this live class.")

    def perform_destroy(self, instance : LiveClassSchedule):
        instance.is_active = False
        instance.save()

    @action(detail=False, methods=['get'], url_path="next-class")
    def next_class(self, request):
        queryset = self.get_queryset()
        if queryset:
            next_class = queryset[0] 
            serializer = self.get_serializer(next_class)
            return Response(serializer.data)
        return Response({"message": "No upcoming classes found."})

    def notify_users(self, live_class : LiveClassSchedule):
        # Get all users enrolled in the course
        enrolled_students = live_class.course.enrollment_set.values_list('student__user', flat=True)
        
        # Fetch the actual User objects from the IDs
        users = User.objects.filter(id__in=enrolled_students)

        for user in users:
            # Send a notification to each enrolled user
            NotificationService.send_notification(
                user=user,
                notification_type='live_class',
                content=f'A new live class "{live_class.title}" for {live_class.course.name} is scheduled for {live_class.date} at {live_class.start_time}. Venue/Link: {live_class.link_or_venue}',
                email_subject='New Live Class Scheduled',
                email_body=f'Dear {user.username},\n\nA new live class "{live_class.title}" for the course "{live_class.course.name}" has been scheduled for {live_class.date} at {live_class.start_time}.\nVenue/Link: {live_class.link_or_venue}\n\nBest regards,\nYour Team',
            )

class EnrollmentViewSet(ModelViewSet):
    """Viewset for enrollment model."""
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Enrollment.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course')
        course = Course.objects.get(id=course_id)

        # Check if the user is already enrolled in the course
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response({'detail': 'User is already enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new enrollment
        enrollment = Enrollment.objects.create(user=user, course=course, status='enrolled')
        # Automatically create a CourseProfile for the user
        CourseProfile.objects.create(course=course, icon='path/to/default/icon.png', body='Default body content')

        serializer = self.get_serializer(enrollment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ModuleProgressViewSet(ModelViewSet):
    """Viewset for module progress model."""
    queryset = ModuleProgress.objects.all()
    serializer_class = ModuleProgressSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        module_id = request.data.get('module')
        module = CourseModule.objects.get(id=module_id)

        # Ensure only one progress record per module per user
        if ModuleProgress.objects.filter(user=user, module=module).exists():
            return Response({'detail': 'Progress for this module already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create initial progress record for the module
        progress = ModuleProgress.objects.create(user=user, module=module, progress=0.00)
        serializer = self.get_serializer(progress)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user = request.user
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update progress percentage based on user activities
        calculate_module_progress(user, instance.module)  # Update progress logic

        serializer.save()
        return Response(serializer.data)

class LessonProgressViewSet(ModelViewSet):
    """Viewset for lesson progress model."""
    queryset = LessonProgress.objects.all()
    serializer_class = LessonProgressSerializer

    def update(self, request, *args, **kwargs):
        user = request.user
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update lesson completion based on user activities
        if 'completed' in request.data and request.data['completed']:
            instance.completed = True
            instance.save()

        serializer.save()
        return Response(serializer.data)


class ModuleAssignmentViewSet(ModelViewSet):
    """Viewset for module assignment model."""
    queryset = ModuleAssignment.objects.all()
    serializer_class = ModuleAssignmentSerializer
    permission_classes = [AllowAny]

class LessonAssignmentViewSet(ModelViewSet):
    """Viewset for lesson assignment model."""
    queryset = LessonAssignment.objects.all()
    serializer_class = LessonAssignmentSerializer
    permission_classes = [AllowAny]
    
class AssignmentViewSet(ModelViewSet):
    """
    A viewset that provides the standard actions for the Assignment model.
    """
    
    queryset = Assignment.objects.all()
    permission_classes = (IsAuthenticated, )
    def get_serializer_class(self):
        if self.request.user.role == 'Student':
            return StudentAssignmentSerializer
        return AssignmentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'Student':
            student = Student.objects.get(user=user)
            return Assignment.objects.filter(course__enrollment__student=student)
        elif user.role == 'Instructor':
            instructor = Instructor.objects.get(user=user)
            return Assignment.objects.filter(course__instructor=instructor)
        elif user.is_staff:
            return Assignment.objects.all()
        else:
            return Assignment.objects.none()

    def perform_create(self, serializer):
        """
        Override the creation process to automatically set the instructor
        to the currently authenticated user.
        """
        try:
            instructor = Instructor.objects.get(user=self.request.user)
        except Instructor.DoesNotExist:
            raise ValidationError("Instructor profile not found for the current user.")
        course_id = serializer.validated_data.get('course', None)
        due_date = serializer.validated_data.get('due_date', None)
        assignment = serializer.save(instructor=instructor, due_date=due_date)
        if due_date is None:
            raise ValidationError("Due date is required bana.")
        enrolled_students = Enrollment.objects.filter(course=assignment.course).select_related('student')

        for enrollment in enrolled_students:
            student = enrollment.student
            NotificationService.send_notification(
                user=student.user,
                notification_type='assignment',
                content=f'A new assignment "{assignment.title}" has been posted for {assignment.course.name}.',
                email_subject='New Assignment Posted',
                email_body=f"Dear {student.user.username},\n\nA new assignment titled '{assignment.title}' has been posted for the course '{assignment.course.name}'. Please review the assignment and complete it by the due date: {assignment.due_date.strftime('%d %b, %Y %H:%M')}.",
            )

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    @transaction.atomic
    def submit_marks(self, request, pk=None):
        """
        Submit marks and private comments for a student's assignment submission.

        This action is restricted to admin users and instructors.
        """
        user = request.user
        if not (user.is_staff or user.role == 'Instructor'):
            raise PermissionDenied("Only administrators and instructors can submit marks.")
        
        serializer = AssignmentMarkingSerializer(data=request.data)
        assignment = self.get_object()
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        submission = get_object_or_404(
            AssignmentSubmission, 
            id=request.data.get('submission_id'), 
            assignment=assignment
        )

        submission.marks = serializer.validated_data['marks']
        submission.private_comment = serializer.validated_data['private_comment']
        submission.status = 'reviewed'
        submission.save()

        return Response({
            'message': f"Marks and comments submitted for {submission.student.user.username}.",
            'submission': AssignmentSubmissionSerializer(submission).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        Custom action to allow students to submit their work for an assignment.
        URL: /api/elearning/assignments/{assignment_id}/submit/
        Method: POST
        """
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            raise ValidationError("No student profile found for the current user.")

        assignment = self.get_object()
        serializer = AssignmentSubmissionSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                assignment=assignment,
                student=student, 
                status='pending'
            )

            NotificationService.send_notification(
                user=student.user,
                notification_type='submission',
                content=f"Your submission for the assignment '{assignment.title}' has been received.",
                email_subject="Assignment Submission Received",
                email_body=f"Dear {student.user.username},\n\nYour submission for the assignment '{assignment.title}' has been successfully received."
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """
        Custom action to retrieve all submissions for a specific assignment.
        URL: /api/elearning/assignments/{assignment_id}/submissions/
        Method: GET
        """
        assignment = self.get_object()
        if (request.user.role == "Student"):
            student = Student.objects.get(user=request.user)
            submissions = AssignmentSubmission.objects.filter(Q(assignment=assignment) & Q(student=student))
        else:
            submissions = AssignmentSubmission.objects.filter(assignment=assignment)
        serializer = AssignmentSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def assignment_overview(self, request):
        """
        Custom action to retrieve all assignments with student count, handed-in count, and submissions.
        URL: /api/elearning/assignments/assignment_overview/
        Method: GET
        """
        if request.user.role not in ['Instructor', 'Administrator']:
            raise PermissionDenied("Only instructors and administrators can access this view.")
        
        assignments = Assignment.objects.annotate(
            total_students=Count('course__enrollment', distinct=True),
            handed_in=Count('assignmentsubmission', distinct=True),
            pending_submissions=Count('assignmentsubmission', 
                                      filter=Q(assignmentsubmission__status="pending"),
                                      distinct=True)
        ).prefetch_related(
            'assignmentsubmission_set__student__user'
        )

        assignments_data = []
        for assignment in assignments:
            submissions_data = [
                self.get_submission_data(submission)
                for submission in assignment.assignmentsubmission_set.all()
            ]

            assignments_data.append({
                "id": assignment.id,
                "title": assignment.title,
                "dueDate": assignment.due_date.strftime("%d %b, %H:%M"),
                "postedDate": assignment.posted_date.strftime("%d %b"),
                "students": assignment.total_students,
                "handedIn": assignment.handed_in,
                "module": assignment.module.id if assignment.module else None,
                "assignment_file_url": self.get_file_url(assignment.file),
                "total_pending_submissions": assignment.pending_submissions,
                "submissions": submissions_data
            })

        return Response(assignments_data)

    def get_submission_data(self, submission : AssignmentSubmission):
        return {
            "fullname": submission.student.user.get_username(),
            "date_handed": submission.submitted_date.strftime("%d %b, %H:%M"),
            "marks": submission.marks if submission.marks is not None else "",
            "comments": submission.private_comment or "",
            "status": submission.status,
            "submission_file_url": self.get_file_url(submission.file)
        }

    def get_file_url(self, file):
        return self.request.build_absolute_uri(file.url) if file else ''

class UserProgressView(APIView):
    """
    View to list all users and their progress or retrieve progress for a specific user.
    """

    def get(self, request, user_id=None):
        if user_id is None:
            # If user_id is not provided, return all users with their progress
            user_progress = UserProgress.objects.all()
            serialized_progress = UserProgressSerializer(user_progress, many=True)
            return Response(serialized_progress.data)
        else:
            # Retrieve progress for a specific user by user_id
            user = get_object_or_404(User, id=user_id)  # Replace User with your actual User model
            user_progress = UserProgress.objects.filter(user=user)
            serialized_progress = UserProgressSerializer(user_progress, many=True)
            return Response(serialized_progress.data)

class AnalyticsDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = self.get_user_data(user)
        data['live_classes'] = self.get_live_classes(user)
        return Response(data, status=status.HTTP_200_OK)

    def get_user_data(self, user: User):
        data = {'user': user.username, 'last_login': user.last_login}
        role_data_methods = {
            "Student": self.get_student_data,
            "Administrator": self.get_admin_data,
            "Instructor": self.get_instructor_data
        }
        role_data = role_data_methods.get(user.role, lambda x: {})(user)
        data.update(role_data)

        # Add live classes data for all roles
        data['live_classes'] = self.get_live_classes(user)

        # Add next live class for students
        if user.role == "Student":
            course_enrolled = role_data.get('course_enrolled')
            if course_enrolled:
                next_class = self.get_next_live_class(course_enrolled['id'])
                if next_class:
                    data['next_live_class'] = self.format_next_class_data(next_class)

        return data

    def get_live_classes(self, user : User):
        queryset = self.get_live_classes_queryset(user)
        for schedule in queryset:
            schedule.next_class_time = schedule.next_occurrence()
        sorted_queryset = sorted(queryset, key=lambda x: x.next_class_time)
        return LiveClassScheduleSerializer(sorted_queryset, many=True).data

    def get_live_classes_queryset(self, user : User):
        if user.role == 'Administrator':
            return LiveClassSchedule.objects.filter(is_active=True)
        elif user.role == 'Instructor':
            return LiveClassSchedule.objects.filter(instructor=user, is_active=True)
        else:  # Student
            student = Student.objects.get(user=user)
            enrolled_courses = Course.objects.filter(enrollment__student=student)
            return LiveClassSchedule.objects.filter(course__in=enrolled_courses, is_active=True)

    def get_student_data(self, user: User):
        try:
            student = Student.objects.get(user=user)
            enrollment = self.get_enrollment(student, user)
            course = enrollment.course
            return self.get_course_data(user, course, student)
        except Enrollment.DoesNotExist:
            return self.get_default_student_data()

    def get_enrollment(self, student : Student, user: User):
        return Enrollment.objects.select_related('course').prefetch_related(
            Prefetch('course__modules',
                     queryset=CourseModule.objects.prefetch_related(
                         Prefetch('moduleprogress_set',
                                  queryset=ModuleProgress.objects.filter(user=user),
                                  to_attr='user_progress')
                     ))
        ).get(student=student)

    def get_course_data(self, user: User, course : Course, student : Student):
        course_data = CourseSerializer(course).data
        course_data.update(self.get_course_profile(course))
        course_data['modules'] = self.get_modules_data(user, course)
        course_data['lesson_progress'] = self.get_lesson_progress(user, course)

        return {
            'total_time_spent': self.get_time_spent_data(user, course),
            'course_completion_rate': self.get_completion_rate_data(user, course),
            'course_enrolled': course_data,
            'total_assignments': Assignment.objects.filter(course=course).count(),
            'completed_assignments': AssignmentSubmission.objects.filter(student=student).count(),
            'average_module_progress': self.get_average_module_progress(user, course),
            'monthly_progress': get_monthly_progress(user, course),
            'submission_stats': self.get_submission_stats_by_month(user),
        }

    def get_time_spent_data(self, user: User, course : Course):
        return {
            'value': calculate_time_spent(user, course),
            'change': f"{get_weekly_change(user, course, calculate_time_spent):+.1f}% this week"
        }

    def get_completion_rate_data(self, user : User, course : Course):
        return {
            'value': calculate_course_progress(user, course, end_date=datetime.now()),
            'change': f"{get_weekly_change(user, course, calculate_course_progress):+.1f}% this week"
        }

    def get_average_module_progress(self, user : User, course : Course):
        module_progresses = ModuleProgress.objects.filter(user=user, module__course=course).values_list('progress', flat=True)
        return mean(module_progresses) if module_progresses else 0

    def get_course_profile(self, course : User):
        course_profile = CourseProfile.objects.filter(course=course).first()
        if course_profile:
            return {
                'icon': course_profile.icon.url if course_profile.icon else None,
                'body': course_profile.body
            }
        return {}

    def get_modules_data(self, user : User, course : Course):
        modules = course.modules.all()
        return [{
            **CourseModuleSerializer(module).data,
            'progress': ModuleProgressSerializer(ModuleProgress.objects.filter(user=user, module=module).first()).data
        } for module in modules]

    def get_lesson_progress(self, user : User, course : Course):
        return LessonProgress.objects.filter(
            user=user,
            lesson__module__course=course
        ).aggregate(
            total_lessons=Count('id'),
            completed_lessons=Count('id', filter=Q(completed=True))
        )

    def get_default_student_data(self):
        return {
            'total_time_spent': {'value': 0, 'change': "0.0% this week"},
            'course_completion_rate': {'value': 0, 'change': "0.0% this week"},
            'course_enrolled': None,
            'total_assignments': 0,
            'completed_assignments': 0,
            'average_module_progress': 0,
            'monthly_progress': []
        }

    def get_admin_data(self, user : User):
        courses = Course.objects.annotate(enrollment_count=Count('enrollment')).order_by('-enrollment_count')
        students = get_user_model().objects.filter(role="Student")
        instructors = get_user_model().objects.filter(role="Instructor")
        lesson_assignments = LessonAssignment.objects.all()
        module_assignments = ModuleAssignment.objects.all()

        return {
            'courses': self.annotate_submission_counts(CourseSerializer(courses, many=True).data, courses),
            'lesson_assignments': self.annotate_lesson_submissions(LessonAssignmentSerializer(lesson_assignments, many=True).data),
            'module_assignments': ModuleAssignmentSerializer(module_assignments, many=True).data,
            'students': self.serialize_users(students),
            'instructors': self.serialize_users(instructors),
            'submission_stats': self.get_submission_stats_by_month(user),
        }

    def get_instructor_data(self, user : User):
        instructor = Instructor.objects.get(user=user)
        courses = Course.objects.filter(instructor=instructor)
        courses_data = self.annotate_submission_counts(CourseSerializer(courses, many=True).data, courses)

        total_students = sum(Enrollment.objects.filter(course_id=course['id']).count() for course in courses_data)
        total_submissions = sum(self.get_course_submission_count(Course.objects.get(id=course['id'])) for course in courses_data)

        return {
            'Total Students': total_students,
            'Course_count': courses.count(),
            'Total Submissions': total_submissions,
            'courses': courses_data,
        }

    def annotate_submission_counts(self, courses_data, courses):
        for course in courses_data:
            course_obj = courses.get(id=course['id'])
            course['submission_count'] = self.get_course_submission_count(course_obj)
            course['enrollment_count'] = Enrollment.objects.filter(course_id=course['id']).count()
        return courses_data

    def get_course_submission_count(self, course : Course):
        assignments = Assignment.objects.filter(course=course)
        return sum(AssignmentSubmission.objects.filter(assignment=assignment).count() for assignment in assignments)

    def annotate_lesson_submissions(self, lesson_assignments_data):
        for assignment in lesson_assignments_data:
            assignment['submission_count'] = AssignmentSubmission.objects.filter(assignment_id=assignment['id']).count()
        return lesson_assignments_data

    def serialize_users(self, users):
        return [{'username': user.username, 'email': user.email} for user in users]

    def get_next_live_class(self, course):
        if course:
            now = timezone.localtime()
            return LiveClassSchedule.objects.filter(
                course=course,
                is_active=True
            ).annotate(
                next_time=ExpressionWrapper(
                    Case(
                        When(start_time__gt=now.time(), then=F('start_time')),
                        default=ExpressionWrapper(F('start_time'), output_field=TimeField())
                    ),
                    output_field=TimeField()
                )
            ).order_by('next_time').first()
        return None

    def format_next_class_data(self, next_class : LiveClassSchedule):
        return {
            'title': next_class.title,
            'course': next_class.course.name,
            'time': next_class.next_occurrence(),
            'room': next_class.room
        }

    def get_submission_stats_by_month(self, user):
        submission_stats = self.get_filtered_submission_stats(user)
        current_year, previous_year = datetime.now().year, datetime.now().year - 1
        chart_data = self.aggregate_submission_stats(submission_stats, current_year, previous_year)
        return self.format_chart_data(chart_data, current_year, previous_year)

    def get_filtered_submission_stats(self, user):
        submission_stats = AssignmentSubmission.objects.all()
        if user.role == 'Student':
            student = Student.objects.get(user=user)
            return submission_stats.filter(student=student)
        elif user.role == 'Instructor':
            instructor = Instructor.objects.get(user=user)
            return submission_stats.filter(assignment__course__instructor=instructor)
        elif user.role != 'Administrator':
            return submission_stats.none()
        return submission_stats

    def aggregate_submission_stats(self, submission_stats, current_year, previous_year):
        aggregated_stats = submission_stats.filter(submitted_date__year__in=[previous_year, current_year]).annotate(
            month=TruncMonth('submitted_date'),
            year=TruncYear('submitted_date')
        ).values('year', 'month').annotate(submission_count=Count('id')).order_by('year', 'month')

        chart_data = {year: [0] * 12 for year in [previous_year, current_year]}
        for stat in aggregated_stats:
            chart_data[stat['year'].year][stat['month'].month - 1] = stat['submission_count']
        return chart_data

    def format_chart_data(self, chart_data, current_year, previous_year):
        return [
            {"label": str(previous_year), "data": chart_data[previous_year]},
            {"label": str(current_year), "data": chart_data[current_year][:datetime.now().month]}
        ]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_enrolled_course(request):
    # Check if the user is a student
    if not hasattr(request.user, 'role') or request.user.role != 'Student':
        return Response({"detail": "Access denied. Only students can access this resource."}, status=status.HTTP_403_FORBIDDEN)

    # Get the enrollment object
    enrollment = get_object_or_404(Enrollment, user=request.user)
    course = enrollment.course
    course_completion = calculate_course_progress(request.user, course, end_date=datetime.now())
    serializer = CourseSerializer(course, context={'user': request.user})
    complition= {
        "progress" : course_completion
    }
    data = serializer.data
    data.update(complition)
    return Response(data, status=status.HTTP_200_OK)

class ElearningTransactionViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=['get'], url_path='student-data')
    def student_data(self, request):
        user=request.user
        service_type = request.query_params.get('service_type', 'course')
        if not user.is_staff:
            data = PaymentUtils.get_student_data(user, service_type)
            serializer = TransactionSerializer(data['transactions'], many=True)
            return Response({
                'summary': data['summary'],
                'transactions': serializer.data
            }, status.HTTP_200_OK)
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='admin-data')
    def admin_data(self, request):
        if request.user.is_staff:
            service_type = request.query_params.get('service_type', 'COURSE')
            data = PaymentUtils.get_admin_data(service_type=service_type)
            serializer = TransactionSerializer(data['transactions'], many=True)
            return Response({
                'summary': data['summary'],
                'transactions': serializer.data
            }, status.HTTP_200_OK)
        return Response({'detail': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

class InviteUserViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def validate_and_create_user(
        self, email : str, username : str, role : str, 
        request_user : User, course : Course, send_email=True
    ):
        if not email and not username:
            return {"error": "Email or Username is required"}, status.HTTP_400_BAD_REQUEST

        # Validate email format
        try:
            validator = EmailValidator()
            validator(email)
        except ValidationError:
            return {"error": "Invalid email format"}, status.HTTP_400_BAD_REQUEST

        # Check if the user already exists
        if User.objects.filter(Q(email=email) | Q(username=username)).exists():
            return {"error": "User with this email or username already exists"}, status.HTTP_400_BAD_REQUEST

        # Create the user
        password = generate_password(8)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )

        if role == "Instructor":
            instructor = Instructor.objects.create(user=user)
            course.instructor = instructor
            course.save()
        elif role == "Student":
            student = Student.objects.create(user=user)
            Enrollment.objects.create(student=student, course = course)

        if send_email:
            send_invitation_emails(request_user, email, password, username, student=(role == "Student"))

        return {"status": "success"}, status.HTTP_201_CREATED

    def post(self, request, role):
        """
        Handle POST requests to invite either Instructors or Students based on the role passed.
        """
        email = request.data.get('email')
        username = request.data.get('username')
        course_id = request.data.get('course_id')
        
        course = Course.objects.get(pk=course_id)

        if role == "Student" and request.user.role == "Student":
            return Response({"error": "Method not allowed for students"}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate and create user
        response, status_code = self.validate_and_create_user(
            email=email,
            username=username,
            role=role,
            request_user=request.user,
            course = course
        )
        return Response(response, status=status_code)

class InviteInstructorViewSet(InviteUserViewSet):
    permission_classes = [IsAdminUser]

    def post(self, request):
        return super().post(request, role="Instructor")

class InviteStudentViewSet(InviteUserViewSet):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return super().post(request, role="Student")
