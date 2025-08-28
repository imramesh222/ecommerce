from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions

from .models import UserProfile, UserAddress

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password2 from the data before creating the user
        validated_data.pop('password2', None)
        
        # Create the user
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token obtain pair serializer to include user data in the response."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Add extra responses here
        data['user'] = UserSerializer(self.user).data
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""
    
    class Meta:
        model = UserProfile
        fields = ('bio', 'website', 'facebook_url', 'twitter_handle', 
                 'instagram_handle', 'receive_newsletter', 'email_notifications')
        read_only_fields = ('created_at', 'updated_at')


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for user addresses."""
    
    class Meta:
        model = UserAddress
        fields = ('id', 'address_type', 'full_name', 'phone_number', 
                 'address_line1', 'address_line2', 'city', 'state', 
                 'postal_code', 'country', 'is_default', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at')

    def validate(self, attrs):
        # If this is being set as default, update other addresses
        if attrs.get('is_default', False):
            UserAddress.objects.filter(
                user=self.context['request'].user,
                address_type=attrs.get('address_type', 'home')
            ).update(is_default=False)
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    
    profile = UserProfileSerializer(read_only=True)
    addresses = UserAddressSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number',
                 'profile_picture', 'date_of_birth', 'is_email_verified',
                 'address_line1', 'address_line2', 'city', 'state',
                 'postal_code', 'country', 'profile', 'addresses',
                 'date_joined', 'last_login')
        read_only_fields = ('id', 'email', 'is_email_verified', 'date_joined', 'last_login')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add the full URL for the profile picture if it exists
        if representation.get('profile_picture'):
            request = self.context.get('request')
            if request is not None:
                representation['profile_picture'] = request.build_absolute_uri(instance.profile_picture.url)
        return representation


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password2 = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "The two password fields didn't match."})
        
        # Validate the new password
        try:
            validate_password(data['new_password'], self.context['request'].user)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
            
        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user
