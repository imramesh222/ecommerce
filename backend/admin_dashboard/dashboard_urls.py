from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Dashboard
    path('', login_required(views.custom_dashboard), name='dashboard'),
    # Add more dashboard-related URLs here
]
