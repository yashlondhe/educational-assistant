"""
Authentication module for user login, registration, and session management.
"""

import hashlib
import secrets
import re
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging

from database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class AuthManager:
    """Handles user authentication and session management."""
    
    def __init__(self, db: Database = None):
        """Initialize authentication manager."""
        self.db = db or Database()
        self.session_duration = timedelta(hours=24)  # Sessions last 24 hours
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        # In production, use bcrypt or argon2
        # For now, using SHA-256 with salt
        salt = "educational_assistant_salt_2024"  # In production, use random salt per user
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength.
        Returns (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        # Add more validation rules as needed
        # if not re.search(r'[A-Z]', password):
        #     return False, "Password must contain at least one uppercase letter"
        # if not re.search(r'[0-9]', password):
        #     return False, "Password must contain at least one number"
        
        return True, ""
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return True  # Phone is optional
        # Remove spaces and dashes
        phone_digits = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it's a valid phone number (10-12 digits)
        return re.match(r'^\+?\d{10,12}$', phone_digits) is not None
    
    def register_user(self, email: str, password: str, name: str, class_grade: str,
                     date_of_birth: str = None, phone_number: str = None) -> Dict:
        """
        Register a new user with profile.
        Returns user info on success, raises AuthenticationError on failure.
        """
        # Validate inputs
        if not self.validate_email(email):
            raise AuthenticationError("Invalid email format")
        
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        if not name or len(name.strip()) < 2:
            raise AuthenticationError("Name must be at least 2 characters long")
        
        if not self.validate_phone(phone_number):
            raise AuthenticationError("Invalid phone number format")
        
        # Validate class grade
        valid_classes = [f"class{i}" for i in range(1, 11)]
        if class_grade.lower() not in valid_classes:
            raise AuthenticationError(f"Invalid class. Must be one of: {', '.join(valid_classes)}")
        
        # Check if email already exists
        existing_user = self.db.get_user_by_email(email)
        if existing_user:
            raise AuthenticationError("Email already registered")
        
        try:
            # Create user
            password_hash = self.hash_password(password)
            user_id = self.db.create_user(email, password_hash)
            
            # Create profile
            profile_id = self.db.create_user_profile(
                user_id=user_id,
                name=name,
                class_grade=class_grade,
                date_of_birth=date_of_birth,
                phone_number=phone_number
            )
            
            # Update last login
            self.db.update_last_login(user_id)
            
            return {
                'user_id': user_id,
                'email': email,
                'name': name,
                'class_grade': class_grade
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise AuthenticationError(f"Registration failed: {str(e)}")
    
    def login(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user login.
        Returns user info on success, None on failure.
        """
        if not email or not password:
            return None
        
        # Get user by email
        user = self.db.get_user_by_email(email)
        if not user:
            return None
        
        # Verify password
        password_hash = self.hash_password(password)
        if user['password_hash'] != password_hash:
            return None
        
        # Update last login
        self.db.update_last_login(user['id'])
        
        # Get user profile
        profile = self.db.get_user_profile(user['id'])
        if not profile:
            logger.error(f"User {user['id']} has no profile")
            return None
        
        return {
            'user_id': user['id'],
            'email': user['email'],
            'name': profile['name'],
            'class_grade': profile['class_grade'],
            'profile': profile
        }
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information including profile."""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        
        profile = self.db.get_user_profile(user_id)
        if not profile:
            return None
        
        return {
            'user_id': user['id'],
            'email': user['email'],
            'name': profile['name'],
            'class_grade': profile['class_grade'],
            'date_of_birth': profile['date_of_birth'],
            'phone_number': profile['phone_number'],
            'created_at': user['created_at'],
            'last_login': user['last_login']
        }
    
    def update_profile(self, user_id: int, **kwargs) -> bool:
        """Update user profile information."""
        # Validate inputs if provided
        if 'email' in kwargs:
            # Email update not implemented in this version
            raise AuthenticationError("Email update not supported")
        
        if 'name' in kwargs and len(kwargs['name'].strip()) < 2:
            raise AuthenticationError("Name must be at least 2 characters long")
        
        if 'phone_number' in kwargs and not self.validate_phone(kwargs['phone_number']):
            raise AuthenticationError("Invalid phone number format")
        
        if 'class_grade' in kwargs:
            valid_classes = [f"class{i}" for i in range(1, 11)]
            if kwargs['class_grade'].lower() not in valid_classes:
                raise AuthenticationError(f"Invalid class. Must be one of: {', '.join(valid_classes)}")
        
        try:
            # Update profile
            rows_affected = self.db.update_user_profile(user_id, **kwargs)
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            raise AuthenticationError(f"Profile update failed: {str(e)}")
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password."""
        # Get user
        user = self.db.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Verify old password
        old_password_hash = self.hash_password(old_password)
        if user['password_hash'] != old_password_hash:
            raise AuthenticationError("Incorrect current password")
        
        # Validate new password
        is_valid, error_msg = self.validate_password(new_password)
        if not is_valid:
            raise AuthenticationError(error_msg)
        
        # Update password
        new_password_hash = self.hash_password(new_password)
        query = "UPDATE users SET password_hash = ? WHERE id = ?"
        rows_affected = self.db.execute_update(query, (new_password_hash, user_id))
        
        return rows_affected > 0
    
    def generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)
    
    def validate_session(self, session_token: str, user_id: int) -> bool:
        """
        Validate session token.
        In a real implementation, this would check against a sessions table.
        """
        # For now, we'll use Streamlit's session state
        # In production, implement proper session management with expiration
        return True
