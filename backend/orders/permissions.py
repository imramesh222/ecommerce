from rest_framework import permissions

class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is the owner of the order or an admin.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the order or admin.
        return obj.user == request.user or request.user.is_staff


class IsOrderItemOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is the owner of the order item's order or an admin.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner of the order or admin.
        return obj.order.user == request.user or request.user.is_staff


class IsOrderNoteAuthorOrAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is the author of the note or an admin.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the author of the note or admin.
        return obj.author == request.user or request.user.is_staff
