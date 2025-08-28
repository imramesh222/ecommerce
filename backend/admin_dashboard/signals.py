from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import DashboardMetrics

@receiver(post_save, sender=None)
def update_dashboard_metrics_on_save(sender, instance, created, **kwargs):
    """Update dashboard metrics when relevant models are saved."""
    from products.models import Product
    from orders.models import Order

    from accounts.models import User
    
    model_name = sender.__name__
    
    if model_name in ['Product', 'Order', 'User']:
        update_dashboard_metrics()

@receiver(post_delete, sender=None)
def update_dashboard_metrics_on_delete(sender, instance, **kwargs):
    """Update dashboard metrics when relevant models are deleted."""
    from products.models import Product
    from orders.models import Order
    from accounts.models import User
    
    model_name = sender.__name__
    
    if model_name in ['Product', 'Order', 'User']:
        update_dashboard_metrics()

def update_dashboard_metrics():
    """Update the dashboard metrics for the current day."""
    today = timezone.now().date()
    metrics, created = DashboardMetrics.objects.get_or_create(date_recorded=today)
    metrics.update_metrics()
