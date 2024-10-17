from rest_framework import serializers
from elearning.models import Course
from .models import PreSignup, Payment, MpesaCallback
from .mpesa_client import MpesaClient

client = MpesaClient()

class PreSignupSerializer(serializers.ModelSerializer):
    """Serializer for storing temporary user details during payment."""
    class Meta:
        model = PreSignup
        fields = ['email', 'phone_number', 'service_type', 'service_id']
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
            'service_type': {'required': True},
            'service_id': {'required': True},
        }

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for handling payment details."""
    class Meta:
        model = Payment
        fields = ['user', 'service_type', 'service_id', 'amount', 'payment_plan', 'payment_method', 'status', 'transaction_id', 'timestamp']
        read_only_fields = ['status', 'transaction_id', 'timestamp']

class MpesaCallbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaCallback
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', required=False, allow_null=True)
    user_name = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['user_id', 'user_name', 'course_name', 'amount', 'payment_plan', 'payment_method', 'timestamp']

    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return None

    def get_course_name(self, obj):
        if obj.service_type == 'course':
            try:
                course = Course.objects.get(id=obj.service_id)
                return course.name
            except Course.DoesNotExist:
                return None
        return None