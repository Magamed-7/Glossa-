from rest_framework.permissions import BasePermission

class IsDashboardUser(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.dashboard_role in ['superadmin', 'moderator', 'analyst']
        )

class IsSuperadmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.dashboard_role == 'superadmin'
        )

class IsModerator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.dashboard_role in ['superadmin', 'moderator']
        )

class IsAnalyst(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.dashboard_role in ['superadmin', 'analyst']
        )