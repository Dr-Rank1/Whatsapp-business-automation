"""
API URL configuration for v1 endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactViewSet, MessageTemplateViewSet, CampaignViewSet,
    ScheduledMessageViewSet, MessageLogViewSet, AnalyticsViewSet
)

router = DefaultRouter()
router.register(r'contacts', ContactViewSet, basename='contacts')
router.register(r'templates', MessageTemplateViewSet, basename='templates')
router.register(r'campaigns', CampaignViewSet, basename='campaigns')
router.register(r'scheduled', ScheduledMessageViewSet, basename='scheduled')
router.register(r'messages', MessageLogViewSet, basename='messages')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]
