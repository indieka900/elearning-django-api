from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, NotificationPreference, NotificationType

def create_notification(user, notification_type, content):
    preference, created = NotificationPreference.objects.get_or_create(
        user=user,
        notification_type=notification_type,
        defaults={'email_enabled': True, 'platform_enabled': True}
    )
    
    if preference.platform_enabled:
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            content=content
        )
        return notification
    return None

def send_email_notification(user, notification_type, content):
    preference, created = NotificationPreference.objects.get_or_create(
        user=user,
        notification_type=notification_type,
        defaults={'email_enabled': True, 'platform_enabled': True}
    )
    
    if preference.email_enabled and user.email and user.email_verified:
        subject = f"New {notification_type.name} Notification"
        send_mail(
            subject,
            content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    return False

def get_user_notifications(user):
    return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')

def mark_notification_as_read(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False