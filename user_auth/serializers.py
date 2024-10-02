import time
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

from elearning.send_mails import send_registration_emails
from elearning.utils import calculate_time_spent
from .models import CustomUser,Administrator,Instructor,Student
from elearning.models import Course, Enrollment
import logging
from .utils import OTPManager
from payments.models import Payment, PreSignup
User = CustomUser

#signup
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, handling serialization and deserialization of user data.
    """
    class Meta:
        model = User
        fields = ('username', 'email','password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Creates a new user with the validated data.
        :param validated_data: Dictionary containing the validated data.
        :return: The created user instance.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        student = Student.objects.create(user=user)
        student.save()
        # send mail
        send_registration_emails(user)

        """ Get pre-signup object and update the user field in payment model using payment_id """
        pre_signup = PreSignup.objects.filter(email=user.email).first()
        if pre_signup:
            payment = Payment.objects.get(id=pre_signup.payment_id.pk)
            payment.user = user
            payment.save()

            if payment.status == 'SUCCESS':
                """ Get service and service id from payment model and enroll user to the course """
                if payment.service_type == 'course':
                    course = Course.objects.get(id=payment.service_id)
                    enrollment = Enrollment(user=user, course=course)
                    enrollment.save()
                    pre_signup.delete()
                    return user
                

        return user
    
#login  
class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login, handling authentication of user credentials.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Validates the provided email and password.
        
        :param data: Dictionary containing 'email' and 'password' keys.
        :return: The authenticated user if credentials are valid and user is active.
        :raises serializers.ValidationError: If the credentials are invalid or the user is inactive.
        """
        email = data.get('email')
        password = data.get('password')
        user = authenticate(email=email, password=password)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

class TokenSerializer(serializers.Serializer):
    """
    Serializer for handling JWT tokens.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()
    user_role = serializers.CharField()
    
#OTP
class SendOTPSerializer(serializers.Serializer):
    # Email field to input and validate the user's email address
    email = serializers.EmailField()

    def validate_email(self, value):
        """
        Validates that the email exists in the User model.
        
        :param value: The email address to validate.
        :return: The validated email address.
        :raises serializers.ValidationError: If the email does not exist in the User model.
        """
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist")
        return value

    def send_otp(self):
        """
        Sends an OTP to the validated email address.
        
        1. Retrieves the email from the validated data.
        2. Generates a TOTP (Time-based One-Time Password) token for the user.
        3. Sends an email with the OTP code to the user's email address.
        4. Caches the OTP token with the email as the key and a timeout of 300 seconds (5 minutes).
        """
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        otp_token = user.generate_totp_token()
        
        send_mail(
            'Your OTP Code',
            f'Your OTP code is {otp_token}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        cache.set(email, otp_token, timeout=300)
 
class VerifyOTPSerializer(serializers.Serializer):
    # Email field to input and validate the user's email address
    email = serializers.EmailField()

    # OTP field to input and validate the OTP code
    otp = serializers.CharField()

    def validate(self, data):
        """
        Validates the provided email and OTP code.
        
        :param data: Dictionary containing 'email' and 'otp' keys.
        :return: Dictionary containing the validated user.
        :raises serializers.ValidationError: If the email does not exist or the OTP is invalid.
        """
        email = data.get('email')
        otp = data.get('otp')
        otp = int(otp)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")
        

        if not OTPManager.verify_otp(user, otp):
            raise serializers.ValidationError("Invalid OTP")

        return {'user': user}

logger = logging.getLogger(__name__)

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("This email address is not associated with any account.")
        return value

    def save(self):
        request = self.context.get('request')
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        password_reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        try:
            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n{password_reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                fail_silently=False,
            )
            logger.info(f'Password reset email sent to {email}')
        except Exception as e:
            logger.error(f'Error sending password reset email: {str(e)}')
            raise serializers.ValidationError('Failed to send password reset email. Please try again later.')

class UserUpdateSerializer(serializers.Serializer):
    course = serializers.CharField(max_length=100)
    paymentPlan = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100, required=False)
    firstName = serializers.CharField(max_length=30)
    lastName = serializers.CharField(max_length=30)
    city = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    streetaddress = serializers.CharField(max_length=255)
    phoneNumber = serializers.CharField(max_length=15)
    country = serializers.CharField(max_length=100)
    consent = serializers.BooleanField()
    agree = serializers.BooleanField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def update(self, instance : CustomUser, validated_data):
        instance.first_name = validated_data.get('firstName', instance.first_name)
        instance.last_name = validated_data.get('lastName', instance.last_name)
        # instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phoneNumber', instance.phone_number)
        instance.save()

        # Update or create Student profile
        student_profile, created = Student.objects.get_or_create(user=instance)
        student_profile.country = validated_data.get('country', student_profile.country)
        student_profile.city = validated_data.get('city', student_profile.city)
        student_profile.street_address = validated_data.get('streetaddress', student_profile.street_address)
        student_profile.payment_plan = validated_data.get('paymentPlan', student_profile.payment_plan)
        student_profile.course = validated_data.get('course', student_profile.course)
        student_profile.save()

        return instance

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate_uid(self, value):
        try:
            user_id = urlsafe_base64_decode(value).decode()
            User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError('Invalid token')
        return value

    def validate(self, data):
        uid = data.get('uid')
        token = data.get('token')
        new_password = data.get('new_password')
        
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError('Invalid token')

        if user.check_password(new_password):
            raise serializers.ValidationError('The new password can not be the same as the old password.')

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['name', 'duration'] 
        
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username",'first_name', 'last_name', 'email', 'phone_number', 'last_login']
        read_only_fields = ["last_login", "username", "email"]
        
    def update(self, instance, validated_data):
        if 'email' in validated_data:
            raise serializers.ValidationError({"email": "You cannot update the email address."})
        if 'username' in validated_data:
            raise serializers.ValidationError({"username": "You cannot update the username."})
        
        return super().update(instance, validated_data)

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Student  # This serves as a base model for fields
        fields = ['user', 'course', 'country', 'city', 'street_address']
        # Add common fields here

class AdministratorProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    class Meta:
        model = Administrator
        fields = ['user', 'country', 'city', 'street_address', 'profile_picture']
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_serializer = CustomUserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()
        return super().update(instance, validated_data)

class StudentProfileSerializer(serializers.ModelSerializer):
    
    user = CustomUserSerializer()
    course = serializers.SerializerMethodField()
    total_hours_spent = serializers.SerializerMethodField()
    class Meta:
        model = Student
        fields = [
            'user', 'country', 'city', 'street_address', 
            'profile_picture', 'payment_plan','total_hours_spent', 'course'
        ]
        read_only_fields = ["total_hours_spent", "payment_plan", "course"]
       
    def get_total_hours_spent(self, obj):
        student = Student.objects.get(user=obj.user)
        enrollment = Enrollment.objects.filter(student=student).first()
        if enrollment:
            total_seconds = calculate_time_spent(obj.user, enrollment.course)
            total_hours = total_seconds / 3600  # Convert seconds to hours
            return round(total_hours, 2)  # Round to 2 decimal places
        return 0
        
    def get_course(self, obj):
        student = Student.objects.get(user=obj.user)
        enrollment = Enrollment.objects.filter(student=student).first()
        if student.course != enrollment.course.name:
            student.course = enrollment.course.name
            student.save()
        if enrollment:
            return enrollment.course.name
        return None
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_serializer = CustomUserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()
        return super().update(instance, validated_data)

class InstructorProfileSerializer(serializers.ModelSerializer):
    
    user = CustomUserSerializer()
    class Meta:
        model = Instructor
        fields = ['user', 'country', 'city', 'street_address', 'profile_picture']
        
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user_serializer = CustomUserSerializer(instance.user, data=user_data, partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()
        return super().update(instance, validated_data)

       
class StudentSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField() 
    email = serializers.EmailField(source='user.email') 
    status = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    last_active = serializers.DateTimeField(source='user.last_login')

    class Meta:
        model = Student
        fields = ['email', 'username', 'course', 'status',"user_id" ,'last_active']

    def get_username(self, obj):
        return obj.user.username
    
    def get_status(self, obj):
        return obj.user.is_active
    
    def get_user_id(self, obj):
        return obj.user.id
    
    def get_course(self, obj):
        enrollment = Enrollment.objects.filter(student=obj).first()
        if enrollment:
            return enrollment.course.name
        return None

class InstructorSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField() 
    email = serializers.EmailField(source='user.email') 
    status = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    last_active = serializers.DateTimeField(source='user.last_login')

    class Meta:
        model = Instructor
        fields = ['email', 'username', 'course', 'status','user_id', 'last_active']

    def get_username(self, obj):
        return obj.user.username
    
    def get_user_id(self, obj):
        return obj.user.id
    
    def get_status(self, obj):
        return obj.user.is_active
    
    def get_course(self, obj):
        course = Course.objects.filter(instructor=obj).first()
        if course:
            return course.name
        return None

