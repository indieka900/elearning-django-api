from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import(
    AssignmentViewSet, CourseModuleViewSet, CourseViewSet, CourseProfileViewSet, 
    EnrollmentViewSet, LessonAssignmentViewSet, LessonProgressViewSet, 
    LessonViewSet, LiveClassScheduleViewSet, ModuleAssignmentViewSet, 
    ModuleProgressViewSet, AnalyticsDashboard, UserProgressView, SubscriptionPlanViewSet, get_enrolled_course,
    ElearningTransactionViewSet, InviteInstructorViewSet, InviteStudentViewSet, SubmissionViewSet
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'live-classes', LiveClassScheduleViewSet)
router.register(r'course-profiles', CourseProfileViewSet)
router.register(r'course-modules', CourseModuleViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'module-progress', ModuleProgressViewSet)
router.register(r'lesson-progress', LessonProgressViewSet)
router.register(r'module-assignments', ModuleAssignmentViewSet)
router.register(r'lesson-assignments', LessonAssignmentViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'submissions', SubmissionViewSet)

router.register(r'subscription-plans', SubscriptionPlanViewSet)
router.register(r'transactions', ElearningTransactionViewSet, basename='transactions')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics-dashboard/', AnalyticsDashboard.as_view(), name='analytics-dashboard'),
    path('invite-instructor/', InviteInstructorViewSet.as_view(), name='invite-instractor'),
    path('invite-student/', InviteStudentViewSet.as_view(), name='invite-student'),
    path('enrolled-course/', get_enrolled_course ),
    path('user-progress/<int:user_id>/', UserProgressView.as_view(), name='user-progress'),
    path('user-progress/', UserProgressView.as_view(), name='user-progress')

]
