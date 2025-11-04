# Development Guide

This guide covers development setup, architecture, and contribution guidelines for LDAP Web Manager.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Backend Development](#backend-development)
- [Frontend Development](#frontend-development)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Code Style](#code-style)

---

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git
- Access to 389 DS LDAP server (for testing)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create development configuration
cp ../config/app-config.example.yaml ../config/app-config.yaml
# Edit app-config.yaml with your LDAP settings

# Set environment variables
export LDAP_WEBMANAGER_PASSWORD="your_password"
export JWT_SECRET=$(openssl rand -hex 32)
export SECRET_KEY=$(openssl rand -hex 32)

# Run development server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API documentation at: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Architecture Overview

### Backend (FastAPI)

```
backend/app/
├── api/              # API route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── users.py      # User management
│   └── groups.py     # Group management
├── auth/             # Authentication logic
│   └── jwt.py        # JWT token handling
├── ldap/             # LDAP integration
│   └── connection.py # Connection manager
├── models/           # Pydantic data models
│   ├── auth.py
│   ├── user.py
│   └── group.py
├── config.py         # Configuration management
└── main.py           # FastAPI application
```

**Key Patterns:**
- Pydantic models for validation
- Dependency injection for auth
- LDAP connection pooling
- Automatic failover to secondary LDAP

### Frontend (React)

```
frontend/src/
├── api/              # API client methods
│   ├── client.js     # Axios instance
│   ├── auth.js       # Auth API
│   ├── users.js      # Users API
│   └── groups.js     # Groups API
├── components/       # Reusable components
│   └── Layout.jsx    # Main layout
├── contexts/         # React contexts
│   └── AuthContext.jsx
├── pages/            # Page components
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── Users.jsx
│   └── Groups.jsx
└── App.jsx           # Root component
```

**Key Patterns:**
- React Query for data fetching
- Context API for global state
- Protected routes with auth
- Tailwind CSS for styling

---

## Backend Development

### Adding a New API Endpoint

1. **Create Model** (`app/models/your_model.py`):
```python
from pydantic import BaseModel

class YourModel(BaseModel):
    field: str
```

2. **Create Router** (`app/api/your_endpoint.py`):
```python
from fastapi import APIRouter, Depends
from app.auth.jwt import get_current_user

router = APIRouter()

@router.get("")
async def list_items(current_user: dict = Depends(get_current_user)):
    return {"items": []}
```

3. **Register Router** (`app/main.py`):
```python
from app.api import your_endpoint
app.include_router(your_endpoint.router, prefix="/api/your-endpoint", tags=["YourEndpoint"])
```

### LDAP Operations

```python
from app.ldap.connection import get_ldap_connection

# Get connection
ldap_conn = get_ldap_connection()

# Search
results = ldap_conn.search(
    "ou=People,dc=eh168,dc=alexson,dc=org",
    "(uid=username)",
    attributes=['cn', 'mail']
)

# Add
ldap_conn.add(dn, attributes_dict)

# Modify
ldap_conn.modify(dn, modifications_list)

# Delete
ldap_conn.delete(dn)
```

### Authentication

```python
from app.auth.jwt import require_admin, require_operator

# Require admin role
@router.delete("/{id}")
async def delete_item(id: str, current_user: dict = Depends(require_admin)):
    pass

# Require operator or higher
@router.post("")
async def create_item(data: Model, current_user: dict = Depends(require_operator)):
    pass
```

---

## Frontend Development

### Adding a New Page

1. **Create Page Component** (`src/pages/YourPage.jsx`):
```jsx
import React from 'react';

const YourPage = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold">Your Page</h1>
    </div>
  );
};

export default YourPage;
```

2. **Add Route** (`src/App.jsx`):
```jsx
import YourPage from './pages/YourPage';

// In AppRoutes component:
<Route path="your-page" element={<YourPage />} />
```

3. **Add Navigation** (`src/components/Layout.jsx`):
```jsx
{ name: 'Your Page', href: '/your-page', icon: FiIcon }
```

### API Integration

```jsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { yourApi } from '../api/your-api';

// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['your-data'],
  queryFn: () => yourApi.list(),
});

// Mutation
const mutation = useMutation({
  mutationFn: yourApi.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['your-data']);
    toast.success('Success!');
  },
});
```

### Common Patterns

**Loading State:**
```jsx
{isLoading ? (
  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
) : (
  // Content
)}
```

**Error State:**
```jsx
{error && (
  <div className="text-red-600">
    Error: {error.message}
  </div>
)}
```

**Empty State:**
```jsx
{data?.length === 0 && (
  <div className="text-center py-12 text-gray-500">
    <p>No items found</p>
  </div>
)}
```

---

## API Documentation

### Interactive API Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Testing Endpoints

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# List users
curl http://localhost:8000/api/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
pytest tests/ -v  # Verbose
pytest tests/ --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm test -- --coverage  # With coverage
```

### Integration Tests

```bash
# Run both backend and frontend
# Test full workflows in browser
```

---

## Code Style

### Python (Backend)

**Tools:**
- `black` - Code formatter
- `flake8` - Linter
- `mypy` - Type checker
- `isort` - Import sorter

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/

# Sort imports
isort app/
```

**Style Guide:**
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Max line length: 100 characters

### JavaScript/React (Frontend)

**Tools:**
- `prettier` - Code formatter
- `eslint` - Linter

```bash
# Format code
npm run format

# Lint
npm run lint
```

**Style Guide:**
- Use functional components
- Use hooks for state
- Destructure props
- Use arrow functions
- Prefer const over let

---

## Git Workflow

1. **Create Feature Branch**:
```bash
git checkout -b feature/your-feature
```

2. **Make Changes and Commit**:
```bash
git add .
git commit -m "Add your feature"
```

3. **Push and Create PR**:
```bash
git push origin feature/your-feature
# Create Pull Request on GitHub
```

### Commit Messages

Format: `<type>: <description>`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

Examples:
```
feat: Add DNS zone management API
fix: Resolve LDAP connection timeout
docs: Update installation guide
```

---

## Debugging

### Backend

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use VS Code debugger with launch.json:
{
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"]
    }
  ]
}
```

### Frontend

```javascript
// Console logging
console.log('Debug:', data);

// React DevTools (browser extension)
// Redux DevTools (for state)
```

### LDAP Debugging

```bash
# Test LDAP connection
ldapsearch -x -H ldaps://ldap1.svc.eh168.alexson.org:636 \
  -D "cn=webmanager,ou=ServiceAccounts,dc=eh168,dc=alexson,dc=org" \
  -W -b "dc=eh168,dc=alexson,dc=org" "(uid=*)"
```

---

## Performance

### Backend Optimization

- Use connection pooling
- Cache frequently accessed data
- Implement pagination
- Use async/await properly
- Profile with `cProfile`

### Frontend Optimization

- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Lazy load routes with React.lazy
- Optimize images
- Use production builds

---

## Security

### Backend Security Checklist

- [ ] Use LDAPS (TLS) for LDAP connections
- [ ] Validate all input with Pydantic
- [ ] Use JWT with expiration
- [ ] Implement rate limiting
- [ ] Hash passwords properly
- [ ] Use parameterized queries
- [ ] Sanitize LDAP filters
- [ ] Log security events

### Frontend Security Checklist

- [ ] Store tokens securely (httpOnly if possible)
- [ ] Validate user input
- [ ] Use HTTPS only
- [ ] Implement CSP headers
- [ ] Sanitize user content
- [ ] Don't expose sensitive data in client

---

## Deployment

See [INSTALLATION.md](doc/INSTALLATION.md) for production deployment.

For development deployment:

```bash
# Quick deploy to test server
./scripts/deploy-full.sh
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [389 DS Documentation](https://directory.fedoraproject.org/docs/389ds/documentation.html)
- [python-ldap Documentation](https://www.python-ldap.org/)

---

## Getting Help

- **Issues**: https://github.com/infrastructure-alexson/ldap-web-manager/issues
- **Discussions**: https://github.com/infrastructure-alexson/ldap-web-manager/discussions
- **Email**: admin@eh168.alexson.org

---

**LDAP Web Manager Development Guide**  
**Version**: 2.0.0  
**Last Updated**: November 4, 2025  
**Repository**: https://github.com/infrastructure-alexson/ldap-web-manager
