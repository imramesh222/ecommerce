from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware to restrict access to admin dashboard to staff users only.
    """
    def process_request(self, request):
        # List of paths that don't require staff access
        public_paths = [
            '/admin/login/',
            '/admin/logout/',
            '/admin/password_reset/',
            '/admin/password_reset/done/',
            '/admin/reset/',
            '/admin/reset/done/',
        ]
        
        # Check if the request path starts with /admin/
        if request.path.startswith('/admin/'):
            # Allow access to public paths
            if any(request.path.startswith(path) for path in public_paths):
                return None
                
            # For all other admin paths, require staff status
            if not (request.user.is_authenticated and request.user.is_staff):
                return HttpResponseRedirect(f'/admin/login/?next={request.path}')
                
        return None
