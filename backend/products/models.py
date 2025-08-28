from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """Product category model."""
    name = models.CharField(_('name'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('parent category')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent == self:
            raise ValidationError(_('A category cannot be a parent of itself.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product model."""
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('used', _('Used')),
        ('refurbished', _('Refurbished')),
    ]
    
    name = models.CharField(_('name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    compare_at_price = models.DecimalField(
        _('compare at price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    cost_per_item = models.DecimalField(
        _('cost per item'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )
    sku = models.CharField(_('SKU'), max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(_('barcode'), max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(_('quantity'), default=0)
    track_quantity = models.BooleanField(_('track quantity'), default=True)
    continue_selling_when_out_of_stock = models.BooleanField(
        _('continue selling when out of stock'),
        default=False
    )
    categories = models.ManyToManyField(
        Category,
        related_name='products',
        verbose_name=_('categories')
    )
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    condition = models.CharField(
        _('condition'),
        max_length=20,
        choices=CONDITION_CHOICES,
        default='new'
    )
    weight = models.DecimalField(
        _('weight'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Weight in grams')
    )
    height = models.DecimalField(
        _('height'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Height in centimeters')
    )
    width = models.DecimalField(
        _('width'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Width in centimeters')
    )
    length = models.DecimalField(
        _('length'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Length in centimeters')
    )
    seo_title = models.CharField(_('SEO title'), max_length=70, blank=True)
    seo_description = models.CharField(_('SEO description'), max_length=160, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        """Check if the product is in stock."""
        if not self.track_quantity or self.continue_selling_when_out_of_stock:
            return True
        return self.quantity > 0

    @property
    def discount_percentage(self):
        """Calculate the discount percentage if compare_at_price is set."""
        if self.compare_at_price and self.compare_at_price > self.price:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return round(discount, 2)
        return 0


class ProductImage(models.Model):
    """Product image model."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product')
    )
    image = models.ImageField(
        _('image'),
        upload_to='products/images/'
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=128,
        blank=True,
        help_text=_('Alternative text for accessibility')
    )
    is_primary = models.BooleanField(_('is primary'), default=False)
    position = models.PositiveIntegerField(_('position'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['position', 'created_at']
        unique_together = ['product', 'is_primary']

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"

    def clean(self):
        # Ensure only one primary image per product
        if self.is_primary and ProductImage.objects.filter(
            product=self.product, is_primary=True
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('A primary image already exists for this product.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Review(models.Model):
    """Product review model."""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user')
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('title'), max_length=200)
    comment = models.TextField(_('comment'))
    is_approved = models.BooleanField(_('is approved'), default=False)
    is_verified_purchase = models.BooleanField(_('is verified purchase'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        unique_together = ['product', 'user']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating}"

    def clean(self):
        # Ensure users can only review products they've purchased
        if not self.is_verified_purchase:
            from orders.models import OrderItem
            has_purchased = OrderItem.objects.filter(
                order__user=self.user,
                product=self.product
            ).exists()
            if not has_purchased:
                raise ValidationError(_('You can only review products you have purchased.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        # Update product's average rating
        self.product.save()


class ProductVariant(models.Model):
    """Product variant model for different options like size, color, etc."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('product')
    )
    name = models.CharField(_('variant name'), max_length=100)
    sku = models.CharField(_('SKU'), max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quantity = models.PositiveIntegerField(_('quantity'), default=0)
    is_default = models.BooleanField(_('is default'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('product variant')
        verbose_name_plural = _('product variants')
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def clean(self):
        # Ensure only one default variant per product
        if self.is_default and ProductVariant.objects.filter(
            product=self.product, is_default=True
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('A default variant already exists for this product.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ProductOption(models.Model):
    """Product options like size, color, etc."""
    OPTION_TYPES = [
        ('size', _('Size')),
        ('color', _('Color')),
        ('material', _('Material')),
        ('style', _('Style')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('product')
    )
    name = models.CharField(_('option name'), max_length=50, choices=OPTION_TYPES)
    value = models.CharField(_('option value'), max_length=100)
    position = models.PositiveIntegerField(_('position'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('product option')
        verbose_name_plural = _('product options')
        ordering = ['position']
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.get_name_display()}: {self.value}"
