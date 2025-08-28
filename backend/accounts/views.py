from rest_framework import generics, status, permissions, exceptions
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer, 
    CustomTokenObtainPairSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserAddressSerializer,
    ChangePasswordSerializer
)
from .models import UserProfile, UserAddress

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        token_serializer = CustomTokenObtainPairSerializer.get_token(user)
        
        return Response({
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(token_serializer),
            'access': str(token_serializer.access_token),
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view to use our custom serializer."""
    serializer_class = CustomTokenObtainPairSerializer


@swagger_auto_schema(
    operation_description="Retrieve or update the authenticated user's profile",
    responses={
        200: UserSerializer()
    }
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """View to retrieve and update user profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        # Handle profile picture upload
        if 'profile_picture' in self.request.FILES:
            serializer.save(profile_picture=self.request.FILES['profile_picture'])
        else:
            serializer.save()


class ChangePasswordView(generics.UpdateAPIView):
    """View for changing user password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Update the user's session auth hash to prevent logging them out
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        return Response(
            {"message": "Password updated successfully"}, 
            status=status.HTTP_200_OK
        )


@swagger_auto_schema(
    operation_description="List all addresses for the authenticated user or create a new address",
    responses={
        200: UserAddressSerializer(many=True),
        201: UserAddressSerializer()
    }
)
class UserAddressListCreateView(generics.ListCreateAPIView):
    """View to list and create user addresses."""
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return empty queryset during schema generation to prevent errors
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
            
        # Ensure user is authenticated before filtering
        if not self.request.user.is_authenticated:
            return UserAddress.objects.none()
            
        return UserAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise exceptions.PermissionDenied("Authentication required")
        serializer.save(user=self.request.user)


@swagger_auto_schema(
    operation_description="Retrieve, update or delete an address",
    responses={
        200: UserAddressSerializer(),
        204: 'No Content'
    }
)
class UserAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update, or delete a user address."""
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return empty queryset during schema generation to prevent errors
        if getattr(self, 'swagger_fake_view', False):
            return UserAddress.objects.none()
            
        # Ensure user is authenticated before filtering
        if not self.request.user.is_authenticated:
            return UserAddress.objects.none()
            
        return UserAddress.objects.filter(user=self.request.user)


class UserProfilePictureView(APIView):
    """View to handle user profile picture uploads."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        if 'profile_picture' not in request.FILES:
            return Response(
                {"error": "No profile picture provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile_picture = request.FILES['profile_picture']
        user.save()
        
        return Response(
            {"profile_picture": user.profile_picture.url},
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, *args, **kwargs):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete()
            user.profile_picture = None
            user.save()
        return Response(
            {"message": "Profile picture removed successfully"},
            status=status.HTTP_204_NO_CONTENT
        )


@swagger_auto_schema(
    operation_description="Retrieve or update the authenticated user's profile details",
    responses={
        200: UserProfileSerializer()
    }
)
class UserProfileDetailsView(generics.RetrieveUpdateAPIView):
    """View to retrieve and update user profile details."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        # Get or create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


@swagger_auto_schema(
    operation_description="Get the currently authenticated user's details",
    responses={
        200: UserSerializer()
    }
)
class CurrentUserView(generics.RetrieveAPIView):
    """View to get the currently authenticated user's details."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
