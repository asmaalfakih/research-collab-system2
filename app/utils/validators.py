import re
from typing import Dict, List, Any, Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    pattern = r'^[\+]?[0-9\s\-\(\)]{8,20}$'
    return bool(re.match(pattern, phone))

def validate_date(date_str: str, format: str = '%Y-%m-%d') -> bool:
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_year(year: int) -> bool:
    current_year = datetime.now().year
    return 1900 <= year <= current_year + 1

def validate_password(password: str) -> List[str]:
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    return errors

def validate_researcher_data(data: Dict[str, Any]) -> List[str]:
    errors = []

    if 'name' not in data or not data['name'].strip():
        errors.append("Name is required")
    elif len(data['name'].strip()) < 2:
        errors.append("Name must be at least 2 characters")

    if 'email' not in data or not data['email']:
        errors.append("Email is required")
    elif not validate_email(data['email']):
        errors.append("Invalid email format")

    if 'department' not in data or not data['department'].strip():
        errors.append("Department is required")

    if 'password' in data:
        password_errors = validate_password(data['password'])
        errors.extend(password_errors)

    if 'research_interests' in data and not isinstance(data['research_interests'], list):
        errors.append("Research interests must be a list")

    return errors

def validate_project_data(data: Dict[str, Any]) -> List[str]:
    errors = []

    if 'title' not in data or not data['title'].strip():
        errors.append("Project title is required")
    elif len(data['title'].strip()) < 3:
        errors.append("Project title must be at least 3 characters")

    if 'description' not in data or not data['description'].strip():
        errors.append("Project description is required")
    elif len(data['description'].strip()) < 10:
        errors.append("Project description must be at least 10 characters")

    if 'creator_id' not in data or not data['creator_id']:
        errors.append("Creator ID is required")

    if 'start_date' in data and data['start_date']:
        if not validate_date(data['start_date']):
            errors.append("Invalid start date format (YYYY-MM-DD)")

    if 'end_date' in data and data['end_date']:
        if not validate_date(data['end_date']):
            errors.append("Invalid end date format (YYYY-MM-DD)")
        elif 'start_date' in data and data['start_date']:
            if data['end_date'] < data['start_date']:
                errors.append("End date cannot be before start date")

    if 'status' in data and data['status']:
        valid_statuses = ['active', 'completed', 'pending', 'cancelled']
        if data['status'] not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")

    return errors

def validate_publication_data(data: Dict[str, Any]) -> List[str]:
    errors = []

    if 'title' not in data or not data['title'].strip():
        errors.append("Publication title is required")
    elif len(data['title'].strip()) < 5:
        errors.append("Publication title must be at least 5 characters")

    if 'authors' not in data or not data['authors']:
        errors.append("At least one author is required")
    elif not isinstance(data['authors'], list) or len(data['authors']) == 0:
        errors.append("Authors must be a non-empty list")
    else:
        for i, author in enumerate(data['authors']):
            if not isinstance(author, dict):
                errors.append(f"Author {i + 1} must be a dictionary")
            elif 'researcher_id' not in author or not author['researcher_id']:
                errors.append(f"Author {i + 1} missing researcher ID")
            elif 'name' not in author or not author['name'].strip():
                errors.append(f"Author {i + 1} missing name")

    if 'year' not in data or not data['year']:
        errors.append("Publication year is required")
    elif not validate_year(data['year']):
        errors.append("Invalid publication year")

    if 'doi' in data and data['doi']:
        if not data['doi'].startswith('10.'):
            errors.append("DOI should start with '10.'")

    if 'status' in data and data['status']:
        valid_statuses = ['published', 'submitted', 'accepted', 'rejected']
        if data['status'] not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")

    return errors

def sanitize_input(text: str) -> str:
    if not text:
        return text

    text = ' '.join(text.split())

    dangerous_chars = ['<', '>', ';', '|', '&', '$']
    for char in dangerous_chars:
        text = text.replace(char, '')

    return text.strip()

def validate_list_input(input_str: str, min_items: int = 1, max_items: int = 10) -> List[str]:
    if not input_str:
        return []

    items = [item.strip() for item in input_str.split(',') if item.strip()]

    if len(items) < min_items:
        raise ValueError(f"At least {min_items} item(s) required")

    if len(items) > max_items:
        raise ValueError(f"Maximum {max_items} items allowed")

    return items

def validate_numeric_range(value: Any, min_val: float, max_val: float) -> bool:
    try:
        num = float(value)
        return min_val <= num <= max_val
    except (ValueError, TypeError):
        return False