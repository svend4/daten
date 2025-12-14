"""
OAuth 2.0 Providers
Integration with Google, Microsoft, GitHub
"""

import logging
from typing import Optional, Dict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import secrets

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class OAuthProvider(ABC):
    """
    Base OAuth 2.0 provider
    
    Implements OAuth 2.0 authorization code flow
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    @abstractmethod
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get OAuth authorization URL"""
        pass
    
    @abstractmethod
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information"""
        pass
    
    def generate_state(self) -> str:
        """Generate state parameter for CSRF protection"""
        return secrets.token_urlsafe(32)


class GoogleOAuth(OAuthProvider):
    """
    Google OAuth 2.0 provider
    
    Scopes:
    - openid: User ID
    - email: User email
    - profile: User profile info
    
    Usage:
        oauth = GoogleOAuth(
            client_id="...",
            client_secret="...",
            redirect_uri="https://app.com/auth/google/callback"
        )
        
        # Generate authorization URL
        state = oauth.generate_state()
        url = oauth.get_authorization_url(state)
        
        # Exchange code for token
        tokens = await oauth.exchange_code(code)
        
        # Get user info
        user = await oauth.get_user_info(tokens['access_token'])
    """
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    SCOPES = ["openid", "email", "profile"]
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL"""
        
        if not state:
            state = self.generate_state()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent"
        }
        
        query_string = "&".join(
            f"{k}={v}" for k, v in params.items()
        )
        
        return f"{self.AUTH_URL}?{query_string}"
    
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get Google user information"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "provider": "google",
                "provider_id": data["id"],
                "email": data["email"],
                "name": data.get("name"),
                "picture": data.get("picture"),
                "email_verified": data.get("email_verified", False)
            }


class MicrosoftOAuth(OAuthProvider):
    """
    Microsoft OAuth 2.0 provider
    
    Scopes:
    - openid: User ID
    - email: User email
    - profile: User profile
    
    Usage:
        oauth = MicrosoftOAuth(
            client_id="...",
            client_secret="...",
            redirect_uri="https://app.com/auth/microsoft/callback"
        )
    """
    
    AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"
    
    SCOPES = ["openid", "email", "profile"]
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Microsoft OAuth authorization URL"""
        
        if not state:
            state = self.generate_state()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "response_mode": "query"
        }
        
        query_string = "&".join(
            f"{k}={v}" for k, v in params.items()
        )
        
        return f"{self.AUTH_URL}?{query_string}"
    
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            response.raise_for_status()
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get Microsoft user information"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USER_INFO_URL,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "provider": "microsoft",
                "provider_id": data["id"],
                "email": data.get("mail") or data.get("userPrincipalName"),
                "name": data.get("displayName"),
                "email_verified": True  # Microsoft verifies emails
            }


class GitHubOAuth(OAuthProvider):
    """
    GitHub OAuth 2.0 provider
    
    Scopes:
    - user:email: User email
    
    Usage:
        oauth = GitHubOAuth(
            client_id="...",
            client_secret="...",
            redirect_uri="https://app.com/auth/github/callback"
        )
    """
    
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_INFO_URL = "https://api.github.com/user"
    USER_EMAIL_URL = "https://api.github.com/user/emails"
    
    SCOPES = ["user:email"]
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get GitHub OAuth authorization URL"""
        
        if not state:
            state = self.generate_state()
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.SCOPES),
            "state": state
        }
        
        query_string = "&".join(
            f"{k}={v}" for k, v in params.items()
        )
        
        return f"{self.AUTH_URL}?{query_string}"
    
    async def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {"Accept": "application/json"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get GitHub user information"""
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                self.USER_INFO_URL,
                headers=headers
            )
            response.raise_for_status()
            user_data = response.json()
            
            # Get user emails
            response = await client.get(
                self.USER_EMAIL_URL,
                headers=headers
            )
            response.raise_for_status()
            emails = response.json()
            
            # Find primary email
            primary_email = next(
                (e for e in emails if e.get("primary")),
                emails[0] if emails else None
            )
            
            return {
                "provider": "github",
                "provider_id": str(user_data["id"]),
                "email": primary_email["email"] if primary_email else None,
                "name": user_data.get("name"),
                "username": user_data.get("login"),
                "picture": user_data.get("avatar_url"),
                "email_verified": primary_email.get("verified", False)
                    if primary_email else False
            }