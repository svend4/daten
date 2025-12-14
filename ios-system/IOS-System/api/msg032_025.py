"""
Authentication routes
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ios_core.config import settings

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


# Temporary in-memory user storage (replace with database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin"),  # Change in production!
        "email": "admin@example.com"
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):
    """Get user by username"""
    return fake_users_db.get(username)


def authenticate_user(username: str, password: str):
    """Authenticate user"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - returns JWT token
    
    Usage:
    ```
    curl -X POST "http://localhost:8000/api/auth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=admin&password=admin"
    ```
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """
    Register new user
    
    Note: This is a simplified implementation.
    In production, add email verification, password strength checks, etc.
    """
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    hashed_password = pwd_context.hash(user.password)
    
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "email": user.email
    }
    
    return {"message": "User created successfully"}


@router.post("/logout")
async def logout():
    """
    Logout endpoint
    
    Note: With JWT, logout is typically handled client-side
    by deleting the token. For server-side logout, implement
    a token blacklist.
    """
    return {"message": "Successfully logged out"}