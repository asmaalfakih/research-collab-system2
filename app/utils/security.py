
import secrets
import re

def generate_session_token(length=32):
    return secrets.token_urlsafe(length)

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_phone(phone):
    return bool(re.match(r'^[\+]?[0-9\s\-\(\)]{7,15}$', phone))