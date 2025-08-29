from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, path
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDay
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import LoginView

from .models import DashboardMetrics, AdminDashboardSettings, DashboardWidget
from .views import custom_dashboard, admin_login, admin_logout


class CustomAdminSite(admin.AdminSite):
    site_header = 'E-Commerce Admin'
    site_title = 'E-Commerce Admin Portal'
    index_title = 'Dashboard'
    login_template = 'admin_dashboard/login.html'
    index_template = 'admin_dashboard/dashboard.html'
    
    def get_urls(self):
        from django.urls import include, path
        from django.contrib.auth import views as auth_views
        
        # Get default admin URLs
        urls = super().get_urls()
        
        # Define custom URLs
        custom_urls = [
            # Dashboard and auth
            path('', self.admin_view(custom_dashboard), name='index'),
            path('login/', admin_login, name='login'),
            path('logout/', admin_logout, name='logout'),
            
            # Password reset URLs
            path('password_reset/', 
                auth_views.PasswordResetView.as_view(
                    template_name='admin_dashboard/password_reset.html',
                    email_template_name='admin_dashboard/emails/password_reset_email.html',
                    subject_template_name='admin_dashboard/emails/password_reset_subject.txt',
                    success_url='done/'
                ), 
                name='admin_password_reset'),
                
            path('password_reset/done/', 
                auth_views.PasswordResetDoneView.as_view(
                    template_name='admin_dashboard/password_reset_done.html'
                ), 
                name='password_reset_done'),
                
            path('reset/<uidb64>/<token>/', 
                auth_views.PasswordResetConfirmView.as_view(
                    template_name='admin_dashboard/password_reset_confirm.html',
                    success_url='/admin/reset/done/'
                ), 
                name='password_reset_confirm'),
                
            path('reset/done/', 
                auth_views.PasswordResetCompleteView.as_view(
                    template_name='admin_dashboard/password_reset_complete.html'
                ), 
                name='password_reset_complete'),
        ]
        
        # Combine custom URLs with default admin URLs
        return custom_urls + urls
    
    def login(self, request, extra_context=None):
        """
        Display the login form for the given HttpRequest.
        """
        if request.method == 'GET' and self.has_permission(request):
            # Already logged-in, redirect to admin index
            index_path = reverse('admin:index', current_app=self.name)
            return HttpResponseRedirect(index_path)
            
        context = {
            **self.each_context(request),
            'title': _('Log in'),
            'app_path': request.get_full_path(),
            'username': request.user.get_username(),
        }
        
        if (REDIRECT_FIELD_NAME not in request.GET and 
                REDIRECT_FIELD_NAME not in request.POST):
            context[REDIRECT_FIELD_NAME] = reverse('admin:index', current_app=self.name)
            
        defaults = {
            'extra_context': {**context, **(extra_context or {})},
            'authentication_form': self.login_form or AuthenticationForm,
            'template_name': self.login_template or 'admin/login.html',
        }
        
        request.current_app = self.name
        return LoginView.as_view(**defaults)(request)

# Create custom admin site instance
admin_site = CustomAdminSite(name='admin')

# Set the default admin site to our custom admin site
admin.site = admin_site
admin.sites.site = admin_site
admin.autodiscover()

# Register models with the custom admin site
@admin.register(DashboardMetrics, site=admin_site)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = ('date_recorded', 'total_products', 'total_orders', 'total_revenue', 'total_customers')
    list_filter = ('date_recorded',)
    readonly_fields = ('date_recorded', 'total_products', 'total_orders', 'total_revenue', 
                     'total_customers', 'pending_orders', 'completed_orders', 
                     'low_stock_products', 'out_of_stock_products')
    date_hierarchy = 'date_recorded'
    ordering = ('-date_recorded',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AdminDashboardSettings, site=admin_site)
class AdminDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'enable_daily_reports', 'dashboard_refresh_interval')
    
    def has_add_permission(self, request):
        # Only one instance should exist
        return not AdminDashboardSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'widget_type', 'is_visible', 'position')
    list_editable = ('is_visible', 'position')
    list_filter = ('is_visible', 'widget_type')
    ordering = ('position', 'title')
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('position')


# Add a dashboard view to the admin site
class CustomAdminSite(admin.AdminSite):
    site_header = _('E-Commerce Admin')
    site_title = _('E-Commerce Admin')
    index_title = _('Dashboard')
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get dashboard settings
        dashboard_settings = AdminDashboardSettings.load()
        
        # Get latest metrics
        metrics = DashboardMetrics.get_latest_metrics()
        
# Import models and admins to ensure they're registered with the custom admin site
# The actual model registrations happen in their respective apps' admin.py files
# This import is just to ensure the admin modules are loaded
from products import admin as products_admin
from orders import admin as orders_admin
from accounts import admin as accounts_admin
