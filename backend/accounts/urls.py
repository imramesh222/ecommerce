from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile
    path('me/', views.CurrentUserView.as_view(), name='current_user'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/details/', views.UserProfileDetailsView.as_view(), name='profile_details'),
    path('profile/picture/', views.UserProfilePictureView.as_view(), name='profile_picture'),
    
    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Addresses
    path('addresses/', views.UserAddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/<int:pk>/', views.UserAddressDetailView.as_view(), name='address_detail'),
]
