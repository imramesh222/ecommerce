from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDay
from django.utils import timezone

from .models import DashboardMetrics, AdminDashboardSettings, DashboardWidget


@admin.register(DashboardMetrics)
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


@admin.register(AdminDashboardSettings)
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
        
        # Get recent orders (simplified example)
        from orders.models import Order
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
        
        # Get top products (simplified example)
        from products.models import Product
        top_products = Product.objects.annotate(
            order_count=Count('order_items')
        ).order_by('-order_count')[:5]
        
        extra_context.update({
            'dashboard_settings': dashboard_settings,
            'metrics': metrics,
            'recent_orders': recent_orders,
            'top_products': top_products,
            'show_dashboard': True,
        })
        
        return super().index(request, extra_context)


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='customadmin')

# Register models with the custom admin site
custom_admin_site.register(DashboardMetrics, DashboardMetricsAdmin)
custom_admin_site.register(AdminDashboardSettings, AdminDashboardSettingsAdmin)
custom_admin_site.register(DashboardWidget, DashboardWidgetAdmin)

# Register other models with the custom admin site
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from products.admin import ProductAdmin, CategoryAdmin, ReviewAdmin, ProductVariantAdmin, ProductOptionAdmin
from products.models import Product, Category, Review, ProductVariant, ProductOption

custom_admin_site.register(Group, GroupAdmin)
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Product, ProductAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Review, ReviewAdmin)
custom_admin_site.register(ProductVariant, ProductVariantAdmin)
custom_admin_site.register(ProductOption, ProductOptionAdmin)
