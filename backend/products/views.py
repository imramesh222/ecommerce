from django.db.models import Q, Avg, Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters, permissions, serializers
from rest_framework.decorators import action
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView,
    ListCreateAPIView, RetrieveUpdateDestroyAPIView
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import ProductFilter
from .models import Category, Product, Review, ProductVariant, ProductOption, ProductImage
from .permissions import IsAdminOrReadOnly, IsReviewAuthorOrReadOnly, IsProductOwnerOrReadOnly
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ReviewSerializer, ProductVariantSerializer,
    ProductOptionSerializer, ProductImageSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class with standard settings."""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(ModelViewSet):
    """ViewSet for viewing and editing categories."""
    queryset = Category.objects.filter(is_active=True).select_related('parent')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Optionally filter by parent category."""
        queryset = super().get_queryset()
        parent_slug = self.request.query_params.get('parent', None)
        
        if parent_slug:
            if parent_slug.lower() == 'none':
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent__slug=parent_slug)
        
        return queryset

    @method_decorator(cache_page(60 * 60 * 2))  # Cache for 2 hours
    @method_decorator(vary_on_cookie)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours
    @method_decorator(vary_on_cookie)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ProductViewSet(ModelViewSet):
    """ViewSet for viewing and editing products."""
    queryset = Product.objects.prefetch_related(
        'categories', 'images', 'variants', 'options', 'reviews'
    ).select_related().annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews', filter=Q(reviews__is_approved=True))
    )
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku', 'barcode']
    ordering_fields = ['price', 'created_at', 'average_rating']
    ordering = ['-created_at']
    lookup_field = 'slug'

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_queryset(self):
        """Filter products based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by category
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug, categories__is_active=True)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price is not None:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price is not None:
            queryset = queryset.filter(price__lte=float(max_price))
        
        # Filter by in-stock status
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(
                Q(track_quantity=False) | 
                (Q(track_quantity=True) & Q(quantity__gt=0)) |
                (Q(track_quantity=True) & Q(continue_selling_when_out_of_stock=True))
            )
        
        # Filter by featured status
        featured = self.request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        # Filter by condition
        condition = self.request.query_params.get('condition')
        if condition:
            queryset = queryset.filter(condition=condition.lower())
        
        return queryset.filter(is_active=True)

    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    @method_decorator(vary_on_headers('Authorization', 'Cookie'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours
    @method_decorator(vary_on_headers('Authorization', 'Cookie'))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Get related products based on categories."""
        product = self.get_object()
        related_products = Product.objects.filter(
            categories__in=product.categories.all(),
            is_active=True
        ).exclude(id=product.id).distinct()[:8]
        
        serializer = ProductListSerializer(
            related_products,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class ProductVariantViewSet(ModelViewSet):
    """ViewSet for viewing and editing product variants."""
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return ProductVariant.objects.none()
            
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            return ProductVariant.objects.none()
            
        return ProductVariant.objects.filter(
            product__slug=product_slug
        ).select_related('product')
    
    def perform_create(self, serializer):
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            raise serializers.ValidationError("Product slug is required")
            
        try:
            product = Product.objects.get(slug=product_slug)
            serializer.save(product=product)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")


class ProductOptionViewSet(ModelViewSet):
    """ViewSet for viewing and editing product options."""
    serializer_class = ProductOptionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return ProductOption.objects.none()
            
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            return ProductOption.objects.none()
            
        return ProductOption.objects.filter(
            product__slug=product_slug
        ).select_related('product')
    
    def perform_create(self, serializer):
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            raise serializers.ValidationError("Product slug is required")
            
        try:
            product = Product.objects.get(slug=product_slug)
            serializer.save(product=product)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")


class ReviewViewSet(ModelViewSet):
    """ViewSet for viewing and creating product reviews."""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewAuthorOrReadOnly]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return Review.objects.none()
            
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            return Review.objects.none()
            
        queryset = Review.objects.filter(
            product__slug=product_slug,
            is_approved=True
        ).select_related('user', 'product')
        
        # For non-admin users, only show approved reviews
        if not self.request.user.is_staff:
            return queryset
            
        # For admin users, show all reviews including unapproved ones
        return Review.objects.filter(
            product__slug=product_slug
        ).select_related('user', 'product')
    
    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs['product_slug'])
        serializer.save(
            user=self.request.user,
            product=product
        )
    
    @action(detail=False, methods=['get'])
    def pending(self, request, product_slug=None):
        """Get pending reviews (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to perform this action.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reviews = Review.objects.filter(
            product__slug=product_slug,
            is_approved=False
        ).select_related('user', 'product')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class ProductImageViewSet(ModelViewSet):
    """ViewSet for managing product images."""
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            # Return empty queryset for schema generation
            return ProductImage.objects.none()
            
        product_slug = self.kwargs.get('product_slug')
        if not product_slug:
            return ProductImage.objects.none()
            
        return ProductImage.objects.filter(
            product__slug=product_slug
        ).select_related('product')
    
    def perform_create(self, serializer):
        product = Product.objects.get(slug=self.kwargs['product_slug'])
        
        # If this is the first image, set it as primary
        if not product.images.exists():
            serializer.save(product=product, is_primary=True)
        else:
            serializer.save(product=product)
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, product_slug=None, pk=None):
        """Set an image as the primary image for the product."""
        image = self.get_object()
        
        # Update all images for this product to set is_primary=False
        ProductImage.objects.filter(
            product=image.product
        ).update(is_primary=False)
        
        # Set the selected image as primary
        image.is_primary = True
        image.save(update_fields=['is_primary'])
        
        return Response({'status': 'primary image set'})
