#!/usr/bin/env python3
"""
JWT Authentication Module
Handles token generation, validation, and user authentication
"""

import ldap
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_config
from app.ldap.connection import get_ldap_connection
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class AuthenticationError(Exception):
    """Authentication error"""
    pass


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def authenticate_user_ldap(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user against LDAP
    
    Args:
        username: Username (uid)
        password: Password
        
    Returns:
        User information dict if authentication successful, None otherwise
    """
    config = get_config()
    ldap_conn = get_ldap_connection()
    
    try:
        # Search for user
        search_filter = f"(uid={username})"
        results = ldap_conn.search(
            config.ldap_people_ou,
            search_filter,
            attributes=['uid', 'cn', 'mail', 'memberOf']
        )
        
        if not results:
            logger.warning(f"User not found: {username}")
            return None
        
        user_dn, user_attrs = results[0]
        
        # Attempt to bind with user credentials
        conn = ldap.initialize(config.ldap_primary_server)
        conn.protocol_version = ldap.VERSION3
        
        try:
            conn.simple_bind_s(user_dn, password)
            conn.unbind_s()
        except ldap.INVALID_CREDENTIALS:
            logger.warning(f"Invalid credentials for user: {username}")
            return None
        except ldap.LDAPError as e:
            logger.error(f"LDAP error during authentication: {e}")
            return None
        
        # Extract user information
        user_info = {
            "username": user_attrs['uid'][0].decode('utf-8'),
            "dn": user_dn,
            "cn": user_attrs.get('cn', [b''])[0].decode('utf-8'),
            "email": user_attrs.get('mail', [b''])[0].decode('utf-8'),
            "groups": [g.decode('utf-8') for g in user_attrs.get('memberOf', [])]
        }
        
        # Determine role based on group membership
        user_info['role'] = determine_user_role(user_info['groups'])
        
        logger.info(f"User authenticated successfully: {username}")
        return user_info
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error: {e}")
        return None


def determine_user_role(groups: list) -> str:
    """
    Determine user role based on group membership
    
    Args:
        groups: List of group DNs
        
    Returns:
        Role string (admin, operator, readonly)
    """
    # Check for admin group
    for group in groups:
        if 'cn=ldap-admins' in group.lower():
            return 'admin'
        elif 'cn=ldap-operators' in group.lower():
            return 'operator'
    
    # Default to readonly
    return 'readonly'


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    config = get_config()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=config.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Data to encode in token
        
    Returns:
        JWT token string
    """
    config = get_config()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=config.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=config.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    config = get_config()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        "email": payload.get("email"),
        "cn": payload.get("cn")
    }


async def require_role(required_role: str):
    """
    Dependency to require specific role
    
    Args:
        required_role: Required role (admin, operator, readonly)
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)) -> Dict:
        role_hierarchy = {'admin': 3, 'operator': 2, 'readonly': 1}
        
        user_role_level = role_hierarchy.get(current_user.get('role', 'readonly'), 1)
        required_role_level = role_hierarchy.get(required_role, 3)
        
        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role('admin')
require_operator = require_role('operator')
require_readonly = require_role('readonly')

