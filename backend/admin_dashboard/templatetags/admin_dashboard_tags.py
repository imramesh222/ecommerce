from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    """Get dashboard statistics."""
    from products.models import Product, Order
    from accounts.models import User
    
    # Calculate date ranges for comparison
    today = timezone.now().date()
    last_week = today - timedelta(days=7)
    
    # Get current period stats
    current_orders = Order.objects.filter(created_at__date__gte=today).count()
    current_revenue = sum(order.total_amount for order in Order.objects.filter(created_at__date__gte=today))
    current_customers = User.objects.filter(date_joined__date__gte=today, is_customer=True).count()
    
    # Get previous period stats for comparison
    previous_orders = Order.objects.filter(created_at__date__range=(last_week, today - timedelta(days=1))).count()
    previous_revenue = sum(order.total_amount for order in Order.objects.filter(created_at__date__range=(last_week, today - timedelta(days=1))))
    previous_customers = User.objects.filter(date_joined__date__range=(last_week, today - timedelta(days=1)), is_customer=True).count()
    
    # Calculate trends
    orders_trend = ((current_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else 0
    revenue_trend = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    customers_trend = ((current_customers - previous_customers) / previous_customers * 100) if previous_customers > 0 else 0
    
    # Get product stats
    total_products = Product.objects.count()
    low_stock = Product.objects.filter(quantity__gt=0, quantity__lte=10).count()
    out_of_stock = Product.objects.filter(quantity=0).count()
    
    return {
        'total_orders': Order.objects.count(),
        'total_revenue': sum(order.total_amount for order in Order.objects.all()),
        'total_customers': User.objects.filter(is_customer=True).count(),
        'total_products': total_products,
        'low_stock_products': low_stock,
        'out_of_stock_products': out_of_stock,
        'orders_trend': orders_trend,
        'revenue_trend': revenue_trend,
        'customers_trend': customers_trend,
    }

@register.filter
def format_currency(value):
    """Format a number as currency."""
    if value is None:
        return "$0.00"
    return f"${float(value):,.2f}"

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary."""
    return dictionary.get(key)

@register.filter
def percentage(value, decimal_places=1):
    """Format a number as a percentage."""
    if value is None:
        return "0%"
    return f"{float(value):.{int(decimal_places)}f}%"

@register.filter
def trend_icon(value):
    """Return an icon based on trend value."""
    if value > 0:
        return mark_safe('<i class="fas fa-arrow-up trend-up"></i>')
    elif value < 0:
        return mark_safe('<i class="fas fa-arrow-down trend-down"></i>')
    return mark_safe('<i class="fas fa-minus"></i>')

@register.filter
def trend_class(value):
    """Return a CSS class based on trend value."""
    if value > 0:
        return 'trend-up'
    elif value < 0:
        return 'trend-down'
    return ''

@register.simple_tag
def get_recent_activity(limit=5):
    """Get recent admin activity."""
    from django.contrib.admin.models import LogEntry
    return LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')[:limit]

@register.filter
def get_action_icon(log_entry):
    """Get an icon for the log entry action."""
    icons = {
        1: 'plus',    # Addition
        2: 'edit',    # Change
        3: 'trash',   # Deletion
    }
    return icons.get(log_entry.action_flag, 'info-circle')

@register.filter
def get_content_type_name(content_type):
    """Get a human-readable name for a content type."""
    names = {
        'product': 'Product',
        'order': 'Order',
        'user': 'User',
        'category': 'Category',
    }
    return names.get(content_type.model, content_type.model.capitalize())

@register.filter
def get_change_message(log_entry):
    """Format the change message for a log entry."""
    if log_entry.change_message and log_entry.change_message[0] == '[':
        # This is a JSON array of change messages
        import json
        try:
            messages = json.loads(log_entry.change_message)
            return ' '.join(messages)
        except (json.JSONDecodeError, TypeError):
            pass
    return log_entry.change_message or 'Changed'
