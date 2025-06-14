import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from src.config import Config
from src.user.profile_manager import UserProfileManager

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, config: Config, profile_manager: UserProfileManager):
        self.config = config
        self.profile_manager = profile_manager
        self.notifications: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        self.notification_preferences: Dict[int, Dict[str, Any]] = {}
        self.notification_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def create_notification(self,
                           user_id: int,
                           notification_type: str,
                           content: Dict[str, Any],
                           priority: str = 'normal',
                           expiry: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a new notification for a user."""
        try:
            # Check user notification preferences
            if not self._should_create_notification(user_id, notification_type):
                logger.info(f"Notification suppressed for user {user_id} due to preferences")
                return {}
            
            notification = {
                'id': self._generate_notification_id(user_id),
                'user_id': user_id,
                'type': notification_type,
                'content': content,
                'priority': priority,
                'created_at': datetime.now(),
                'expiry': expiry or (datetime.now() + timedelta(days=7)),
                'status': 'pending',
                'read_at': None,
                'action_taken': None
            }
            
            self.notifications[user_id].append(notification)
            self._update_notification_stats('created', notification_type)
            
            logger.info(f"Created {notification_type} notification for user {user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise
    
    def _should_create_notification(self, user_id: int, notification_type: str) -> bool:
        """Check if notification should be created based on user preferences."""
        try:
            # Get user preferences
            preferences = self.notification_preferences.get(user_id, {})
            
            # Check if notifications are enabled globally
            if not preferences.get('notifications_enabled', True):
                return False
            
            # Check specific notification type preference
            type_preference = preferences.get('type_preferences', {}).get(notification_type, True)
            if not type_preference:
                return False
            
            # Check frequency limits
            if self._exceeds_frequency_limit(user_id, notification_type):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification creation: {str(e)}")
            return False
    
    def _exceeds_frequency_limit(self, user_id: int, notification_type: str) -> bool:
        """Check if notification frequency limit is exceeded."""
        try:
            preferences = self.notification_preferences.get(user_id, {})
            frequency_limits = preferences.get('frequency_limits', {})
            
            if notification_type not in frequency_limits:
                return False
            
            limit = frequency_limits[notification_type]
            recent_notifications = [
                n for n in self.notifications[user_id]
                if n['type'] == notification_type and
                n['created_at'] >= datetime.now() - timedelta(days=1)
            ]
            
            return len(recent_notifications) >= limit
            
        except Exception as e:
            logger.error(f"Error checking frequency limit: {str(e)}")
            return True
    
    def _generate_notification_id(self, user_id: int) -> str:
        """Generate a unique notification ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        count = len(self.notifications[user_id])
        return f"notif_{user_id}_{timestamp}_{count}"
    
    def update_notification_preferences(self, user_id: int, preferences: Dict[str, Any]) -> None:
        """Update notification preferences for a user."""
        try:
            if user_id not in self.notification_preferences:
                self.notification_preferences[user_id] = {
                    'notifications_enabled': True,
                    'type_preferences': {},
                    'frequency_limits': {},
                    'quiet_hours': {'start': '22:00', 'end': '08:00'},
                    'channels': ['email', 'in_app']
                }
            
            # Update preferences
            user_prefs = self.notification_preferences[user_id]
            for key, value in preferences.items():
                if key in user_prefs:
                    user_prefs[key] = value
            
            logger.info(f"Updated notification preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {str(e)}")
            raise
    
    def mark_notification_read(self, user_id: int, notification_id: str) -> None:
        """Mark a notification as read."""
        try:
            notification = self._get_notification(user_id, notification_id)
            if notification and notification['status'] == 'pending':
                notification['status'] = 'read'
                notification['read_at'] = datetime.now()
                self._update_notification_stats('read', notification['type'])
                
            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise
    
    def record_notification_action(self,
                                 user_id: int,
                                 notification_id: str,
                                 action: str) -> None:
        """Record an action taken on a notification."""
        try:
            notification = self._get_notification(user_id, notification_id)
            if notification:
                notification['action_taken'] = {
                    'action': action,
                    'timestamp': datetime.now()
                }
                self._update_notification_stats('action_taken', notification['type'])
                
            logger.info(f"Recorded action {action} for notification {notification_id}")
            
        except Exception as e:
            logger.error(f"Error recording notification action: {str(e)}")
            raise
    
    def get_user_notifications(self,
                             user_id: int,
                             status: Optional[str] = None,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Get notifications for a user with optional filtering."""
        try:
            notifications = self.notifications[user_id]
            
            # Filter by status if specified
            if status:
                notifications = [n for n in notifications if n['status'] == status]
            
            # Filter out expired notifications
            current_time = datetime.now()
            notifications = [
                n for n in notifications
                if n['expiry'] > current_time
            ]
            
            # Sort by priority and creation time
            priority_weights = {'high': 3, 'normal': 2, 'low': 1}
            notifications.sort(
                key=lambda x: (priority_weights[x['priority']], x['created_at']),
                reverse=True
            )
            
            return notifications[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {str(e)}")
            raise
    
    def _get_notification(self, user_id: int, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific notification by ID."""
        try:
            for notification in self.notifications[user_id]:
                if notification['id'] == notification_id:
                    return notification
            return None
            
        except Exception as e:
            logger.error(f"Error getting notification: {str(e)}")
            raise
    
    def _update_notification_stats(self, action: str, notification_type: str) -> None:
        """Update notification statistics."""
        try:
            self.notification_stats[notification_type][action] += 1
            
        except Exception as e:
            logger.error(f"Error updating notification stats: {str(e)}")
            raise
    
    def get_notification_stats(self, time_period: str = 'all') -> Dict[str, Any]:
        """Get notification statistics for analysis."""
        try:
            stats = {
                'total_notifications': sum(
                    stats['created']
                    for stats in self.notification_stats.values()
                ),
                'read_rate': self._calculate_rate('read', 'created'),
                'action_rate': self._calculate_rate('action_taken', 'created'),
                'type_breakdown': {
                    ntype: {
                        'created': nstats['created'],
                        'read_rate': self._calculate_type_rate(ntype, 'read'),
                        'action_rate': self._calculate_type_rate(ntype, 'action_taken')
                    }
                    for ntype, nstats in self.notification_stats.items()
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            raise
    
    def _calculate_rate(self, action: str, base_action: str) -> float:
        """Calculate overall rate for an action."""
        try:
            total_base = sum(stats[base_action] for stats in self.notification_stats.values())
            total_action = sum(stats[action] for stats in self.notification_stats.values())
            
            return total_action / total_base if total_base > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating rate: {str(e)}")
            return 0
    
    def _calculate_type_rate(self, notification_type: str, action: str) -> float:
        """Calculate rate for a specific notification type."""
        try:
            stats = self.notification_stats[notification_type]
            return stats[action] / stats['created'] if stats['created'] > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating type rate: {str(e)}")
            return 0