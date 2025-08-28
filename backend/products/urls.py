from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')

# Nested router for product variants, options, images, and reviews
products_router = nested_routers.NestedSimpleRouter(
    router, r'products', lookup='product'
)
products_router.register(
    r'variants', views.ProductVariantViewSet,
    basename='product-variant'
)
products_router.register(
    r'options', views.ProductOptionViewSet,
    basename='product-option'
)
products_router.register(
    r'images', views.ProductImageViewSet,
    basename='product-image'
)
products_router.register(
    r'reviews', views.ReviewViewSet,
    basename='product-review'
)

# URL patterns
urlpatterns = [
    # Include the default router URLs
    path('', include(router.urls)),
    
    # Include the nested router URLs
    path('', include(products_router.urls)),
    
    # Additional endpoints for reviews
    path(
        'products/<slug:product_slug>/reviews/pending/',
        views.ReviewViewSet.as_view({'get': 'pending'}),
        name='product-review-pending'
    ),
    
    # Additional endpoints for images
    path(
        'products/<slug:product_slug>/images/<int:pk>/set_primary/',
        views.ProductImageViewSet.as_view({'post': 'set_primary'}),
        name='product-image-set-primary'
    ),
    
    # Additional endpoints for related products
    path(
        'products/<slug:slug>/related/',
        views.ProductViewSet.as_view({'get': 'related'}),
        name='product-related'
    ),
]
