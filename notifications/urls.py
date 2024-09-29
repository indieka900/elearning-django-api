from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserPreferenceViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'platform', NotificationViewSet, basename='notification')
router.register(r'preferences', UserPreferenceViewSet, basename='preference')

urlpatterns = [
    path('', include(router.urls)),
]
