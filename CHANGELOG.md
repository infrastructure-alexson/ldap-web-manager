# Changelog

All notable changes to LDAP Web Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-04

### Initial Release

#### Added

**Core Infrastructure**
- React 18 frontend with modern UI/UX
- FastAPI Python backend with async support
- NGINX reverse proxy configuration
- Systemd service integration
- Comprehensive deployment automation

**User & Group Management**
- LDAP user CRUD operations
- LDAP group management
- Group membership management
- Password management and policies
- Service account management
- Bulk user import/export (CSV)

**DNS Management (BIND 9)**
- Forward and reverse zone management
- DNS record management (A, AAAA, CNAME, MX, TXT, PTR, SRV, NS, SOA)
- DNSSEC support
- Dynamic DNS (DDNS) integration
- Zone import/export
- Real-time validation

**DHCP Management (Kea)**
- IPv4/IPv6 subnet management
- Dynamic address pool configuration
- Static host reservations (MAC-to-IP)
- DHCP options configuration
- Lease monitoring
- Failover status monitoring

**IPAM (IP Address Management)**
- IP pool visualization
- Subnet calculator
- IP allocation tracking
- Conflict detection
- Integration with DNS and DHCP

**Security & Authentication**
- JWT-based authentication
- Role-Based Access Control (RBAC)
- LDAPS-only connections
- Session management
- API rate limiting
- Audit logging
- Input validation and sanitization

**User Experience**
- Responsive design (desktop, tablet, mobile)
- Dark mode support
- Real-time search and filtering
- Dashboard with infrastructure overview
- Activity timeline
- Alert system

**Documentation**
- Complete installation guide
- NGINX setup documentation
- API documentation (Swagger/ReDoc)
- User guide
- Development guide

**Deployment**
- Automated deployment script
- Rocky Linux 8 support
- Systemd service files
- NGINX configuration templates
- Environment-based configuration

---

## [1.2.0] - 2025-11-04

### Added

**DNS Management**
- DNS zone CRUD API (create, read, update, delete)
- DNS record listing API
- Zone models with full SOA record support
- Automatic SOA serial number generation (YYYYMMDDnn format)
- Support for multiple record types (A, AAAA, CNAME, MX, TXT, PTR, SRV, NS)
- DNS zones page with search and pagination
- Dashboard integration showing DNS zone counts
- BIND 9 DLZ LDAP backend support

**User Management UI**
- Complete user create/edit modal
- Full form validation with error messages
- Password complexity validation (12+ chars, uppercase, lowercase, number, special)
- Client-side validation before API calls
- Permission-based action buttons
- Delete user with confirmation dialog
- Group membership display in user table
- Enhanced search and pagination

### Improved

- Dashboard now fetches real statistics for users, groups, and DNS zones
- Enhanced table layouts with better responsiveness
- Improved error handling across all pages
- Better loading states and user feedback

---

## [1.1.0] - 2025-11-04

### Added

**Groups Management**
- Full CRUD API for LDAP groups
- Group member management (add/remove members)
- Automatic GID number generation
- Groups listing page with search and pagination
- Group member count display

**Dashboard Enhancements**
- Real-time statistics (users, groups)
- Clickable stat cards linking to management pages
- Live data fetching with React Query
- Loading states for statistics

**Development Tools**
- Comprehensive development guide
- API integration examples
- Code style guidelines
- Debugging instructions

### Improved

- Frontend API client with groups support
- Error handling in API responses
- Table layouts with better responsiveness
- Search functionality across pages

---

## [Unreleased]

### Planned Features

- DNS Zone and Record Management
- DHCP Subnet and Host Management
- IP Address Management (IPAM)
- User management UI with create/edit modals
- Advanced search and filtering
- Audit log viewer
- Two-Factor Authentication (2FA)
- API Keys for programmatic access
- Advanced reporting and analytics
- LDAP schema visualization
- Backup/restore from web interface
- Multi-language support
- Email notifications
- Webhook integrations
- Template system for bulk operations
- Integration with monitoring systems (Prometheus/Grafana)

### Known Issues

- None reported

---

## Version History

- **1.0.0** (2025-11-04) - Initial release

---

## Support

For bug reports and feature requests, please visit:
https://github.com/infrastructure-alexson/ldap-web-manager/issues

