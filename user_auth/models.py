from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.auth.validators import UnicodeUsernameValidator
from django_otp.oath import TOTP
from django_otp.util import random_hex
import time
from django.conf import settings
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", 'Administrator')
        return self.create_user(email, password, **extra_fields)
class CustomUser(AbstractBaseUser, PermissionsMixin):
    Role_choices = (
        ("Administrator", "Administrator"),
        ("Student", "Student"),
        ("Instructor", "Instructor")
    )
    
    username_validator = UnicodeUsernameValidator()
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = models.CharField(max_length=15, default='')
    role = models.CharField(max_length=25, choices=Role_choices, default="Student")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    secret = models.CharField(max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = random_hex(20)
        super().save(*args, **kwargs)

    def generate_totp_token(self):
        totp = TOTP(key=self.otp_secret, digits=6)  # Adjust interval to match the one used in OTPManager
        return totp.token()

    
    def verify_totp_token(self, token):
        totp = TOTP(key=self.otp_secret, digits=6)  # Adjust interval to match the one used in OTPManager
        return totp.verify(token)


class Profile(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE, unique=True,related_name='%(class)s_profile')
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile",default="default.png")
    
    class Meta:
        abstract= True  
            
class Administrator(Profile):
    pass
    @transaction.atomic
    def save(self, *args, **kwargs):
        '''if self.user.role != "Student":
            raise ValidationError("Only users with the 'Student' role can be saved as students.")'''
        
        # Check if the user is already an Student or Instructor
        student_profile = Student.objects.filter(user=self.user).first()
        instructor_profile = Instructor.objects.filter(user=self.user).first()
        
        if student_profile:
            # If the user is an Student, delete the Student profile
            student_profile.delete()
            # Update the user's role
            self.user.role = "Administrator"
            self.user.is_superuser = True
            self.user.is_staff = True
            self.user.save()
        elif instructor_profile:
            # If the user is an Instructor, delete the Instructor profile
            instructor_profile.delete()
            # Update the user's role
            self.user.role = "Administrator"
            self.user.is_superuser = True
            self.user.is_staff = True
            self.user.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.user.email

 # Adjust the import based on your actual structure

class Student(Profile):
    is_active = models.BooleanField(default=True) 
    payment_plan = models.CharField(max_length=100, blank=True, null=True)
    course = models.CharField(max_length=100,blank=True, null=True)
    last_active = models.DateTimeField(auto_now=True, blank=True, null=True)
    @property
    def get_course_duration(self):
        return self.course.duration

    @transaction.atomic
    def save(self, *args, **kwargs):
        admin_profile = Administrator.objects.filter(user=self.user).first()
        instructor_profile = Instructor.objects.filter(user=self.user).first()
        
        if admin_profile:
            # If the user is an Administrator, delete the Administrator profile
            admin_profile.delete()
            # Update the user
            self.user.role = "Student"
            self.user.is_superuser = False
            self.user.is_staff = False
            self.user.save()
        elif instructor_profile:
            # If the user is an Instructor, delete the Instructor profile
            instructor_profile.delete()
            # Update the user
            self.user.role = "Student"
            self.user.is_superuser = False
            self.user.is_staff = False
            self.user.save()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.user.email
    
class Instructor(Profile):
    course = models.CharField(max_length=100,blank=True, null=True) 
    pass

    @transaction.atomic
    def save(self, *args, **kwargs):
        '''if self.user.role != "Student":
            raise ValidationError("Only users with the 'Student' role can be saved as students.")'''
        
        admin_profile = Administrator.objects.filter(user=self.user).first()
        student_profile = Student.objects.filter(user=self.user).first()
        
        if admin_profile:
            admin_profile.delete()
            # Update the user
            self.user.role = "Instructor"
            self.user.is_superuser = False
            self.user.is_staff = False
            self.user.save()
        elif student_profile:
            student_profile.delete()
            self.user.role = "Instructor"
            self.user.is_superuser = False
            self.user.is_staff = False
            self.user.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email

class DeviceLogin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_identifier = models.CharField(max_length=255)
    device_type = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=50)
    login_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Device Login'
        verbose_name_plural = 'Device Logins'


class KnownDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device = models.CharField(max_length=255)
    os = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=45, default='0.0.0.0')
    browser = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user} - {self.device} - {self.os} - {self.browser}"

    @staticmethod
    def is_new_device(user, device, os, browser):
        return not KnownDevice.objects.filter(user=user, device=device, os=os, browser=browser).exists()


admin_models = [
    DeviceLogin,
    KnownDevice,
    Administrator,
    Student,
    Instructor,
      
]