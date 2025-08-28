from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q
from django.utils import timezone

def get_dashboard_stats():
    """
    Get statistics for the admin dashboard.
    Returns a dictionary with various statistics.
    """
    from products.models import Product
    from orders.models import Order
    from accounts.models import User
    
    # Calculate date ranges
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    
    # Get basic counts
    stats = {
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'total_customers': User.objects.filter(is_staff=False).count(),
        'total_revenue': Order.objects.filter(status='completed').aggregate(
            total=Sum('total')
        )['total'] or 0,
    }
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    stats['recent_orders'] = recent_orders
    
    # Get top products
    top_products = Product.objects.annotate(
        order_count=Count('order_items')
    ).order_by('-order_count')[:5]
    stats['top_products'] = top_products
    
    # Get order status counts
    order_status = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    stats['order_status'] = order_status
    
    # Get recent customers
    recent_customers = User.objects.filter(
        is_staff=False
    ).order_by('-date_joined')[:5]
    stats['recent_customers'] = recent_customers
    
    # Get sales data for the last 7 days
    sales_data = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_sales = Order.objects.filter(
            created_at__date=date,
            status='completed'
        ).aggregate(
            total=Sum('total')
        )['total'] or 0
        
        sales_data.append({
            'date': date,
            'total': float(day_sales)
        })
    
    stats['sales_data'] = sorted(sales_data, key=lambda x: x['date'])
    
    return stats

def get_recent_activity(limit=10):
    """
    Get recent activity across the system.
    """
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    
    # Get recent admin actions
    recent_actions = LogEntry.objects.select_related(
        'user', 'content_type'
    ).order_by('-action_time')[:limit]
    
    # Format the actions
    activities = []
    for action in recent_actions:
        activities.append({
            'user': action.user,
            'action_time': action.action_time,
            'action_flag': action.get_action_flag_display(),
            'object_repr': action.object_repr,
            'content_type': action.content_type,
            'change_message': action.change_message
        })
    
    return activities

def get_system_health():
    """
    Get system health information.
    """
    import os
    import platform
    import psutil
    from django.conf import settings
    
    # Get system information
    system_info = {
        'os': f"{platform.system()} {platform.release()}",
        'python_version': platform.python_version(),
        'django_version': settings.VERSION,
        'database': settings.DATABASES['default']['ENGINE'].split('.')[-1],
    }
    
    # Get resource usage
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    resource_usage = {
        'cpu_percent': psutil.cpu_percent(),
        'memory_used': memory_info.rss / (1024 * 1024),  # Convert to MB
        'memory_percent': process.memory_percent(),
        'disk_usage': psutil.disk_usage('/').percent,
    }
    
    # Get database stats
    from django.db import connection
    db_stats = {}
    with connection.cursor() as cursor:
        cursor.execute("SELECT datname FROM pg_database WHERE datname = %s", [connection.settings_dict['NAME']])
        if cursor.rowcount > 0:
            cursor.execute("""
                SELECT relname, n_live_tup 
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
                LIMIT 10
            """)
            db_stats['table_sizes'] = [{'table': row[0], 'rows': row[1]} for row in cursor.fetchall()]
    
    return {
        'system': system_info,
        'resources': resource_usage,
        'database': db_stats,
    }
