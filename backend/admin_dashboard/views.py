# Standard library imports
from datetime import datetime, timedelta

# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Sum, Q, F, Case, When, Value, IntegerField
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.views.decorators.http import require_http_methods
from django.db import transaction

# Models
from products.models import Product, Category
from orders.models import Order
from accounts.models import User

def admin_redirect(request):
    """Redirect to login if not authenticated, otherwise to admin dashboard."""
    if request.user.is_authenticated and request.user.is_staff:
        # If already authenticated and staff, redirect to admin index
        return redirect('admin:index')
    # Otherwise, redirect to the login page with next parameter
    return redirect('{}?next={}'.format(reverse('admin_dashboard:login'), request.path))

def custom_404(request, exception=None):
    """Custom 404 handler for admin dashboard."""
    return render(request, 'admin_dashboard/404.html', status=404)

@never_cache
def admin_login(request, extra_context=None):
    """
    Custom admin login view that works with the admin site.
    """
    from django.contrib.admin.views.decorators import staff_member_required
    from django.contrib.admin.views.decorators import user_passes_test
    from django.contrib.auth.views import LoginView
    
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    
    # Use the admin's login view but with our template
    return LoginView.as_view(
        template_name='admin_dashboard/login.html',
        extra_context={
            **{
                'title': 'Log in',
                'app_path': request.path,
                'site_title': 'E-Commerce Admin',
                'site_header': 'E-Commerce Admin',
                'has_permission': request.user.is_authenticated and request.user.is_staff,
                'site_url': '/admin',
                'is_popup': False,
                'is_nav_sidebar_enabled': False,
                'available_apps': [],
            },
            **(extra_context or {})
        }
    )(request)

def admin_logout(request):
    """Custom admin logout view."""
    from django.contrib.auth import logout
    logout(request)
    return redirect('admin:login')

@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='admin:login')
def custom_dashboard(request):
    """Custom admin dashboard view."""
    
    # Get statistics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    
    # Calculate total revenue
    total_revenue = Order.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    
    # Get top products
    top_products = Product.objects.annotate(
        order_count=Count('order_items')
    ).order_by('-order_count')[:5]
    
    # Get order status distribution
    order_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'title': 'Admin Dashboard',
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'order_status': order_status,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


def dashboard_stats(request):
    """API endpoint to get dashboard statistics."""
    if not request.user.is_authenticated or not request.user.is_staff:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    from django.http import JsonResponse
    from datetime import datetime, timedelta
    
    # Get date range for the last 7 days
    today = datetime.now().date()
    date_range = [today - timedelta(days=i) for i in range(7)]
    date_range.reverse()
    
    # Get orders by status
    status_counts = Order.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Get daily sales for the last 7 days
    daily_sales = []
    for date in date_range:
        next_date = date + timedelta(days=1)
        day_sales = Order.objects.filter(
            created_at__date__gte=date,
            created_at__date__lt=next_date,
            status='completed'
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        daily_sales.append({
            'date': date.strftime('%Y-%m-%d'),
            'total': float(day_sales)
        })
    
    # Get top products
    top_products = Product.objects.annotate(
        order_count=Count('order_items')
    ).order_by('-order_count')[:5].values('id', 'name', 'order_count')
    
    # Get recent orders
    recent_orders = list(Order.objects.select_related('user').order_by('-created_at')[:5].values(
        'id', 'order_number', 'user__email', 'total', 'status', 'created_at'
    ))
    
    return JsonResponse({
        'status': 'success',
        'stats': {
            'total_products': Product.objects.count(),
            'total_orders': Order.objects.count(),
            'total_customers': User.objects.filter(is_staff=False).count(),
            'total_revenue': float(Order.objects.filter(
                status='completed'
            ).aggregate(
                total=Sum('total')
            )['total'] or 0)
        },
        'daily_sales': daily_sales,
        'status_counts': list(status_counts),
        'top_products': list(top_products),
        'recent_orders': recent_orders,
    })
