from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem, OrderNote
from products.serializers import ProductListSerializer as ProductSerializer, ProductVariantSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product = ProductSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'variant', 'quantity', 'price', 'total']
        read_only_fields = ['id', 'order', 'product', 'variant', 'price', 'total']

class OrderNoteSerializer(serializers.ModelSerializer):
    """Serializer for order notes."""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = OrderNote
        fields = ['id', 'order', 'user', 'user_name', 'note', 'is_public', 'created_at']
        read_only_fields = ['id', 'order', 'user', 'user_name', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    items = OrderItemSerializer(many=True, read_only=True)
    notes = OrderNoteSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'user_email', 'user_name', 'status', 'status_display',
            'payment_status', 'payment_status_display', 'subtotal', 'tax_amount', 'shipping_cost',
            'discount_amount', 'total', 'currency', 'billing_address', 'shipping_address', 'payment_id', 'transaction_id',
            'tracking_number', 'notes', 'items', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'status', 'payment_status', 'subtotal', 'tax_amount',
            'shipping_cost', 'discount_amount', 'total', 'currency', 'payment_id', 'transaction_id',
            'tracking_number', 'created_at', 'updated_at', 'completed_at'
        ]
    
    def to_representation(self, instance):
        """Modify representation to include notes based on user permissions."""
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and hasattr(request, 'user'):
            if not request.user.is_staff:
                representation['notes'] = [
                    note for note in representation['notes'] 
                    if note['is_public']
                ]
        
        return representation


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating orders from a cart."""
    cart_id = serializers.UUIDField(required=True)
    billing_address = serializers.DictField(required=True)
    shipping_address = serializers.DictField(required=True)
    shipping_method = serializers.CharField(required=True)
    payment_method = serializers.CharField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_cart_id(self, value):
        from cart.models import Cart
        try:
            cart = Cart.objects.get(id=value)
            if cart.is_empty:
                raise serializers.ValidationError(_("The cart is empty."))
            if cart.items.count() == 0:
                raise serializers.ValidationError(_("Cannot create order with an empty cart."))
            return cart
        except Cart.DoesNotExist:
            raise serializers.ValidationError(_("Invalid cart ID."))
    
    def validate_billing_address(self, value):
        required_fields = ['first_name', 'last_name', 'address1', 'city', 'country', 'postal_code']
        return self._validate_address(value, required_fields)
    
    def validate_shipping_address(self, value):
        required_fields = ['first_name', 'last_name', 'address1', 'city', 'country', 'postal_code']
        return self._validate_address(value, required_fields)
    
    def _validate_address(self, address, required_fields):
        if not isinstance(address, dict):
            raise serializers.ValidationError(_("Address must be a JSON object."))
        
        missing_fields = [field for field in required_fields if field not in address]
        if missing_fields:
            raise serializers.ValidationError(
                _("Missing required address fields: {}".format(", ".join(missing_fields)))
            )
        return address
    
    def create(self, validated_data):
        from cart.models import CartItem
        from decimal import Decimal
        import uuid
        
        cart = validated_data.pop('cart_id')
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        
        # Calculate order totals
        cart_items = cart.items.select_related('product', 'variant').all()
        subtotal = sum(item.total for item in cart_items)
        shipping_cost = Decimal('10.00')  # This should come from shipping method
        tax_rate = Decimal('0.1')  # Example 10% tax rate
        tax_amount = (subtotal + shipping_cost) * tax_rate
        total = subtotal + shipping_cost + tax_amount
        
        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=tax_amount,
            total=total,
            currency='USD',
            billing_address=validated_data['billing_address'],
            shipping_address=validated_data['shipping_address'],
            shipping_method=validated_data['shipping_method'],
            payment_method=validated_data['payment_method'],
            customer_note=validated_data.get('notes', '')
        )
        
        # Create order items
        order_items = []
        for cart_item in cart_items:
            order_items.append(OrderItem(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                product_name=cart_item.product.name,
                variant_name=cart_item.variant.name if cart_item.variant else None,
                sku=cart_item.variant.sku if cart_item.variant else cart_item.product.sku,
                price=cart_item.price,
                quantity=cart_item.quantity,
                tax_amount=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
                total=cart_item.total
            ))
        
        # Bulk create order items
        if order_items:
            OrderItem.objects.bulk_create(order_items)
        
        # Clear the cart
        cart.items.all().delete()
        cart.save()
        
        return order
