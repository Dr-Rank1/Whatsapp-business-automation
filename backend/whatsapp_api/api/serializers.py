"""
API serializers for WhatsApp automation.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Contact, MessageTemplate, Campaign, ScheduledMessage, MessageLog, Analytics


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact model."""
    
    class Meta:
        model = Contact
        fields = [
            'id', 'phone', 'name', 'email', 'company', 'tags',
            'notes', 'is_blocked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ContactListSerializer(serializers.ModelSerializer):
    """Simplified contact serializer for list views."""
    
    class Meta:
        model = Contact
        fields = ['id', 'phone', 'name', 'company', 'tags', 'is_blocked', 'created_at']


class MessageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for MessageTemplate model."""
    
    class Meta:
        model = MessageTemplate
        fields = [
            'id', 'name', 'content', 'variables', 'category',
            'is_active', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MessageTemplateDetailSerializer(serializers.ModelSerializer):
    """Detailed template serializer with usage stats."""
    
    class Meta:
        model = MessageTemplate
        fields = '__all__'


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model."""
    contacts_detail = ContactListSerializer(source='contacts', many=True, read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'template', 'template_name',
            'message_content', 'contacts', 'contacts_detail', 'status',
            'total_contacts', 'sent_count', 'delivered_count', 'failed_count',
            'scheduled_at', 'started_at', 'completed_at',
            'delay_between_messages', 'retry_failed', 'max_retries',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'sent_count', 'delivered_count', 'failed_count',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        if data.get('scheduled_at') and data['scheduled_at'] < timezone.now():
            raise serializers.ValidationError({'scheduled_at': 'Scheduled time must be in the future.'})
        return data


class CampaignDetailSerializer(serializers.ModelSerializer):
    """Detailed campaign serializer with full info."""
    contacts_detail = ContactListSerializer(source='contacts', many=True, read_only=True)
    
    class Meta:
        model = Campaign
        fields = '__all__'


class ScheduledMessageSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledMessage model."""
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone', read_only=True)
    
    class Meta:
        model = ScheduledMessage
        fields = [
            'id', 'contact', 'contact_name', 'contact_phone', 'template',
            'message_content', 'status', 'scheduled_at', 'sent_at',
            'is_recurring', 'recurrence_pattern', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'sent_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        if data.get('scheduled_at') and data['scheduled_at'] < timezone.now():
            raise serializers.ValidationError({'scheduled_at': 'Scheduled time must be in the future.'})
        return data


class ScheduledMessageDetailSerializer(serializers.ModelSerializer):
    """Detailed scheduled message serializer."""
    
    class Meta:
        model = ScheduledMessage
        fields = '__all__'


class MessageLogSerializer(serializers.ModelSerializer):
    """Serializer for MessageLog model."""
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    
    class Meta:
        model = MessageLog
        fields = [
            'id', 'contact', 'contact_name', 'contact_phone',
            'campaign', 'campaign_name', 'template',
            'message_content', 'status', 'error_message', 'retry_count',
            'sent_at', 'delivered_at', 'read_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'error_message', 'retry_count',
            'sent_at', 'delivered_at', 'read_at', 'created_at'
        ]


class MessageLogDetailSerializer(serializers.ModelSerializer):
    """Detailed message log serializer."""
    
    class Meta:
        model = MessageLog
        fields = '__all__'


class AnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for Analytics model."""
    
    class Meta:
        model = Analytics
        fields = [
            'id', 'date', 'messages_sent', 'messages_delivered',
            'messages_failed', 'messages_read', 'contacts_added',
            'campaigns_created', 'scheduled_messages'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    total_contacts = serializers.IntegerField()
    total_templates = serializers.IntegerField()
    total_campaigns = serializers.IntegerField()
    total_scheduled = serializers.IntegerField()
    messages_sent_today = serializers.IntegerField()
    messages_sent_this_month = serializers.IntegerField()
    messages_delivered = serializers.IntegerField()
    messages_failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
