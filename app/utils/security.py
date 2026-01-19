#!/usr/bin/env python3
"""
Security utilities for the Research Collaboration System
"""

import secrets
import re

def generate_session_token(length=32):
    """Generate secure session token"""
    return secrets.token_urlsafe(length)

def validate_email(email):
    """Validate email format"""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_phone(phone):
    """Validate phone number"""
    return bool(re.match(r'^[\+]?[0-9\s\-\(\)]{7,15}$', phone))