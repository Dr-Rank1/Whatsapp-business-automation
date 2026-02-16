"""
Core views for authentication and user management.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import logout
from .models import UserProfile
from .serializers import (
    UserSerializer, UserRegistrationSerializer, TokenObtainPairSerializer,
    ChangePasswordSerializer, UserUpdateSerializer, ProfileUpdateSerializer,
    UserProfileSerializer
)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Registration successful.'
        }, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    """User login endpoint with JWT tokens."""
    serializer_class = TokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(generics.GenericAPIView):
    """User logout endpoint."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            logout(request)
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password endpoint."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Password changed successfully.'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        profile = getattr(user, 'profile', None)
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data if profile else None
        })
    
    def update(self, request, *args, **kwargs):
        user = request.user
        user_serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        
        profile_data = request.data.get('profile', {})
        if profile_data and hasattr(user, 'profile'):
            profile_serializer = ProfileUpdateSerializer(
                user.profile, data=profile_data, partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        
        return Response({
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(user.profile).data
        })


class UserView(generics.RetrieveAPIView):
    """Get current user details."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """Refresh access token."""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        return Response({
            'access': str(token.access_token),
            'refresh': str(token)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """Get user statistics and quota info."""
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
        'subscription_tier': user.subscription_tier,
        'api_usage_limit': user.api_usage_limit,
        'api_usage_count': user.api_usage_count,
        'remaining_quota': user.remaining_quota,
        'whatsapp_connected': user.whatsapp_connected,
    })
