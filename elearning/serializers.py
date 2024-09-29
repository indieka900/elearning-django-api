from urllib.parse import urljoin
from django.conf import settings
from rest_framework import serializers
from .models import (
    Assignment,
    AssignmentSubmission,
    Course,
    CourseProfile,
    CourseModule,
    SubscriptionPlan,
    Enrollment,
    Lesson,
    LessonAssignment,
    LessonProgress,
    LiveClassSchedule,
    ModuleAssignment,
    ModuleProgress,
    UserProgress,
)

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = CourseModule
        fields = ['id', 'title', 'description', 'objectives', 'lessons']
class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'description','duration', 'modules']
class CourseSerializer_(serializers.ModelSerializer):
    enrollment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'description', 'enrollment_count']
class Assignment_SubmissionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source = 'assignment.title')
    posted_date = serializers.CharField(source = 'assignment.posted_date')
    due_date = serializers.CharField(source = 'assignment.due_date')
    score = serializers.CharField(source = 'marks')

    class Meta:
        model = AssignmentSubmission
        # fields = '__all__'
        exclude = ['content', 'assignment', 'student','file']
        
        
class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    submission_file_url = serializers.SerializerMethodField()
    assignment = serializers.CharField(source = 'assignment.title')
    class Meta:
        model = AssignmentSubmission
        fields = "__all__"
        read_only_fields = ['student', 'assignment', 'status',]
        
    def get_submission_file_url(self, obj):
        if obj.file:
            return urljoin(settings.MEDIA_URL, obj.file.name)
        return ''
class AssignmentSerializer(serializers.ModelSerializer):
    handedIn = serializers.SerializerMethodField()
    submissions = AssignmentSubmissionSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'due_date', 'posted_date', 'handedIn', 'module', 'submissions', 'course', 'points', 'link', 'file']

    def get_handedIn(self, obj):
        return AssignmentSubmission.objects.filter(assignment=obj).count()

    # def get_students(self, obj):
    #     return obj.course.students.count()  # Assuming `course` has a related `students` field

    
class StudentAssignmentSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(source = 'instructor.user.username')

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description','instructor' , 'due_date', 'posted_date', 'course', 'module', 'points', 'link', 'file']

class CourseProfileSerializer(serializers.ModelSerializer):
    """Serializer for course profile model."""

    class Meta:
        model = CourseProfile
        fields = "__all__"



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'course', 'display_price', 'upfront', 'two_months', 'three_months']

        


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'code', 'name', 'description', 'duration', 'instructor_name', 'modules']

    def get_instructor_name(self, obj : Course):
        return obj.instructor.user.username if obj.instructor else None
        
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrollment_date','progress','status']

class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleProgress
        fields = ['progress','module']


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = '__all__'

class ModuleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleAssignment
        fields = '__all__'

class LessonAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonAssignment
        fields = '__all__'

class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = '__all__' 


class LiveClassScheduleSerializer(serializers.ModelSerializer):
    next_class_time = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = LiveClassSchedule
        fields = ['id', 'course', 'course_name', 'instructor', 'title', 'description','date', 'start_time', 'duration', 'room', 'is_active', 'next_class_time']
        read_only_fields = ['instructor', 'course_name']

    def get_next_class_time(self, obj):
        return obj.next_occurrence()
    
class AssignmentMarkingSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()
    marks = serializers.IntegerField(min_value=0)
    private_comment = serializers.CharField(allow_blank=True)