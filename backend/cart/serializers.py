from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem, SavedCart, SavedCartItem
from products.models import Product, ProductVariant
from products.serializers import ProductListSerializer as ProductSerializer, ProductVariantSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items."""
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        required=False,
        allow_null=True
    )
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    total = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id',
            'quantity', 'price', 'total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price', 'created_at', 'updated_at']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(_("Quantity must be at least 1."))
        return value
    
    def validate(self, data):
        product = data.get('product')
        variant = data.get('variant')
        
        if variant and variant.product != product:
            raise serializers.ValidationError({
                'variant_id': _("This variant doesn't belong to the selected product.")
            })
            
        # Check inventory if needed
        if variant and variant.inventory < data.get('quantity', 1):
            raise serializers.ValidationError({
                'quantity': _(f"Only {variant.inventory} items available in stock.")
            })
        elif product.inventory < data.get('quantity', 1):
            raise serializers.ValidationError({
                'quantity': _(f"Only {product.inventory} items available in stock.")
            })
            
        return data


class CartSerializer(serializers.ModelSerializer):
    """Serializer for the cart model."""
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    total_items = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'session_key', 'items', 'subtotal',
            'total', 'total_items', 'is_empty', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'session_key', 'created_at', 'updated_at']


class SavedCartItemSerializer(serializers.ModelSerializer):
    """Serializer for saved cart items (wishlist items)."""
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        source='variant',
        write_only=True,
        required=False,
        allow_null=True
    )
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    class Meta:
        model = SavedCartItem
        fields = [
            'id', 'product', 'product_id', 'variant', 'variant_id',
            'quantity', 'added_at'
        ]
        read_only_fields = ['added_at']


class SavedCartSerializer(serializers.ModelSerializer):
    """Serializer for saved carts (wishlists)."""
    items = SavedCartItemSerializer(many=True, read_only=True)
    item_count = serializers.IntegerField(source='items.count', read_only=True)
    
    class Meta:
        model = SavedCart
        fields = [
            'id', 'user', 'name', 'is_default', 'items', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate(self, data):
        if self.instance is None and 'is_default' not in data:
            # Set first saved cart as default if none exists
            if not SavedCart.objects.filter(
                user=self.context['request'].user,
                is_default=True
            ).exists():
                data['is_default'] = True
        return data


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart."""
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True
    )
    variant_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    quantity = serializers.IntegerField(default=1, min_value=1)
    update_quantity = serializers.BooleanField(default=False)
    
    def validate(self, data):
        product = data['product_id']
        variant = data.get('variant_id')
        
        if variant and variant.product != product:
            raise serializers.ValidationError({
                'variant_id': _("This variant doesn't belong to the selected product.")
            })
            
        # Check inventory
        if variant:
            if variant.inventory < data['quantity']:
                raise serializers.ValidationError({
                    'quantity': _(f"Only {variant.inventory} items available in stock.")
                })
        elif product.inventory < data['quantity']:
            raise serializers.ValidationError({
                'quantity': _(f"Only {product.inventory} items available in stock.")
            })
            
        return data
