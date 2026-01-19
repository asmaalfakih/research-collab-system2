from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from colorama import Fore, Style
import math
import uuid
import time


class Helpers:
    """General helper functions"""

    @staticmethod
    def format_timestamp(timestamp) -> str:
        """Format timestamp"""
        if not timestamp:
            return "N/A"

        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return timestamp

        if isinstance(timestamp, datetime):
            now = datetime.utcnow()
            diff = now - timestamp

            if diff < timedelta(minutes=1):
                return "Just now"
            elif diff < timedelta(hours=1):
                minutes = int(diff.seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff < timedelta(days=1):
                hours = int(diff.seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff < timedelta(days=7):
                days = diff.days
                return f"{days} day{'s' if days != 1 else ''} ago"
            else:
                return timestamp.strftime("%Y-%m-%d %H:%M")

        return str(timestamp)

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration"""
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"

    @staticmethod
    def paginate_items(items: List, page: int, per_page: int) -> Dict[str, Any]:
        """Paginate items"""
        if not items:
            return {
                'items': [],
                'page': page,
                'per_page': per_page,
                'total': 0,
                'pages': 0,
                'has_next': False,
                'has_prev': False
            }

        total = len(items)
        pages = math.ceil(total / per_page)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'items': items[start:end],
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'has_next': page < pages,
            'has_prev': page > 1
        }

    @staticmethod
    def calculate_percentage(part: int, whole: int) -> float:
        """Calculate percentage"""
        if whole == 0:
            return 0.0
        return (part / whole) * 100

    @staticmethod
    def generate_progress_bar(percentage: float, width: int = 20) -> str:
        """Generate progress bar"""
        filled = int((percentage / 100) * width)
        empty = width - filled

        bar = '█' * filled + '░' * empty
        return f"{bar} {percentage:.1f}%"

    @staticmethod
    def colorize_status(status: str) -> str:
        """Colorize status"""
        status_colors = {
            'approved': Fore.GREEN,
            'pending': Fore.YELLOW,
            'rejected': Fore.RED,
            'active': Fore.GREEN,
            'completed': Fore.BLUE,
            'cancelled': Fore.RED,
            'published': Fore.GREEN,
            'submitted': Fore.YELLOW,
            'deleted': Fore.RED
        }

        color = status_colors.get(status.lower(), Fore.WHITE)
        return f"{color}{status}{Style.RESET_ALL}"

    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """Truncate text"""
        if len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def generate_id(prefix: str = "ID") -> str:
        """Generate unique ID"""
        timestamp = int(time.time() * 1000)
        unique_part = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_part}"

    @staticmethod
    def deep_update(dict1: Dict, dict2: Dict) -> Dict:
        """Deep dictionary update"""
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Helpers.deep_update(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def safe_json_parse(json_str: str, default: Any = None) -> Any:
        """Safely parse JSON"""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def safe_json_stringify(data: Any) -> str:
        """Safely stringify to JSON"""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            return "{}"

    @staticmethod
    def calculate_similarity(list1: List, list2: List) -> float:
        """Calculate similarity between two lists"""
        if not list1 and not list2:
            return 1.0

        if not list1 or not list2:
            return 0.0

        set1 = set(list1)
        set2 = set(list2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0 B"

        size_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)

        return f"{s} {size_names[i]}"