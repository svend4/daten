"""
External Integrations Module
"""

from .slack import SlackIntegration, slack_integration
from .email import EmailIntegration, email_integration
from .oauth import OAuthProvider, GoogleOAuth, MicrosoftOAuth, GitHubOAuth

__all__ = [
    'SlackIntegration',
    'slack_integration',
    'EmailIntegration',
    'email_integration',
    'OAuthProvider',
    'GoogleOAuth',
    'MicrosoftOAuth',
    'GitHubOAuth',
]