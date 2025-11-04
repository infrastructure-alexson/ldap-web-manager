#!/usr/bin/env python3
"""
Authentication API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserInfo
from app.auth.jwt import (
    authenticate_user_ldap,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user
)
from app.config import get_config
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT tokens
    
    Args:
        credentials: Username and password
        
    Returns:
        Access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user_ldap(credentials.username, credentials.password)
    
    if not user:
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    config = get_config()
    token_data = {
        "sub": user['username'],
        "role": user['role'],
        "email": user.get('email', ''),
        "cn": user.get('cn', '')
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user['username']})
    
    logger.info(f"User logged in successfully: {credentials.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": config.access_token_expire_minutes * 60
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    Args:
        request: Refresh token
        
    Returns:
        New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = verify_token(request.refresh_token)
        
        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        username = payload.get("sub")
        
        # Re-authenticate to get updated user info
        # In production, you might want to cache user info
        # For now, we'll just create new tokens with existing data
        config = get_config()
        token_data = {
            "sub": username,
            "role": payload.get("role", "readonly"),
            "email": payload.get("email", ""),
            "cn": payload.get("cn", "")
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token({"sub": username})
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": config.access_token_expire_minutes * 60
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        User information
    """
    # Map role to permissions
    role_permissions = {
        'admin': ['users:*', 'groups:*', 'dns:*', 'dhcp:*', 'ipam:*', 'audit:read'],
        'operator': ['users:read', 'users:write', 'groups:read', 'groups:write',
                    'dns:read', 'dns:write', 'dhcp:read', 'dhcp:write',
                    'ipam:read', 'ipam:write'],
        'readonly': ['users:read', 'groups:read', 'dns:read', 'dhcp:read', 'ipam:read']
    }
    
    return {
        "username": current_user.get('username', ''),
        "cn": current_user.get('cn', ''),
        "email": current_user.get('email', ''),
        "role": current_user.get('role', 'readonly'),
        "permissions": role_permissions.get(current_user.get('role', 'readonly'), [])
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user
    
    Note: JWT tokens cannot be truly invalidated without a token blacklist.
    This endpoint is provided for client-side token cleanup.
    
    Args:
        current_user: Current user from JWT token
        
    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.get('username')}")
    return {"message": "Logged out successfully"}

