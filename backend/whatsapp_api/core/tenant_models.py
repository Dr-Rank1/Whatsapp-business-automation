"""
Team and Multi-tenant models for collaborative workspaces.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Team(models.Model):
    """
    Team model for collaborative workspaces.
    Allows multiple users to work together under one organization.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True)
    
    # Owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_teams'
    )
    
    # Subscription (shared across team)
    subscription = models.OneToOneField(
        'billing.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team'
    )
    
    # Settings
    logo = models.URLField(blank=True)
    website = models.URLField(blank=True)
    
    # Limits
    max_members = models.IntegerField(default=5)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def can_add_member(self):
        return self.member_count < self.max_members


class TeamMember(models.Model):
    """
    Team member with role-based access control.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
    ]
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Invitation
    is_invited = models.BooleanField(default=False)
    invitation_token = models.CharField(max_length=64, blank=True)
    invitation_expires = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'team_members'
        unique_together = ['team', 'user']

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        if not self.invitation_token:
            self.invitation_token = str(uuid.uuid4())
        if not self.invitation_expires:
            self.invitation_expires = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    @property
    def can_manage(self):
        """Check if member can manage team settings."""
        return self.role in ['owner', 'admin']
    
    @property
    def can_invite(self):
        """Check if member can invite others."""
        return self.role in ['owner', 'admin', 'manager']
    
    @property
    def can_delete(self):
        """Check if member can delete resources."""
        return self.role in ['owner', 'admin', 'manager']


class Invitation(models.Model):
    """
    Team invitation tracking.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('expired', 'Expired'),
        ('declined', 'Declined'),
    ]
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=TeamMember.ROLE_CHOICES, default='member')
    
    # Invited by
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )
    
    # Token
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.email} for {self.team.name}"
    
    @property
    def is_valid(self):
        return self.status == 'pending' and self.expires_at > timezone.now()


class TeamSettings(models.Model):
    """
    Team-specific settings.
    """
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # Notifications
    email_notifications = models.BooleanField(default=True)
    slack_webhook = models.URLField(blank=True)
    
    # Default settings for new members
    default_role = models.CharField(
        max_length=20,
        choices=TeamMember.ROLE_CHOICES,
        default='member'
    )
    
    # Branding
    custom_domain = models.CharField(max_length=100, blank=True)
    accent_color = models.CharField(max_length=7, default='#2563eb')  # Hex color
    
    # Privacy
    allow_member_invites = models.BooleanField(default=True)
    require_approval_for_messages = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'team_settings'

    def __str__(self):
        return f"Settings for {self.team.name}"


class Notification(models.Model):
    """
    In-app notifications for users.
    """
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link
    link = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Action
    action_text = models.CharField(max_length=50, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
