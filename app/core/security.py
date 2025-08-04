"""
Additional security utilities for the application.
"""
import secrets
import string
from typing import Optional
from datetime import datetime, timedelta, timezone
import hashlib
import hmac


class SecurityUtils:
    """Additional security utilities for the application."""
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Length of the password to generate
            
        Returns:
            A secure random password
        """
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special_chars)
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = lowercase + uppercase + digits + special_chars
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password
        password_list = list(password)
        secrets.SystemRandom().shuffle(password_list)
        
        return ''.join(password_list)
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """
        Generate a secure API key.
        
        Args:
            length: Length of the API key
            
        Returns:
            A secure API key
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate a secure verification token for email verification, password reset, etc.
        
        Returns:
            A secure verification token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash data with a salt using SHA-256.
        
        Args:
            data: Data to hash
            salt: Optional salt (if not provided, one will be generated)
            
        Returns:
            Tuple of (hashed_data, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Combine data and salt
        combined = f"{data}:{salt}".encode('utf-8')
        
        # Hash using SHA-256
        hashed = hashlib.sha256(combined).hexdigest()
        
        return hashed, salt
    
    @staticmethod
    def verify_hash(data: str, hashed_data: str, salt: str) -> bool:
        """
        Verify hashed data against original data.
        
        Args:
            data: Original data
            hashed_data: Hashed data to verify against
            salt: Salt used for hashing
            
        Returns:
            True if data matches, False otherwise
        """
        expected_hash, _ = SecurityUtils.hash_data(data, salt)
        return hmac.compare_digest(expected_hash, hashed_data)
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """
        Basic input sanitization to prevent XSS attacks.
        
        Args:
            input_string: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        if not input_string:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', 'script', 'javascript']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """
        Validate email format using basic regex pattern.
        
        Args:
            email: Email to validate
            
        Returns:
            True if email format is valid, False otherwise
        """
        import re
        
        # More comprehensive email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+$'
        
        # Additional checks for common invalid patterns
        if not email or '@' not in email:
            return False
        
        # Check for consecutive dots
        if '..' in email:
            return False
        
        # Check for valid domain structure
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local_part, domain = parts
        
        # Local part cannot be empty
        if not local_part:
            return False
        
        # Domain must have at least one dot
        if '.' not in domain:
            return False
        
        return bool(re.match(pattern, email))
    
    @staticmethod
    def rate_limit_key(identifier: str, action: str) -> str:
        """
        Generate a rate limiting key for tracking requests.
        
        Args:
            identifier: User identifier (IP, user ID, etc.)
            action: Action being rate limited
            
        Returns:
            Rate limiting key
        """
        return f"rate_limit:{action}:{identifier}"
    
    @staticmethod
    def is_password_common(password: str) -> bool:
        """
        Check if password is in a list of common passwords.
        This is a basic implementation - in production, use a comprehensive database.
        
        Args:
            password: Password to check
            
        Returns:
            True if password is common, False otherwise
        """
        common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            'dragon', 'master', 'sunshine', 'princess', 'shadow',
            'football', 'baseball', 'superman', 'batman', 'spider'
        }
        
        return password.lower() in common_passwords
    
    @staticmethod
    def calculate_password_entropy(password: str) -> float:
        """
        Calculate password entropy (measure of randomness).
        
        Args:
            password: Password to analyze
            
        Returns:
            Entropy value (higher is better)
        """
        if not password:
            return 0.0
        
        # Count character sets used
        char_sets = 0
        if any(c.islower() for c in password):
            char_sets += 26
        if any(c.isupper() for c in password):
            char_sets += 26
        if any(c.isdigit() for c in password):
            char_sets += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            char_sets += 32
        
        # Calculate entropy
        entropy = len(password) * (char_sets ** 0.5)
        return entropy
    
    @staticmethod
    def get_password_strength_score(password: str) -> int:
        """
        Get a password strength score from 0-5.
        
        Args:
            password: Password to score
            
        Returns:
            Strength score (0-5, where 5 is strongest)
        """
        score = 0
        
        # Length check
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        if any(c.islower() for c in password):
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        # Penalty for common passwords
        if SecurityUtils.is_password_common(password):
            score = max(0, score - 2)
        
        # Additional penalty for very short passwords
        if len(password) < 4:
            score = 0
        
        return min(5, score) 
