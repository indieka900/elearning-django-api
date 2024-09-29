from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, UserPreferenceSerializer
from .services import NotificationService

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        unread = NotificationService.get_unread_notifications(request.user)
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        NotificationService.mark_as_read(pk)
        return Response({"status": "marked as read"})

class UserPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):

        try:
            notification_pref = NotificationPreference.objects.get(user=self.request.user)
            
            serializer.update(notification_pref, self.request.data)
        except NotificationPreference.DoesNotExist:
            serializer.save(user=self.request.user)