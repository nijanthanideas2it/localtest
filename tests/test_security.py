"""
Unit tests for security utilities.
"""
import pytest
import re
from app.core.security import SecurityUtils


class TestSecurityUtils:
    """Test cases for SecurityUtils class."""
    
    def test_generate_secure_password(self):
        """Test secure password generation."""
        password = SecurityUtils.generate_secure_password(16)
        
        assert len(password) == 16
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    def test_generate_secure_password_different_lengths(self):
        """Test password generation with different lengths."""
        for length in [8, 12, 16, 20]:
            password = SecurityUtils.generate_secure_password(length)
            assert len(password) == length
    
    def test_generate_api_key(self):
        """Test API key generation."""
        api_key = SecurityUtils.generate_api_key(32)
        
        assert len(api_key) == 32
        assert all(c.isalnum() for c in api_key)
    
    def test_generate_api_key_different_lengths(self):
        """Test API key generation with different lengths."""
        for length in [16, 24, 32, 64]:
            api_key = SecurityUtils.generate_api_key(length)
            assert len(api_key) == length
    
    def test_generate_verification_token(self):
        """Test verification token generation."""
        token = SecurityUtils.generate_verification_token()
        
        assert len(token) > 0
        # URL-safe base64 should only contain alphanumeric, '-', and '_'
        assert all(c.isalnum() or c in '-_' for c in token)
    
    def test_hash_data_with_salt(self):
        """Test data hashing with salt."""
        data = "test_data"
        hashed, salt = SecurityUtils.hash_data(data)
        
        assert len(hashed) == 64  # SHA-256 hex digest length
        assert len(salt) == 32  # 16 bytes hex encoded
        assert hashed != data
        assert salt != data
    
    def test_hash_data_with_provided_salt(self):
        """Test data hashing with provided salt."""
        data = "test_data"
        provided_salt = "test_salt"
        hashed, salt = SecurityUtils.hash_data(data, provided_salt)
        
        assert salt == provided_salt
        assert len(hashed) == 64
    
    def test_verify_hash_valid(self):
        """Test hash verification with valid data."""
        data = "test_data"
        hashed, salt = SecurityUtils.hash_data(data)
        
        assert SecurityUtils.verify_hash(data, hashed, salt) is True
    
    def test_verify_hash_invalid(self):
        """Test hash verification with invalid data."""
        data = "test_data"
        wrong_data = "wrong_data"
        hashed, salt = SecurityUtils.hash_data(data)
        
        assert SecurityUtils.verify_hash(wrong_data, hashed, salt) is False
    
    def test_sanitize_input_clean(self):
        """Test input sanitization with clean input."""
        clean_input = "This is clean text"
        sanitized = SecurityUtils.sanitize_input(clean_input)
        
        assert sanitized == clean_input
    
    def test_sanitize_input_with_dangerous_chars(self):
        """Test input sanitization with dangerous characters."""
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = SecurityUtils.sanitize_input(dangerous_input)
        
        assert "<script>" not in sanitized
        assert "javascript" not in sanitized
        assert "alert" in sanitized  # Should still be there
    
    def test_sanitize_input_empty(self):
        """Test input sanitization with empty input."""
        assert SecurityUtils.sanitize_input("") == ""
        assert SecurityUtils.sanitize_input(None) == ""
    
    def test_validate_email_format_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@numbers.com"
        ]
        
        for email in valid_emails:
            assert SecurityUtils.validate_email_format(email) is True
    
    def test_validate_email_format_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com",
            "user@example..com"
        ]
        
        for email in invalid_emails:
            assert SecurityUtils.validate_email_format(email) is False
    
    def test_rate_limit_key(self):
        """Test rate limiting key generation."""
        identifier = "192.168.1.1"
        action = "login"
        key = SecurityUtils.rate_limit_key(identifier, action)
        
        assert key == f"rate_limit:{action}:{identifier}"
    
    def test_is_password_common_true(self):
        """Test common password detection with common passwords."""
        common_passwords = [
            "password",
            "123456",
            "qwerty",
            "admin",
            "letmein"
        ]
        
        for password in common_passwords:
            assert SecurityUtils.is_password_common(password) is True
    
    def test_is_password_common_false(self):
        """Test common password detection with secure passwords."""
        secure_passwords = [
            "SecurePass123!",
            "MyComplexPassword456#",
            "RandomString789$"
        ]
        
        for password in secure_passwords:
            assert SecurityUtils.is_password_common(password) is False
    
    def test_calculate_password_entropy(self):
        """Test password entropy calculation."""
        # Test empty password
        assert SecurityUtils.calculate_password_entropy("") == 0.0
        
        # Test simple password
        simple_entropy = SecurityUtils.calculate_password_entropy("abc")
        assert simple_entropy > 0
        
        # Test complex password
        complex_entropy = SecurityUtils.calculate_password_entropy("SecurePass123!")
        assert complex_entropy > simple_entropy
    
    def test_get_password_strength_score(self):
        """Test password strength scoring."""
        # Test very weak password
        assert SecurityUtils.get_password_strength_score("123") == 0
        
        # Test weak password
        assert SecurityUtils.get_password_strength_score("password") <= 2
        
        # Test strong password
        strong_score = SecurityUtils.get_password_strength_score("SecurePass123!")
        assert strong_score >= 4
        
        # Test maximum score
        max_score = SecurityUtils.get_password_strength_score("VerySecurePassword123!@#")
        assert max_score <= 5
    
    def test_password_strength_score_common_password_penalty(self):
        """Test that common passwords get penalized in scoring."""
        # A common password with good characteristics should still get penalized
        common_but_complex = "password123"
        score = SecurityUtils.get_password_strength_score(common_but_complex)
        
        # Should be penalized for being common
        assert score < 5
    
    def test_generate_secure_password_uniqueness(self):
        """Test that generated passwords are unique."""
        passwords = set()
        for _ in range(100):
            password = SecurityUtils.generate_secure_password(16)
            passwords.add(password)
        
        # Should have generated unique passwords
        assert len(passwords) == 100
    
    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique."""
        api_keys = set()
        for _ in range(100):
            api_key = SecurityUtils.generate_api_key(32)
            api_keys.add(api_key)
        
        # Should have generated unique API keys
        assert len(api_keys) == 100
    
    def test_hash_data_deterministic(self):
        """Test that hashing with same salt produces same result."""
        data = "test_data"
        salt = "test_salt"
        
        hash1, salt1 = SecurityUtils.hash_data(data, salt)
        hash2, salt2 = SecurityUtils.hash_data(data, salt)
        
        assert hash1 == hash2
        assert salt1 == salt2 == salt
    
    def test_hash_data_different_salts(self):
        """Test that different salts produce different hashes."""
        data = "test_data"
        
        hash1, salt1 = SecurityUtils.hash_data(data)
        hash2, salt2 = SecurityUtils.hash_data(data)
        
        # Should have different salts and hashes
        assert salt1 != salt2
        assert hash1 != hash2
    
    def test_sanitize_input_complex(self):
        """Test sanitization with complex dangerous input."""
        complex_input = '<script>alert("XSS");</script><img src="javascript:alert(1)">'
        sanitized = SecurityUtils.sanitize_input(complex_input)
        
        assert "<script>" not in sanitized
        assert "javascript:" not in sanitized
        assert "alert" in sanitized  # Should still be there
    
    def test_validate_email_format_edge_cases(self):
        """Test email validation with edge cases."""
        edge_cases = [
            "a@b.c",  # Very short but valid
            "user@domain-with-dash.com",  # Domain with dash
            "user@domain.co.uk",  # Multi-level domain
            "user+tag@example.com",  # Plus addressing
            "user.name@example.com",  # Dot in local part
        ]
        
        for email in edge_cases:
            assert SecurityUtils.validate_email_format(email) is True 