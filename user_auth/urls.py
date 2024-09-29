from django.urls import path, include
from user_auth.views import (
    SignUpView, UserLoginView, PasswordResetView, PasswordResetConfirmView, 
    VerifyOTPView,UserProfileView, StudentManagementView,
    InstructorManagementView, TotalStudentsView, TotalInstructorsView
)



urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('password_reset/', include('django_rest_passwordreset.urls')),
    # path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('total-students/', TotalStudentsView.as_view(), name='total-students'),
    path('total-instructors/', TotalInstructorsView.as_view(), name='total-instructors'),
    path('students/<int:student_id>/', StudentManagementView.as_view(), name='student-management'),
    path('instructors/<int:instructor_id>/', InstructorManagementView.as_view(), name='instructor-management'),
]