from rest_framework import serializers
from .models import Notification, NotificationPreference

class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'notification_type_display', 'content', 'created_at', 'is_read']
        read_only_fields = ['created_at', 'notification_type_display']

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ['chat', 'live_class', 'assignment', 'submission', 'transaction']
