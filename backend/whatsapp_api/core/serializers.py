"""
Core app serializers for authentication and user management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'whatsapp_connected', 'subscription_tier',
            'api_usage_limit', 'api_usage_count', 'timezone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'whatsapp_connected', 'api_usage_count', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'company_name', 'business_description', 'default_country_code',
            'auto_reply_enabled', 'greeting_message', 'away_message',
            'working_hours_start', 'working_hours_end',
            'notification_email', 'webhook_url'
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class TokenObtainPairSerializer(serializers.Serializer):
    """Custom token serializer with additional user data."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        refresh = RefreshToken.for_user(user)
        
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'timezone']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile details."""
    
    class Meta:
        model = UserProfile
        fields = [
            'company_name', 'business_description', 'default_country_code',
            'auto_reply_enabled', 'greeting_message', 'away_message',
            'working_hours_start', 'working_hours_end',
            'notification_email', 'webhook_url'
        ]
