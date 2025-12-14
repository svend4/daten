# ios_core/settings/sentry.py

"""
Sentry error tracking configuration
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os

def init_sentry():
    """Initialize Sentry SDK"""
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # Adjust this value in production
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        
        # Send 10% of errors for profiling
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        
        # Environment
        environment=os.environ.get('ENVIRONMENT', 'production'),
        
        # Release tracking
        release=os.environ.get('RELEASE_VERSION', 'unknown'),
        
        # Filter out certain errors
        ignore_errors=[
            'Http404',
            'PermissionDenied',
        ],
        
        # Before send callback to add custom data
        before_send=before_send_callback,
    )

def before_send_callback(event, hint):
    """
    Callback to modify events before sending to Sentry
    
    Can filter, modify, or add context to events
    """
    # Add custom tags
    if 'request' in event:
        event['tags'] = event.get('tags', {})
        event['tags']['user_agent'] = event['request'].get('headers', {}).get('User-Agent', 'unknown')
    
    # Filter out noisy errors
    if 'exception' in event:
        for exception in event['exception']['values']:
            if 'ConnectionResetError' in str(exception.get('type', '')):
                return None  # Don't send to Sentry
    
    return event