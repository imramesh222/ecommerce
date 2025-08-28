from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirect root to dashboard
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    
    # Custom dashboard
    path('dashboard/', login_required(views.custom_dashboard), name='admin_dashboard'),
    
    # Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Django admin (original admin interface)
    path('django-admin/', admin.site.urls),
    
    # API endpoints for dashboard data (if needed)
    path('api/', include([
        path('stats/', views.dashboard_stats, name='dashboard_stats'),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom admin site title and header
admin.site.site_header = 'E-Commerce Admin'
admin.site.site_title = 'E-Commerce Admin'
admin.site.index_title = 'Dashboard'
