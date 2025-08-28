from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db.models import Count, Sum, Q, F, Value, IntegerField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.contrib.contenttypes.models import ContentType

from products.models import Product, Category
from orders.models import Order
from accounts.models import User


class DashboardMetrics(models.Model):
    """Model to store and calculate dashboard metrics."""
    date_recorded = models.DateField(_('date recorded'), default=timezone.now, unique=True)
    total_products = models.PositiveIntegerField(_('total products'), default=0)
    total_orders = models.PositiveIntegerField(_('total orders'), default=0)
    total_revenue = models.DecimalField(_('total revenue'), max_digits=12, decimal_places=2, default=0)
    total_customers = models.PositiveIntegerField(_('total customers'), default=0)
    pending_orders = models.PositiveIntegerField(_('pending orders'), default=0)
    completed_orders = models.PositiveIntegerField(_('completed orders'), default=0)
    low_stock_products = models.PositiveIntegerField(_('low stock products'), default=0)
    out_of_stock_products = models.PositiveIntegerField(_('out of stock products'), default=0)
    
    class Meta:
        verbose_name = _('Dashboard Metrics')
        verbose_name_plural = _('Dashboard Metrics')
        ordering = ['-date_recorded']
    
    def __str__(self):
        return f"Metrics for {self.date_recorded}"
    
    @classmethod
    def get_latest_metrics(cls):
        """Get the most recent metrics or create new ones."""
        today = timezone.now().date()
        metrics, created = cls.objects.get_or_create(date_recorded=today)
        if created:
            metrics.update_metrics()
        return metrics
    
    def update_metrics(self):
        """Update all metrics."""
        
        # Product metrics
        self.total_products = Product.objects.count()
        self.low_stock_products = Product.objects.filter(
            quantity__gt=0, 
            quantity__lte=settings.LOW_STOCK_THRESHOLD
        ).count()
        self.out_of_stock_products = Product.objects.filter(quantity=0).count()
        
        # Order metrics
        self.total_orders = Order.objects.count()
        self.pending_orders = Order.objects.filter(status='pending').count()
        self.completed_orders = Order.objects.filter(status='completed').count()
        
        # Revenue metrics
        revenue = Order.objects.filter(status='completed').aggregate(
            total_sum=Coalesce(Sum('total'), 0, output_field=IntegerField())
        )['total_sum']
        self.total_revenue = revenue if revenue else 0
        
        # Customer metrics - count all active users as customers
        self.total_customers = User.objects.filter(is_active=True).count()
        
        self.save()


class AdminDashboardSettings(models.Model):
    """Model to store admin dashboard settings and configurations."""
    enable_daily_reports = models.BooleanField(_('enable daily reports'), default=True)
    low_stock_threshold = models.PositiveIntegerField(_('low stock threshold'), default=10)
    dashboard_refresh_interval = models.PositiveIntegerField(
        _('dashboard refresh interval (minutes)'), 
        default=5,
        help_text=_('Set to 0 to disable auto-refresh')
    )
    show_recent_orders = models.BooleanField(_('show recent orders'), default=True)
    show_sales_statistics = models.BooleanField(_('show sales statistics'), default=True)
    show_product_metrics = models.BooleanField(_('show product metrics'), default=True)
    show_customer_insights = models.BooleanField(_('show customer insights'), default=True)
    
    class Meta:
        verbose_name = _('Dashboard Settings')
        verbose_name_plural = _('Dashboard Settings')
    
    def __str__(self):
        return 'Admin Dashboard Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load the settings or create default ones."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class DashboardWidget(models.Model):
    """Model to store admin dashboard widget configurations."""
    WIDGET_TYPES = [
        ('recent_orders', _('Recent Orders')),
        ('sales_chart', _('Sales Chart')),
        ('top_products', _('Top Products')),
        ('revenue_stats', _('Revenue Statistics')),
        ('customer_activity', _('Customer Activity')),
        ('inventory_status', _('Inventory Status')),
    ]
    
    title = models.CharField(_('title'), max_length=100)
    widget_type = models.CharField(_('widget type'), max_length=50, choices=WIDGET_TYPES)
    is_visible = models.BooleanField(_('is visible'), default=True)
    position = models.PositiveIntegerField(_('position'), default=0)
    settings = models.JSONField(_('settings'), default=dict, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Dashboard Widget')
        verbose_name_plural = _('Dashboard Widgets')
        ordering = ['position', 'title']
    
    def __str__(self):
        return self.title
