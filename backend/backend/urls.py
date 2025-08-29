"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from rest_framework.schemas import get_schema_view
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# Import the custom admin site
from admin_dashboard.admin import admin_site

# Set the custom 404 handler
handler404 = 'admin_dashboard.views.custom_404'

# Use the custom admin site
admin.site = admin_site
admin.autodiscover()

# URL Configuration
urlpatterns = [
    # Admin URLs - using our custom admin site
    path('admin/', admin.site.urls),
    
    # Admin auth URLs (must come before admin_dashboard to avoid conflicts)
    path('admin/password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='admin_dashboard/password_reset.html',
            email_template_name='admin_dashboard/emails/password_reset_email.html',
            subject_template_name='admin_dashboard/emails/password_reset_subject.txt',
            success_url=reverse_lazy('admin:password_reset_done'),
        ), 
        name='admin_password_reset'
    ),
    path('admin/password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='admin_dashboard/password_reset_done.html'
        ), 
        name='admin_password_reset_done'
    ),
    path('admin/reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='admin_dashboard/password_reset_confirm.html',
            success_url=reverse_lazy('admin:password_reset_complete'),
        ), 
        name='admin_password_reset_confirm'
    ),
    path('admin/reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='admin_dashboard/password_reset_complete.html'
        ), 
        name='admin_password_reset_complete'
    ),
    
    # Admin Dashboard URLs - include with namespace
    path('admin/', include('admin_dashboard.urls', namespace='admin_dashboard')),
    
    # API URLs
    path('api/auth/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Root URL redirects to API documentation
    path('', RedirectView.as_view(url='/api/docs/')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
