# your_app/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow administrators to access the view.
    """

    def has_permission(self, request, view):
        print(f"User: {request.user}, Is staff: {request.user.is_staff}")
        # Check if the user is authenticated and is an admin
        return request.user and request.user.is_staff
