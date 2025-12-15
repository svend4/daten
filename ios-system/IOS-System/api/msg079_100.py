"""
OAuth Authentication Routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ios_core.integrations.oauth import (
    GoogleOAuth,
    MicrosoftOAuth,
    GitHubOAuth
)
from ios_core.config import settings
from ios_core.security.jwt import create_access_token
from ..dependencies import get_current_user

router = APIRouter()


# Initialize OAuth providers
google_oauth = GoogleOAuth(
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    redirect_uri=f"{settings.app_url}/api/auth/google/callback"
)

microsoft_oauth = MicrosoftOAuth(
    client_id=settings.microsoft_client_id,
    client_secret=settings.microsoft_client_secret,
    redirect_uri=f"{settings.app_url}/api/auth/microsoft/callback"
)

github_oauth = GitHubOAuth(
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    redirect_uri=f"{settings.app_url}/api/auth/github/callback"
)


@router.get("/auth/google")
async def google_login():
    """
    Initiate Google OAuth flow
    
    Redirects user to Google login page.
    """
    
    state = google_oauth.generate_state()
    url = google_oauth.get_authorization_url(state)
    
    # In production, store state in session/redis
    # For now, just redirect
    
    return RedirectResponse(url)


@router.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: Optional[str] = None
):
    """
    Google OAuth callback
    
    Handles redirect from Google after user authorization.
    """
    
    try:
        # Exchange code for token
        tokens = await google_oauth.exchange_code(code)
        
        # Get user info
        user_info = await google_oauth.get_user_info(
            tokens['access_token']
        )
        
        # Create or update user in database
        # For now, just create JWT token
        
        access_token = create_access_token(
            data={
                "user_id": user_info["provider_id"],
                "email": user_info["email"],
                "provider": "google"
            }
        )
        
        # Redirect to frontend with token
        return RedirectResponse(
            f"{settings.frontend_url}/auth/success?token={access_token}"
        )
        
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")


@router.get("/auth/microsoft")
async def microsoft_login():
    """Initiate Microsoft OAuth flow"""
    
    state = microsoft_oauth.generate_state()
    url = microsoft_oauth.get_authorization_url(state)
    
    return RedirectResponse(url)


@router.get("/auth/microsoft/callback")
async def microsoft_callback(code: str, state: Optional[str] = None):
    """Microsoft OAuth callback"""
    
    try:
        tokens = await microsoft_oauth.exchange_code(code)
        user_info = await microsoft_oauth.get_user_info(tokens['access_token'])
        
        access_token = create_access_token(
            data={
                "user_id": user_info["provider_id"],
                "email": user_info["email"],
                "provider": "microsoft"
            }
        )
        
        return RedirectResponse(
            f"{settings.frontend_url}/auth/success?token={access_token}"
        )
        
    except Exception as e:
        logger.error(f"Microsoft OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")


@router.get("/auth/github")
async def github_login():
    """Initiate GitHub OAuth flow"""
    
    state = github_oauth.generate_state()
    url = github_oauth.get_authorization_url(state)
    
    return RedirectResponse(url)


@router.get("/auth/github/callback")
async def github_callback(code: str, state: Optional[str] = None):
    """GitHub OAuth callback"""
    
    try:
        tokens = await github_oauth.exchange_code(code)
        user_info = await github_oauth.get_user_info(tokens['access_token'])
        
        access_token = create_access_token(
            data={
                "user_id": user_info["provider_id"],
                "email": user_info["email"],
                "provider": "github"
            }
        )
        
        return RedirectResponse(
            f"{settings.frontend_url}/auth/success?token={access_token}"
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth error: {e}")
        raise HTTPException(500, "OAuth authentication failed")