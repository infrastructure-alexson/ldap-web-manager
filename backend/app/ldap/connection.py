#!/usr/bin/env python3
"""
LDAP Connection Manager
Handles connections to 389 Directory Service with failover support
"""

import ldap
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from app.config import get_config

logger = logging.getLogger(__name__)


class LDAPConnectionError(Exception):
    """LDAP connection error"""
    pass


class LDAPConnection:
    """
    LDAP connection manager with automatic failover
    """
    
    def __init__(self):
        self.config = get_config()
        self._connection: Optional[ldap.ldapobject.LDAPObject] = None
        self._current_server = None
        
    def connect(self) -> ldap.ldapobject.LDAPObject:
        """
        Establish connection to LDAP server with failover
        
        Returns:
            LDAP connection object
            
        Raises:
            LDAPConnectionError: If connection fails to all servers
        """
        servers = [
            self.config.ldap_primary_server,
            self.config.ldap_secondary_server
        ]
        
        last_error = None
        for server in servers:
            try:
                logger.info(f"Attempting connection to {server}")
                
                # Initialize connection
                conn = ldap.initialize(server)
                
                # Set connection options
                conn.protocol_version = ldap.VERSION3
                conn.set_option(ldap.OPT_REFERRALS, 0)
                conn.set_option(ldap.OPT_NETWORK_TIMEOUT, self.config.ldap_network_timeout)
                conn.set_option(ldap.OPT_TIMEOUT, self.config.ldap_timeout)
                
                # TLS configuration
                if server.startswith('ldaps://'):
                    if self.config.ldap_tls_verify:
                        conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
                        if self.config.ldap_tls_ca_cert:
                            conn.set_option(ldap.OPT_X_TLS_CACERTFILE, 
                                          self.config.ldap_tls_ca_cert)
                    else:
                        conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                
                # Bind with service account
                conn.simple_bind_s(
                    self.config.ldap_bind_dn,
                    self.config.ldap_bind_password
                )
                
                self._connection = conn
                self._current_server = server
                logger.info(f"Successfully connected to {server}")
                return conn
                
            except ldap.LDAPError as e:
                last_error = e
                logger.warning(f"Failed to connect to {server}: {e}")
                continue
        
        # All servers failed
        raise LDAPConnectionError(f"Failed to connect to any LDAP server: {last_error}")
    
    def get_connection(self) -> ldap.ldapobject.LDAPObject:
        """
        Get active LDAP connection, create if needed
        
        Returns:
            LDAP connection object
        """
        if self._connection is None:
            return self.connect()
        
        # Test connection
        try:
            self._connection.whoami_s()
            return self._connection
        except ldap.LDAPError:
            logger.warning("Connection lost, reconnecting...")
            return self.connect()
    
    def close(self):
        """Close LDAP connection"""
        if self._connection:
            try:
                self._connection.unbind_s()
            except ldap.LDAPError as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._connection = None
                self._current_server = None
    
    def search(
        self,
        base_dn: str,
        search_filter: str = "(objectClass=*)",
        attributes: Optional[List[str]] = None,
        scope: int = ldap.SCOPE_SUBTREE
    ) -> List[tuple]:
        """
        Search LDAP directory
        
        Args:
            base_dn: Base DN for search
            search_filter: LDAP search filter
            attributes: List of attributes to return (None = all)
            scope: Search scope
            
        Returns:
            List of (dn, attributes) tuples
        """
        conn = self.get_connection()
        try:
            result = conn.search_s(base_dn, scope, search_filter, attributes)
            return result
        except ldap.NO_SUCH_OBJECT:
            return []
        except ldap.LDAPError as e:
            logger.error(f"LDAP search error: {e}")
            raise
    
    def add(self, dn: str, attributes: Dict[str, List[bytes]]):
        """
        Add entry to LDAP
        
        Args:
            dn: Distinguished name
            attributes: Dictionary of attribute lists
        """
        conn = self.get_connection()
        # Convert dict to ldap modlist format
        modlist = [(attr, values) for attr, values in attributes.items()]
        conn.add_s(dn, modlist)
        logger.info(f"Added entry: {dn}")
    
    def modify(self, dn: str, modifications: List[tuple]):
        """
        Modify LDAP entry
        
        Args:
            dn: Distinguished name
            modifications: List of (mod_op, attribute, value) tuples
        """
        conn = self.get_connection()
        conn.modify_s(dn, modifications)
        logger.info(f"Modified entry: {dn}")
    
    def delete(self, dn: str):
        """
        Delete LDAP entry
        
        Args:
            dn: Distinguished name
        """
        conn = self.get_connection()
        conn.delete_s(dn)
        logger.info(f"Deleted entry: {dn}")
    
    def get_entry(self, dn: str, attributes: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Get a single LDAP entry by DN
        
        Args:
            dn: Distinguished name
            attributes: List of attributes to return
            
        Returns:
            Dictionary of attributes or None if not found
        """
        try:
            result = self.search(dn, "(objectClass=*)", attributes, ldap.SCOPE_BASE)
            if result:
                _, attrs = result[0]
                # Convert bytes to strings
                return {k: [v.decode('utf-8') if isinstance(v, bytes) else v 
                           for v in vals] 
                       for k, vals in attrs.items()}
            return None
        except ldap.NO_SUCH_OBJECT:
            return None


# Global connection instance
_ldap_connection: Optional[LDAPConnection] = None


def get_ldap_connection() -> LDAPConnection:
    """
    Get global LDAP connection instance
    
    Returns:
        LDAPConnection: LDAP connection manager
    """
    global _ldap_connection
    if _ldap_connection is None:
        _ldap_connection = LDAPConnection()
    return _ldap_connection


@contextmanager
def ldap_connection():
    """
    Context manager for LDAP connection
    
    Usage:
        with ldap_connection() as conn:
            conn.search(...)
    """
    conn = get_ldap_connection()
    try:
        yield conn
    finally:
        pass  # Keep connection alive for connection pooling

