from django.apps import AppConfig
from django.conf import settings


class AdminDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_dashboard'
    
    def ready(self):
        # Add our middleware to the settings
        self._add_middleware()
        
    def _add_middleware(self):
        """Add our middleware to the settings if not already present."""
        middleware_setting = 'MIDDLEWARE'
        middleware_class = 'admin_dashboard.middleware.AdminAccessMiddleware'
        
        # Add our middleware if not already present
        if middleware_class not in settings.MIDDLEWARE:
            # Add our middleware after AuthenticationMiddleware
            try:
                auth_middleware_index = settings.MIDDLEWARE.index(
                    'django.contrib.auth.middleware.AuthenticationMiddleware'
                )
                settings.MIDDLEWARE.insert(auth_middleware_index + 1, middleware_class)
            except ValueError:
                # If AuthenticationMiddleware is not found, add to the end
                settings.MIDDLEWARE.append(middleware_class)
    verbose_name = 'Admin Dashboard'
    
    def ready(self):
        # Import here to avoid AppRegistryNotReady errors
        import admin_dashboard.signals  # Register signals
        
        # Set up default dashboard settings if they don't exist
        from .models import AdminDashboardSettings
        try:
            AdminDashboardSettings.load()
        except Exception as e:
            # Log error but don't prevent app from loading
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading AdminDashboardSettings: {e}")
            
        # Call parent ready method
        super().ready()
