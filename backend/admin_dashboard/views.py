from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

# Models
from products.models import Product, Category
from orders.models import Order
from accounts.models import User

def custom_404(request, exception=None):
    """Custom 404 handler for admin dashboard."""
    return render(request, 'admin_dashboard/404.html', status=404)

def admin_login(request):
    """Custom admin login view."""
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    
    # Handle form submission
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None and user.is_active and user.is_staff:
            login(request, user)
            next_url = request.POST.get('next', reverse('admin_dashboard'))
            return HttpResponseRedirect(next_url)
        else:
            messages.error(request, 'Invalid email or password')
    
    # Get the next URL from the query string
    next_url = request.GET.get('next', reverse('admin_dashboard'))
    
    return render(request, 'admin_dashboard/login.html', {
        'next': next_url,
        'title': 'Admin Login'
    })

def admin_logout(request):
    """Custom admin logout view."""
    logout(request)
    return redirect('admin_login')

@staff_member_required
def custom_dashboard(request):
    """Custom admin dashboard view."""
    # Get metrics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    
    # Get revenue (sum of completed orders)
    revenue = Order.objects.filter(status='completed').aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
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
        'revenue': revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'order_status': order_status,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)

def custom_dashboard(request):
    """Custom admin dashboard view."""
    # Only allow staff users
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')
    
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
    
    context = {
        'title': 'Dashboard',
        'total_products': total_products,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    
    return render(request, 'admin_dashboard/index.html', context)


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
