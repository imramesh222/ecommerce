from django.contrib import admin
from .models import Order, OrderItem, OrderNote

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'product_name', 'variant_name', 'price', 'quantity')
    can_delete = False

class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 1
    readonly_fields = ('user', 'created_at', 'updated_at')
    fields = ('note', 'is_public', 'user', 'created_at', 'updated_at')

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__email', 'billing_first_name', 'billing_last_name')
    inlines = [OrderItemInline, OrderNoteInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total')
        }),
        ('Billing Information', {
            'fields': (
                'billing_first_name', 'billing_last_name', 'billing_email',
                'billing_phone', 'billing_address', 'billing_city',
                'billing_state', 'billing_postal_code', 'billing_country'
            )
        }),
        ('Shipping Information', {
            'fields': (
                'shipping_first_name', 'shipping_last_name', 'shipping_phone',
                'shipping_address', 'shipping_city', 'shipping_state',
                'shipping_postal_code', 'shipping_country'
            )
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'variant', 'quantity', 'price', 'total')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'product__name', 'sku')
    readonly_fields = ('order', 'product', 'variant', 'product_name', 'variant_name', 'sku', 'price', 'quantity')

class OrderNoteAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'created_at', 'is_public')
    list_filter = ('is_public', 'created_at')
    search_fields = ('order__order_number', 'note')
    readonly_fields = ('order', 'user', 'created_at', 'updated_at')


# Register models with the admin site
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(OrderNote, OrderNoteAdmin)
