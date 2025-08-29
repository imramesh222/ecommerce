from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from . import views

# Define app name for namespacing
app_name = 'admin_dashboard'

# This is important for admin site to work with our custom URLs
admin.autodiscover()

urlpatterns = [
    # Root URL redirects to login or dashboard based on auth status
    path('', views.admin_redirect, name='admin_redirect'),
    
    # Login/Logout URLs - using our custom views
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard (protected by login_required)
    path('', include('admin_dashboard.dashboard_urls')),
    
    # API endpoints for dashboard data
    path('api/stats/', login_required(views.dashboard_stats), name='dashboard_stats'),
    
    # Password reset URLs with admin_dashboard namespace
    path('password_reset/', 
        auth_views.PasswordResetView.as_view(
            template_name='admin_dashboard/password_reset.html',
            email_template_name='admin_dashboard/emails/password_reset_email.html',
            subject_template_name='admin_dashboard/emails/password_reset_subject.txt',
            success_url=reverse_lazy('admin_dashboard:password_reset_done'),
        ), 
        name='password_reset'
    ),
    path('password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='admin_dashboard/password_reset_done.html'
        ), 
        name='password_reset_done'
    ),
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(
            template_name='admin_dashboard/password_reset_confirm.html',
            success_url=reverse_lazy('admin_dashboard:password_reset_complete'),
            extra_context={'admin_login_url': reverse_lazy('admin_dashboard:login')}
        ), 
        name='password_reset_confirm'
    ),
    path('reset/done/', 
        auth_views.PasswordResetCompleteView.as_view(
            template_name='admin_dashboard/password_reset_complete.html',
            extra_context={'admin_login_url': reverse_lazy('admin_dashboard:login')}
        ), 
        name='password_reset_complete'
    ),
]
