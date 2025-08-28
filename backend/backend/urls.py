"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import the custom admin site and views
from admin_dashboard.views import custom_dashboard, custom_404, admin_login, admin_logout

# Set the custom 404 handler
handler404 = 'admin_dashboard.views.custom_404'

# Admin site configuration
admin.site.site_header = 'E-Commerce Admin'
admin.site.site_title = 'E-Commerce Admin'
admin.site.index_title = 'Dashboard'

urlpatterns = [
    # Admin dashboard - main entry point
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    
    # Admin dashboard app
    path('admin/', include('admin_dashboard.urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API URLs
    path('api/auth/', include('accounts.urls')),  # Authentication endpoints
    path('api/', include('products.urls')),       # Product-related endpoints
    path('api/', include('cart.urls')),           # Cart endpoints
    path('api/', include('orders.urls')),         # Order-related endpoints
    
    # Auth URLs (for password reset, etc.)
    path('accounts/', include([
        path('password_reset/', auth_views.PasswordResetView.as_view(
            template_name='admin_dashboard/password_reset.html',
            email_template_name='admin_dashboard/emails/password_reset_email.html',
            subject_template_name='admin_dashboard/emails/password_reset_subject.txt'
        ), name='password_reset'),
        path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
            template_name='admin_dashboard/password_reset_done.html'
        ), name='password_reset_done'),
        path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='admin_dashboard/password_reset_confirm.html'
        ), name='password_reset_confirm'),
        path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
            template_name='admin_dashboard/password_reset_complete.html'
        ), name='password_reset_complete'),
    ])),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
