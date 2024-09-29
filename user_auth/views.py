from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import login
from rest_framework.permissions import AllowAny
from django.db import transaction
from elearning.email_backend import send_email
from .serializers import UserSerializer
#login
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserLoginSerializer, TokenSerializer
#change_password
from rest_framework import generics, status
from .serializers import PasswordResetSerializer, PasswordResetConfirmSerializer
#OTP
from .serializers import InstructorSerializer
from .serializers import StudentSerializer
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .models import CustomUser as User
from .utils import OTPManager 
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import Student, Administrator, Instructor
from .serializers import StudentProfileSerializer, AdministratorProfileSerializer, InstructorProfileSerializer
from rest_framework.exceptions import NotFound
from django.shortcuts import get_object_or_404

class SignUpView(generics.CreateAPIView):
    """
    API view for user sign-up. Allows any user to create a new account.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
   
#login
class UserLoginView(generics.GenericAPIView):
    
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for user login.
        
        :param request: The HTTP request containing login data.
        :return: HTTP response with a success message or error details.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data  

        # Generate and Send OTP
        otp = OTPManager.generate_otp(user)
        
        mail = send_email(
            subject='Your OTP Code',
            message=f'Your OTP code is {otp}',
            recipient_list=[user.email],
            use_accounts_backend=True
        )
        
        mail.send()



        return Response({'detail': 'OTP sent to your email'}, status=status.HTTP_200_OK)

#change_password

class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password reset email sent'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset'}, status=status.HTTP_200_OK)

#OTP
class SendOTPView(generics.GenericAPIView):
     serializer_class = SendOTPSerializer

     def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send_otp()
        return Response({"detail": "OTP sent"}, status=status.HTTP_200_OK)

class VerifyOTPView(generics.GenericAPIView):
    """
    API view for verifying OTP. Validates the OTP and generates JWT tokens for the user.
    """
    serializer_class = VerifyOTPSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        """
        Handle POST request for OTP verification.
        
        :param request: The HTTP request containing OTP verification data.
        :return: HTTP response with generated JWT tokens or error details.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        token_data = {
            'refresh': str(refresh),
            'access': str(access),
            'user_role': user.role,
        }
        token_serializer = TokenSerializer(token_data)

        return Response(token_serializer.data, status=status.HTTP_200_OK)
    
class UserProfileView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.role == 'Administrator':
            return AdministratorProfileSerializer
        elif user.role == 'Student':
            return StudentProfileSerializer
        elif user.role == 'Instructor':
            return InstructorProfileSerializer
        return None

    def get_profile(self):
        user = self.request.user
        try:
            if user.role == 'Administrator':
                return user.administrator_profile
            elif user.role == 'Student':
                return user.student_profile
            elif user.role == 'Instructor':
                return user.instructor_profile
        except (Administrator.DoesNotExist, Student.DoesNotExist, Instructor.DoesNotExist):
            raise NotFound(detail="Profile not found for the current user.")
        return None

    def get(self, request, *args, **kwargs):
        profile = self.get_profile()
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            return Response({"detail": "Invalid role"}, status=400)
        
        serializer = serializer_class(profile, context={'request': request})
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        profile = self.get_profile()
        serializer_class = self.get_serializer_class()
        if serializer_class is None:
            return Response({"detail": "Invalid role"}, status=400)
        
        serializer = serializer_class(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TotalStudentsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        total_students = Student.objects.count()
        active_students = Student.objects.filter(user__is_active=True).count()
        
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        data = {
            'total_students': total_students,
            'active_students': active_students,
            'students_details': serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)
class TotalInstructorsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        total_instructors = Instructor.objects.count()
        active_instructors = Instructor.objects.filter(user__is_active=True).count()
        
        instructors = Instructor.objects.all()
        serializer = InstructorSerializer(instructors, many=True)
        
        data = {
            'total_instructors': total_instructors,
            'active_instructors': active_instructors,
            'instructors_details': serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
    
class UserManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def check_admin_permission(self, user):
        if user.role != "Administrator":
            raise PermissionError("Permission denied")

    def get_user_profile(self, user_id, user_type):
        user = get_object_or_404(User, id=user_id)
        if user_type == 'student':
            return get_object_or_404(Student, user=user)
        elif user_type == 'instructor':
            return get_object_or_404(Instructor, user=user)
        else:
            raise ValueError("Invalid user type")

    @transaction.atomic
    def perform_action(self, request, user_id, user_type, action):
        try:
            self.check_admin_permission(request.user)
            user_profile = self.get_user_profile(user_id, user_type)
            user = user_profile.user
            
            if action == 'suspend':
                user.is_active = False
                message = f"{user_type.capitalize()} {user.username} has been suspended"
            elif action == 'restore':
                user.is_active = True
                message = f"{user_type.capitalize()} {user.username} has been restored"
            elif action == 'remove':
                username = user.username
                user.delete()
                return Response({"message": f"{user_type.capitalize()} {username} has been removed"}, status=status.HTTP_200_OK)
            elif action == 'change_role':
                new_role = request.data.get('new_role')
                if new_role not in [choice[0] for choice in User.Role_choices]:
                    return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
                
                user_profile.delete()
                
                if new_role == "Student":
                    Student.objects.create(user=user)
                elif new_role == "Instructor":
                    Instructor.objects.create(user=user)
                elif new_role == "Administrator":
                    Administrator.objects.create(user=user)
                
                user.role = new_role
                user.is_superuser = (new_role == "Administrator")
                user.is_staff = (new_role == "Administrator")
                message = f"User {user.username} role changed to {new_role}"
            
            user.save()
            return Response({"message": message}, status=status.HTTP_200_OK)
        
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentManagementView(UserManagementView):
    def patch(self, request, student_id):
        action = request.data.get('action')
        return self.perform_action(request, student_id, 'student', action)

    def delete(self, request, student_id):
        return self.perform_action(request, student_id, 'student', 'remove')

class InstructorManagementView(UserManagementView):
    def patch(self, request, instructor_id):
        action = request.data.get('action')
        return self.perform_action(request, instructor_id, 'instructor', action)

    def delete(self, request, instructor_id):
        return self.perform_action(request, instructor_id, 'instructor', 'remove')