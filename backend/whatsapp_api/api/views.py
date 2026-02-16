"""
API views for WhatsApp automation.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Contact, MessageTemplate, Campaign, ScheduledMessage, MessageLog, Analytics
from .serializers import (
    ContactSerializer, ContactListSerializer, MessageTemplateSerializer,
    MessageTemplateDetailSerializer, CampaignSerializer, CampaignDetailSerializer,
    ScheduledMessageSerializer, ScheduledMessageDetailSerializer,
    MessageLogSerializer, MessageLogDetailSerializer,
    AnalyticsSerializer, DashboardStatsSerializer
)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for Contact CRUD operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone', 'email', 'company']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ContactListSerializer
        return ContactSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a contact."""
        contact = self.get_object()
        contact.is_blocked = True
        contact.save()
        return Response({'status': 'Contact blocked'})
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a contact."""
        contact = self.get_object()
        contact.is_blocked = False
        contact.save()
        return Response({'status': 'Contact unblocked'})
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export contacts as CSV."""
        contacts = self.get_queryset()
        # Return JSON for now, can be extended to CSV
        return Response(ContactListSerializer(contacts, many=True).data)


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for MessageTemplate CRUD operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'content']
    ordering_fields = ['name', 'usage_count', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return MessageTemplate.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MessageTemplateDetailSerializer
        return MessageTemplateSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available template categories."""
        return Response([
            {'value': 'greeting', 'label': 'Greeting'},
            {'value': 'support', 'label': 'Support'},
            {'value': 'promotional', 'label': 'Promotional'},
            {'value': 'notification', 'label': 'Notification'},
            {'value': 'followup', 'label': 'Follow-up'},
            {'value': 'custom', 'label': 'Custom'},
        ])
    
    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        """Increment template usage count."""
        template = self.get_object()
        template.usage_count += 1
        template.save(update_fields=['usage_count'])
        return Response({'usage_count': template.usage_count})


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for Campaign CRUD operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'status', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user).prefetch_related('contacts')
    
    def get_serializer_class(self,):
        if self.action == 'retrieve':
            return CampaignDetailSerializer
        return CampaignSerializer
    
    def perform_create(self, serializer):
        campaign = serializer.save(user=self.request.user)
        campaign.total_contacts = campaign.contacts.count()
        campaign.save(update_fields=['total_contacts'])
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a campaign."""
        campaign = self.get_object()
        if campaign.status != 'draft':
            return Response(
                {'error': 'Only draft campaigns can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'running'
        campaign.started_at = timezone.now()
        campaign.save()
        
        # Trigger message sending logic here (could be Celery task)
        return Response({'status': 'Campaign started', 'campaign_id': campaign.id})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a running campaign."""
        campaign = self.get_object()
        if campaign.status != 'running':
            return Response(
                {'error': 'Only running campaigns can be paused'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'draft'
        campaign.save()
        return Response({'status': 'Campaign paused'})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a campaign."""
        campaign = self.get_object()
        if campaign.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Campaign already completed or cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.status = 'cancelled'
        campaign.completed_at = timezone.now()
        campaign.save()
        return Response({'status': 'Campaign cancelled'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get campaign statistics."""
        campaigns = self.get_queryset()
        return Response({
            'total': campaigns.count(),
            'draft': campaigns.filter(status='draft').count(),
            'running': campaigns.filter(status='running').count(),
            'completed': campaigns.filter(status='completed').count(),
            'failed': campaigns.filter(status='failed').count(),
        })


class ScheduledMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for ScheduledMessage CRUD operations."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['scheduled_at', 'status', 'created_at']
    ordering = ['scheduled_at']
    
    def get_queryset(self):
        return ScheduledMessage.objects.filter(user=self.request.user).select_related('contact', 'template')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ScheduledMessageDetailSerializer
        return ScheduledMessageSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a scheduled message."""
        scheduled = self.get_object()
        if scheduled.status in ['sent', 'failed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel this scheduled message'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scheduled.status = 'cancelled'
        scheduled.save()
        return Response({'status': 'Scheduled message cancelled'})
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming scheduled messages."""
        upcoming = self.get_queryset().filter(
            status='pending',
            scheduled_at__gte=timezone.now()
        )[:10]
        return Response(ScheduledMessageSerializer(upcoming, many=True).data)


class MessageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for MessageLog (read-only)."""
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['contact__phone', 'contact__name', 'message_content']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return MessageLog.objects.filter(user=self.request.user).select_related('contact', 'campaign', 'template')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MessageLogDetailSerializer
        return MessageLogSerializer
    
    @action(detail=False, methods=['get'])
    def failed(self, request):
        """Get failed messages for retry."""
        failed = self.get_queryset().filter(status='failed')[:50]
        return Response(MessageLogSerializer(failed, many=True).data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed message."""
        message = self.get_object()
        if message.status != 'failed':
            return Response(
                {'error': 'Only failed messages can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.status = 'pending'
        message.error_message = ''
        message.retry_count += 1
        message.save()
        
        return Response({'status': 'Message queued for retry'})


class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Analytics (read-only)."""
    permission_classes = [IsAuthenticated]
    serializer_class = AnalyticsSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        return Analytics.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard statistics."""
        user = request.user
        now = timezone.now()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate stats
        total_contacts = Contact.objects.filter(user=user).count()
        total_templates = MessageTemplate.objects.filter(user=user).count()
        total_campaigns = Campaign.objects.filter(user=user).count()
        total_scheduled = ScheduledMessage.objects.filter(user=user, status='pending').count()
        
        messages_sent_today = MessageLog.objects.filter(
            user=user, sent_at__date=today
        ).count()
        
        messages_sent_this_month = MessageLog.objects.filter(
            user=user, sent_at__gte=month_start
        ).count()
        
        messages_delivered = MessageLog.objects.filter(
            user=user, status='delivered'
        ).count()
        
        messages_failed = MessageLog.objects.filter(
            user=user, status='failed'
        ).count()
        
        total_sent = MessageLog.objects.filter(user=user).count()
        success_rate = (messages_delivered / total_sent * 100) if total_sent > 0 else 0
        
        return Response(DashboardStatsSerializer({
            'total_contacts': total_contacts,
            'total_templates': total_templates,
            'total_campaigns': total_campaigns,
            'total_scheduled': total_scheduled,
            'messages_sent_today': messages_sent_today,
            'messages_sent_this_month': messages_sent_this_month,
            'messages_delivered': messages_delivered,
            'messages_failed': messages_failed,
            'success_rate': round(success_rate, 2),
        }).data)
    
    @action(detail=False, methods=['get'])
    def chart(self, request):
        """Get chart data for analytics."""
        user = request.user
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        analytics = Analytics.objects.filter(
            user=user,
            date__gte=start_date.date()
        ).order_by('date')
        
        return Response(AnalyticsSerializer(analytics, many=True).data)
