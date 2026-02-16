"""
Audit logging middleware for tracking user actions.
"""
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log important actions.
    """
    
    # Actions to log
    LOGGED_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    IGNORED_PATHS = [
        '/api/v1/auth/login/',
        '/api/v1/auth/logout/',
        '/api/v1/auth/token/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        # Store start time for response time tracking
        request._audit_start_time = None
        return None
    
    def process_response(self, request, response):
        # Skip logging for certain paths
        if any(request.path.startswith(path) for path in self.IGNORED_PATHS):
            return response
        
        # Only log certain status codes
        if response.status_code in [403, 500]:
            self._log_security_event(request, response)
        
        # Log successful creates/updates/deletes
        if request.method in self.LOGGED_METHODS and response.status_code in [200, 201, 204]:
            self._log_action(request, response)
        
        return response
    
    def _log_action(self, request, response):
        """Log create/update/delete actions."""
        from whatsapp_api.api.webhook_models import AuditLog
        
        try:
            # Determine resource type
            resource_type = self._get_resource_type(request.path)
            if not resource_type:
                return
            
            # Get action type
            action_map = {
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'update',
                'DELETE': 'delete',
            }
            action = action_map.get(request.method, 'read')
            
            # Get user
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                return
            
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Get resource ID from response or URL
            resource_id = self._get_resource_id(request.path, response)
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id or '',
                description=f"{action.capitalize()} {resource_type}",
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_method=request.method,
                request_path=request.path[:500],
            )
            
        except Exception as e:
            logger.error(f"Error creating audit log: {str(e)}")
    
    def _log_security_event(self, request, response):
        """Log security-related events."""
        from whatsapp_api.api.webhook_models import AuditLog
        
        try:
            user = getattr(request, 'user', None)
            
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Determine action based on status code
            if response.status_code == 403:
                action = 'permission_denied'
            elif response.status_code == 500:
                action = 'error'
            else:
                return
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action=action,
                resource_type='system',
                description=f"{action}: {request.path}",
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                request_method=request.method,
                request_path=request.path[:500],
            )
            
        except Exception as e:
            logger.error(f"Error creating security audit log: {str(e)}")
    
    def _get_resource_type(self, path):
        """Extract resource type from URL path."""
        parts = path.strip('/').split('/')
        
        # /api/v1/contacts/ -> contact
        # /api/v1/campaigns/123/ -> campaign
        if len(parts) >= 3:
            resource = parts[2]  # contacts, campaigns, etc.
            
            # Map to singular
            resource_map = {
                'contacts': 'contact',
                'templates': 'template',
                'campaigns': 'campaign',
                'scheduled': 'scheduled_message',
                'messages': 'message',
                'analytics': 'analytics',
                'billing': 'billing',
                'users': 'user',
            }
            
            return resource_map.get(resource, resource[:-1])  # Remove 's' if not in map
        
        return None
    
    def _get_resource_id(self, path, response):
        """Extract resource ID from URL or response."""
        import json
        
        parts = path.strip('/').split('/')
        
        # Check if ID is in URL
        if len(parts) >= 4 and parts[3].isdigit():
            return parts[3]
        
        # Try to get from response
        if hasattr(response, 'content'):
            try:
                data = json.loads(response.content)
                if 'id' in data:
                    return str(data['id'])
            except:
                pass
        
        return None
