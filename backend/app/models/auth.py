#!/usr/bin/env python3
"""
Authentication models and schemas
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=3, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class UserInfo(BaseModel):
    """Current user information"""
    username: str
    cn: str
    email: str
    role: str
    permissions: list = []

