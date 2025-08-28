from rest_framework import status, permissions, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Cart, CartItem, SavedCart, SavedCartItem
from .serializers import (
    CartSerializer, CartItemSerializer, 
    SavedCartSerializer, SavedCartItemSerializer,
    AddToCartSerializer
)
from products.models import Product, ProductVariant


class CartViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """ViewSet for cart operations."""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return empty queryset for schema generation or unauthenticated users
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Cart.objects.none()
            
        return Cart.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_object(self):
        # Get or create user's cart
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add an item to the cart."""
        cart = self.get_object()
        serializer = AddToCartSerializer(data=request.data)
        
        if serializer.is_valid():
            product = serializer.validated_data['product_id']
            variant = serializer.validated_data.get('variant_id')
            quantity = serializer.validated_data['quantity']
            update_quantity = serializer.validated_data['update_quantity']
            
            try:
                with transaction.atomic():
                    cart_item = cart.add_item(
                        product=product,
                        variant=variant,
                        quantity=quantity,
                        update_quantity=update_quantity
                    )
                
                # Return the updated cart
                serializer = self.get_serializer(cart)
                return Response(serializer.data, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove an item from the cart."""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        
        if not product_id:
            return Response(
                {'detail': _('Product ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
            variant = None
            if variant_id:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            
            cart.remove_item(product=product, variant=variant)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return Response(
                {'detail': _('Product or variant not found')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from the cart."""
        cart = self.get_object()
        cart.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def merge(self, request):
        """Merge a session cart with the user's cart."""
        session_key = request.data.get('session_key')
        if not session_key:
            return Response(
                {'detail': _('Session key is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            session_cart = Cart.objects.get(session_key=session_key, user__isnull=True)
            cart = self.get_object()
            cart.merge_cart(session_cart)
            
            serializer = self.get_serializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response(
                {'detail': _('Session cart not found')},
                status=status.HTTP_404_NOT_FOUND
            )


class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet for cart item operations."""
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return CartItem.objects.none()
            
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Update cart item quantity."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow updating quantity
        if 'quantity' not in request.data:
            return Response(
                {'detail': _('Only quantity can be updated')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            instance, 
            data={'quantity': request.data['quantity']}, 
            partial=partial
        )
        
        if serializer.is_valid():
            self.perform_update(serializer)
            cart_serializer = CartSerializer(instance.cart)
            return Response(cart_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavedCartViewSet(viewsets.ModelViewSet):
    """ViewSet for saved carts (wishlists)."""
    serializer_class = SavedCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return SavedCart.objects.none()
            
        return SavedCart.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add an item to a saved cart (wishlist)."""
        saved_cart = self.get_object()
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        
        if not product_id:
            return Response(
                {'detail': _('Product ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            variant = None
            
            if variant_id:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            
            # Check if item already exists
            item, created = SavedCartItem.objects.get_or_create(
                saved_cart=saved_cart,
                product=product,
                variant=variant,
                defaults={'quantity': quantity}
            )
            
            if not created:
                item.quantity += quantity
                item.save()
            
            serializer = SavedCartItemSerializer(item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return Response(
                {'detail': _('Product or variant not found')},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def move_to_cart(self, request, pk=None):
        """Move an item from saved cart to main cart."""
        saved_cart = self.get_object()
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response(
                {'detail': _('Item ID is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = saved_cart.saved_items.get(id=item_id)
            cart, _ = Cart.objects.get_or_create(user=request.user)
            
            # Add to cart
            cart.add_item(
                product=item.product,
                variant=item.variant,
                quantity=item.quantity
            )
            
            # Remove from saved cart
            item.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except SavedCartItem.DoesNotExist:
            return Response(
                {'detail': _('Item not found in this saved cart')},
                status=status.HTTP_404_NOT_FOUND
            )


class SavedCartItemViewSet(viewsets.ModelViewSet):
    """ViewSet for saved cart items."""
    serializer_class = SavedCartItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return SavedCartItem.objects.none()
            
        return SavedCartItem.objects.filter(saved_cart__user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Update saved cart item quantity."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Only allow updating quantity
        if 'quantity' not in request.data:
            return Response(
                {'detail': _('Only quantity can be updated')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(
            instance, 
            data={'quantity': request.data['quantity']}, 
            partial=partial
        )
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
