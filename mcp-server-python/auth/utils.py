import os
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a stored password against one provided by user."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(email: str) -> str:
        """Create JWT access token."""
        current_time = int(time.time() * 1000)  # Current timestamp in epoch milliseconds
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        payload = {
            "email": email,
            "timestamp": current_time,
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT access token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def extract_token_from_cookies(cookies: str) -> Optional[str]:
        """Extract token from cookies."""
        if not cookies:
            return None
        
        # Parse cookies manually - cookies are in format "name=value; name2=value2"
        cookie_pairs = cookies.split(';')
        for pair in cookie_pairs:
            if '=' in pair:
                name, value = pair.strip().split('=', 1)
                if name == 'access_token':
                    return value
        
        return None
