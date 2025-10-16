# MCP Server Authentication System

This document describes the authentication system for the MCP Server, including signup, signin, signout, and protected endpoints.

## Overview

The authentication system provides:
- JWT-based authentication with Bearer tokens
- HTTP-only cookies for secure token storage
- User signup and signin endpoints
- Protected endpoints with middleware authentication
- PostgreSQL database with user management

## API Endpoints

All authentication endpoints are prefixed with `/api/v1/`

### 1. User Signup
**POST** `/api/v1/signup`

Register a new user account.

```bash
curl -X POST http://localhost:8000/api/v1/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2025-09-28T15:30:00Z",
  "updated_at": "2025-09-28T15:30:00Z"
}
```

**Error (400 Bad Request):**
```json
{
  "detail": "Email already registered"
}
```

### 2. User Signin
**POST** `/api/v1/signin`

Authenticate user and receive access token.

```bash
curl -X POST http://localhost:8000/api/v1/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Features:**
- Sets HTTP-only cookie with `secure=true` and `samesite=strict`
- Cookie expires in 24 hours
- Returns JWT token for Authorization header use

**Error (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

### 3. User Signout
**POST** `/api/v1/signout`

Sign out user by clearing authentication cookie.

```bash
curl -X POST http://localhost:8000/api/v1/signout
```

**Response (200 OK):**
```json
{
  "message": "Successfully signed out"
}
```

### 4. Get Current User
**GET** `/api/v1/me`

Get information about the currently authenticated user. **Requires authentication.**

```bash
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2025-09-28T15:30:00Z",
  "updated_at": "2025-09-28T15:30:00Z"
}
```

**Error (401 Unauthorized):**
```json
{
  "detail": "Authorization token required"
}
```

## JWT Token Format

JWT tokens contain the following payload:

```json
{
  "email": "user@example.com",
  "timestamp": 1727542800000,
  "exp": 1727629200,
  "iat": 1727542800
}
```

- `email`: User's email address
- `timestamp`: Token creation time in epoch milliseconds
- `exp`: Token expiration time (24 hours from creation)
- `iat`: Token issued at time

## Authentication Middleware

The `AuthMiddleware` automatically protects all `/api/v1/` endpoints except:
- `/api/v1/signup`
- `/api/v1/signin` 
- `/api/v1/signout`
- `/checks` (health check)

Protected endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Environment Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/mcp_server

# JWT Configuration  
JWT_SECRET=your-super-secret-jwt-key-change-in-production
```

**Important:** Change the `JWT_SECRET` to a secure random string in production!

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env with your database credentials and JWT secret
   ```

3. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

5. **Test the authentication endpoints:**
   ```bash
   python test_auth_api.py
   ```

## Security Features

- **Password Hashing:** Uses bcrypt with salts
- **JWT Security:** HS256 algorithm with configurable secret
- **HTTP-Only Cookies:** Prevents XSS attacks
- **Secure Cookies:** Only sent over HTTPS in production
- **SameSite Protection:** Prevents CSRF attacks
- **Token Expiration:** 24-hour token lifetime
- **Input Validation:** Email format and password length validation

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Authentication required or invalid credentials
- `404 Not Found` - Endpoint not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server errors

Error responses follow this format:
```json
{
  "detail": "Error description"
}
```

## Testing

Use the provided test script to verify all authentication endpoints:

```bash
python test_auth_api.py
```

This will test:
- User signup
- User signin (with cookie and token)
- Protected endpoint access
- User signout
- Unauthorized access rejection
