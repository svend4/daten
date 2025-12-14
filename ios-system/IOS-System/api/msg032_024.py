"""
Dependency injection for FastAPI
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from ios_core.config import settings
from ios_core.system import IOSSystem
from .database import async_session

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_ios_system(
    db: AsyncSession = Depends(get_db)
) -> IOSSystem:
    """Get IOS System instance"""
    return IOSSystem(db_session=db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        return {"username": username}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current active user (can add more checks here)"""
    return current_user