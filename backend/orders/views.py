from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Order, OrderItem, OrderNote
from .serializers import (
    OrderSerializer, OrderItemSerializer, 
    OrderNoteSerializer, CreateOrderSerializer
)
from .permissions import IsOrderOwnerOrAdmin


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
    
    def get_queryset(self):
        """Return orders for the current user, or all orders for admin."""
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return Order.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
            
        if user.is_staff:
            return Order.objects.all().order_by('-created_at')
            
        return Order.objects.filter(user=user).order_by('-created_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set the user for new orders."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order."""
        order = self.get_object()
        
        if order.status == Order.STATUS_CANCELLED:
            return Response(
                {'detail': _('Order is already cancelled.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status not in [Order.STATUS_PENDING, Order.STATUS_PROCESSING]:
            return Response(
                {'detail': _('Cannot cancel order in current status.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = Order.STATUS_CANCELLED
        order.save()
        
        # Add a note about cancellation
        OrderNote.objects.create(
            order=order,
            author=request.user,
            note=_('Order cancelled by user.'),
            is_public=True
        )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': _('Only admin can update order status.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'status': [_('Invalid status.')]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        
        # Set completed_at if order is marked as completed
        if new_status == Order.STATUS_COMPLETED and not order.completed_at:
            from django.utils import timezone
            order.completed_at = timezone.now()
        
        order.save()
        
        # Add a note about status change
        OrderNote.objects.create(
            order=order,
            author=request.user,
            note=_('Status changed from %(old_status)s to %(new_status)s.') % {
                'old_status': order.get_status_display(),
                'new_status': dict(Order.STATUS_CHOICES).get(new_status, new_status)
            },
            is_public=False
        )
        
        return Response(OrderSerializer(order).data)


class OrderNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing order notes."""
    serializer_class = OrderNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
    
    def get_queryset(self):
        """Return notes for orders the user has access to."""
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return OrderNote.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return OrderNote.objects.none()
            
        if user.is_staff:
            return OrderNote.objects.all()
            
        return OrderNote.objects.filter(
            Q(order__user=user) | 
            (Q(is_public=True) & ~Q(order__user=user))
        )
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Set the author for new notes."""
        serializer.save(author=self.request.user)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing order items."""
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrAdmin]
    
    def get_queryset(self):
        """Return order items for orders the user has access to."""
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return OrderItem.objects.none()
            
        user = self.request.user
        if not user.is_authenticated:
            return OrderItem.objects.none()
            
        if user.is_staff:
            return OrderItem.objects.all()
            
        return OrderItem.objects.filter(order__user=user)
    
    def get_serializer_context(self):
        """Add request to serializer context."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
