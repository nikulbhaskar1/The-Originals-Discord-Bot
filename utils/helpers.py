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
    """Format a timestamp for display"""
    if isinstance(timestamp, str):
        # If it's already a string, return as is
        return timestamp
    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

def get_member_top_role(member):
    """Get the highest role of a member"""
    if member.roles:
        return max(member.roles, key=lambda role: role.position)
    return None

def has_higher_role(member1, member2):
    """Check if member1 has a higher role than member2"""
    role1 = get_member_top_role(member1)
    role2 = get_member_top_role(member2)
    
    if not role1:
        return False
    if not role2:
        return True
    
    return role1.position > role2.position

def clean_content(content):
    """Clean message content for logging"""
    # Remove mentions and clean up formatting
    content = re.sub(r'<@!?\d+>', '[User Mention]', content)
    content = re.sub(r'<@&\d+>', '[Role Mention]', content)
    content = re.sub(r'<#\d+>', '[Channel Mention]', content)
    return content

def chunk_list(lst, chunk_size):
    """Split a list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def is_valid_discord_id(user_id):
    """Check if a string is a valid Discord user ID"""
    try:
        user_id = int(user_id)
        return 17 <= len(str(user_id)) <= 19
    except ValueError:
        return False
