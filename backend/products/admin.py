from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Category, Product, ProductImage, Review, ProductVariant, ProductOption
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Product Count')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 100px; max-width: 100px;" />'
            )
        return _("No image")
    preview_image.short_description = _('Preview')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    readonly_fields = ('created_at', 'updated_at')


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'title', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'price', 'is_active', 'is_featured', 'quantity',
        'created_at', 'preview_image'
    )
    list_filter = ('is_active', 'is_featured', 'categories', 'condition', 'created_at')
    search_fields = ('name', 'description', 'sku', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = (
        'created_at', 'updated_at', 'discount_percentage', 'is_in_stock'
    )
    filter_horizontal = ('categories',)
    inlines = [
        ProductImageInline,
        ProductVariantInline,
        ProductOptionInline,
        ReviewInline,
    ]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'categories')
        }),
        (_('Pricing'), {
            'fields': (
                'price', 'compare_at_price', 'cost_per_item',
                'discount_percentage'
            )
        }),
        (_('Inventory'), {
            'fields': (
                'sku', 'barcode', 'quantity', 'track_quantity',
                'continue_selling_when_out_of_stock', 'is_in_stock'
            )
        }),
        (_('Shipping'), {
            'classes': ('collapse',),
            'fields': ('weight', 'height', 'width', 'length')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_featured', 'condition')
        }),
        (_('SEO'), {
            'classes': ('collapse',),
            'fields': ('seo_title', 'seo_description')
        }),
        (_('Timestamps'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def preview_image(self, obj):
        image = obj.images.filter(is_primary=True).first()
        if not image and obj.images.exists():
            image = obj.images.first()
        if image and image.image:
            return mark_safe(
                f'<img src="{image.image.url}" style="max-height: 50px; max-width: 50px;" />'
            )
        return _("No image")
    preview_image.short_description = _('Image')
    
    def save_model(self, request, obj, form, change):
        if not obj.sku:
            # Generate a default SKU if not provided
            from django.utils.text import slugify
            from random import randint
            obj.sku = f"{slugify(obj.name[:20])}-{randint(1000, 9999)}"
        super().save_model(request, obj, form, change)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating', 'is_verified_purchase', 'created_at')
    search_fields = ('product__name', 'user__email', 'title', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            _('Successfully approved %d review(s).') % updated,
            messages.SUCCESS
        )
    approve_reviews.short_description = _('Approve selected reviews')
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            _('Successfully disapproved %d review(s).') % updated,
            messages.SUCCESS
        )
    disapprove_reviews.short_description = _('Disapprove selected reviews')


class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'price', 'quantity', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('product__name', 'name', 'sku')
    list_select_related = ('product',)
    readonly_fields = ('created_at', 'updated_at')


class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_name_display', 'value', 'position')
    list_filter = ('name', 'created_at')
    search_fields = ('product__name', 'value')
    list_select_related = ('product',)
    readonly_fields = ('created_at',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(ProductOption, ProductOptionAdmin)
