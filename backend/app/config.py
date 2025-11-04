#!/usr/bin/env python3
"""
Configuration management for LDAP Web Manager
Loads settings from YAML configuration file and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Application configuration"""
    
    # Application settings
    app_name: str = "LDAP Web Manager"
    environment: str = "production"
    debug: bool = False
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # LDAP Configuration
    ldap_primary_server: str = Field(..., env="LDAP_PRIMARY_SERVER")
    ldap_secondary_server: str = Field(..., env="LDAP_SECONDARY_SERVER")
    ldap_base_dn: str = Field(..., env="LDAP_BASE_DN")
    ldap_bind_dn: str = Field(..., env="LDAP_BIND_DN")
    ldap_bind_password: str = Field(..., env="LDAP_WEBMANAGER_PASSWORD")
    
    # LDAP OUs
    ldap_people_ou: str = Field(..., env="LDAP_PEOPLE_OU")
    ldap_groups_ou: str = Field(..., env="LDAP_GROUPS_OU")
    ldap_service_accounts_ou: str = Field(..., env="LDAP_SERVICE_ACCOUNTS_OU")
    ldap_dns_ou: str = Field(..., env="LDAP_DNS_OU")
    ldap_dhcp_ou: str = Field(..., env="LDAP_DHCP_OU")
    
    # LDAP connection settings
    ldap_timeout: int = 30
    ldap_network_timeout: int = 10
    ldap_pool_size: int = 10
    ldap_tls_verify: bool = True
    ldap_tls_ca_cert: Optional[str] = "/etc/pki/tls/certs/ca-bundle.crt"
    
    # Authentication
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    
    # Database (for audit logs)
    database_url: str = "sqlite:///var/lib/ldap-web-manager/audit.db"
    
    # Audit logging
    audit_enabled: bool = True
    audit_retention_days: int = 365
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 100
    
    # CORS
    cors_origins: List[str] = [
        "https://ldap-manager.svc.eh168.alexson.org",
        "http://localhost:5173"
    ]
    
    # Feature flags
    feature_user_management: bool = True
    feature_group_management: bool = True
    feature_dns_management: bool = True
    feature_dhcp_management: bool = True
    feature_ipam: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
_config: Optional[Config] = None


def load_config(config_file: Optional[Path] = None) -> Config:
    """
    Load configuration from YAML file and environment variables
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        Config: Configuration object
    """
    global _config
    
    if _config is not None:
        return _config
    
    # Default config file path
    if config_file is None:
        config_file = Path(__file__).parent.parent.parent / "config" / "app-config.yaml"
    
    # Load YAML configuration
    config_data = {}
    if config_file.exists():
        with open(config_file, 'r') as f:
            yaml_data = yaml.safe_load(f)
            
            # Flatten nested YAML structure for environment variables
            if yaml_data:
                # Map YAML structure to flat environment variables
                if 'ldap' in yaml_data:
                    ldap_config = yaml_data['ldap']
                    if 'servers' in ldap_config:
                        os.environ.setdefault('LDAP_PRIMARY_SERVER', 
                                            ldap_config['servers'].get('primary', ''))
                        os.environ.setdefault('LDAP_SECONDARY_SERVER', 
                                            ldap_config['servers'].get('secondary', ''))
                    
                    os.environ.setdefault('LDAP_BASE_DN', ldap_config.get('base_dn', ''))
                    os.environ.setdefault('LDAP_BIND_DN', ldap_config.get('bind_dn', ''))
                    os.environ.setdefault('LDAP_PEOPLE_OU', ldap_config.get('people_ou', ''))
                    os.environ.setdefault('LDAP_GROUPS_OU', ldap_config.get('groups_ou', ''))
                    os.environ.setdefault('LDAP_SERVICE_ACCOUNTS_OU', 
                                        ldap_config.get('service_accounts_ou', ''))
                    os.environ.setdefault('LDAP_DNS_OU', ldap_config.get('dns_ou', ''))
                    os.environ.setdefault('LDAP_DHCP_OU', ldap_config.get('dhcp_ou', ''))
    
    # Create config from environment variables
    _config = Config()
    return _config


def get_config() -> Config:
    """
    Get the global configuration instance
    
    Returns:
        Config: Configuration object
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config

