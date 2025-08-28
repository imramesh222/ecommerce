from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from products.models import Product, ProductVariant


class Cart(models.Model):
    """Model representing a shopping cart."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Anonymous Cart ({self.id})"
    
    @property
    def is_empty(self):
        """Check if cart is empty."""
        return self.items.count() == 0
    
    @property
    def total_items(self):
        """Return total quantity of items in cart."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal (sum of all item totals)."""
        return sum(item.total for item in self.items.all())
    
    @property
    def total(self):
        """Calculate cart total (subtotal + any additional charges)."""
        # In a real implementation, you might add shipping, taxes, discounts here
        return self.subtotal
    
    def add_item(self, product, variant=None, quantity=1, update_quantity=False):
        """
        Add or update an item in the cart.
        
        Args:
            product: Product instance
            variant: Optional ProductVariant instance
            quantity: Item quantity
            update_quantity: If True, quantity is updated, otherwise added to existing
            
        Returns:
            CartItem: The created or updated cart item
        """
        if quantity < 1:
            return None
            
        # Check if item already exists in cart
        cart_item, created = self.items.get_or_create(
            product=product,
            variant=variant,
            defaults={'quantity': 0}
        )
        
        if update_quantity or created:
            cart_item.quantity = quantity
        else:
            cart_item.quantity += quantity
            
        cart_item.save()
        return cart_item
    
    def remove_item(self, product, variant=None):
        """Remove an item from the cart."""
        self.items.filter(product=product, variant=variant).delete()
    
    def clear(self):
        """Remove all items from the cart."""
        self.items.all().delete()
    
    def merge_cart(self, session_cart):
        """Merge a session cart into this cart."""
        if session_cart and session_cart != self:
            for item in session_cart.items.all():
                self.add_item(
                    product=item.product,
                    variant=item.variant,
                    quantity=item.quantity
                )
            session_cart.delete()


class CartItem(models.Model):
    """Model representing an item in a shopping cart."""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        _('price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product', 'variant']
        ordering = ['-created_at']
    
    def __str__(self):
        if self.variant:
            return f"{self.quantity}x {self.product.name} - {self.variant.name}"
        return f"{self.quantity}x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Set price from product or variant
        if self.variant and self.variant.price is not None:
            self.price = self.variant.price
        else:
            self.price = self.product.price
        
        # Ensure quantity is at least 1
        if self.quantity < 1:
            self.quantity = 1
            
        super().save(*args, **kwargs)
    
    @property
    def total(self):
        """Calculate total price for this line item."""
        return self.price * self.quantity
    
    def get_product_name(self):
        """Get display name including variant if applicable."""
        if self.variant:
            return f"{self.product.name} - {self.variant.name}"
        return self.product.name
    
    def get_absolute_url(self):
        """Get URL for this cart item's product."""
        return self.product.get_absolute_url()


class SavedCart(models.Model):
    """Model for saved carts (wishlist or saved for later)."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_carts'
    )
    name = models.CharField(_('name'), max_length=100)
    items = models.ManyToManyField(
        'products.Product',
        through='SavedCartItem',
        related_name='saved_in_carts'
    )
    is_default = models.BooleanField(
        _('default wishlist'),
        default=False,
        help_text=_('Set as default wishlist')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('saved cart')
        verbose_name_plural = _('saved carts')
        ordering = ['-is_default', '-updated_at']
    
    def __str__(self):
        return f"{self.user.email}'s {self.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default wishlist per user
        if self.is_default:
            SavedCart.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class SavedCartItem(models.Model):
    """Through model for SavedCart items."""
    saved_cart = models.ForeignKey(
        SavedCart,
        on_delete=models.CASCADE,
        related_name='saved_items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='saved_cart_items'
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saved_cart_items'
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('saved cart item')
        verbose_name_plural = _('saved cart items')
        unique_together = ['saved_cart', 'product', 'variant']
        ordering = ['-added_at']
    
    def __str__(self):
        if self.variant:
            return f"{self.quantity}x {self.product.name} - {self.variant.name}"
        return f"{self.quantity}x {self.product.name}"
