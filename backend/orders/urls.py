from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'order-items', views.OrderItemViewSet, basename='order-item')
router.register(r'order-notes', views.OrderNoteViewSet, basename='order-note')

app_name = 'orders'

urlpatterns = [
    path('', include(router.urls)),
]
