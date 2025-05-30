import re
from datetime import timedelta

def time_format(seconds):
    """Format seconds into a readable time string"""
    if not seconds:
        return "Unknown"
    
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def parse_time(time_str):
    """Parse time string into seconds"""
    if not time_str:
        return None
    
    time_regex = re.compile(r'(\d+)([smhd])')
    matches = time_regex.findall(time_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        
        if unit == 's':
            total_seconds += amount
        elif unit == 'm':
            total_seconds += amount * 60
        elif unit == 'h':
            total_seconds += amount * 3600
        elif unit == 'd':
            total_seconds += amount * 86400
    
    return total_seconds

def truncate_string(text, max_length=100):
    """Truncate a string to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_user(user):
    """Format a user object for display"""
    return f"{user.name}#{user.discriminator} ({user.id})"

def format_timestamp(timestamp):
