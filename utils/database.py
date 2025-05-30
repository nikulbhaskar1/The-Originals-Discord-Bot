import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.global_bans_file = 'data/global_bans.json'
        self.server_settings_file = 'data/server_settings.json'
        self.warnings_file = 'data/warnings.json'
        self.moderation_logs_file = 'data/moderation_logs.json'
        
        # Initialize files if they don't exist
        self._init_file(self.global_bans_file, {})
        self._init_file(self.server_settings_file, {})
        self._init_file(self.warnings_file, {})
        self._init_file(self.moderation_logs_file, {})
    
    def _init_file(self, filename, default_data):
        """Initialize a file with default data if it doesn't exist"""
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(default_data, f, indent=2)
    
    def _load_json(self, filename):
        """Load JSON data from file"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filename, data):
        """Save JSON data to file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Global Bans
    def add_global_ban(self, user_id, reason, moderator_id):
        """Add a user to global ban list"""
        data = self._load_json(self.global_bans_file)
        data[str(user_id)] = {
            'user_id': user_id,
            'reason': reason,
            'moderator_id': moderator_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        self._save_json(self.global_bans_file, data)
    
    def remove_global_ban(self, user_id):
        """Remove a user from global ban list"""
        data = self._load_json(self.global_bans_file)
        if str(user_id) in data:
            del data[str(user_id)]
            self._save_json(self.global_bans_file, data)
            return True
        return False
    
    def is_globally_banned(self, user_id):
        """Check if a user is globally banned"""
        data = self._load_json(self.global_bans_file)
        return str(user_id) in data
    
    def get_global_bans(self):
        """Get all global bans"""
        data = self._load_json(self.global_bans_file)
        return list(data.values())
    
    # Global Mutes
    def add_global_mute(self, user_id, reason, moderator_id, duration=None):
        """Add a user to global mute list"""
        # For simplicity, storing in the same structure as bans
        # In a real implementation, you might want a separate file
        pass
    
    # Warnings
    def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Add a warning to a user"""
        data = self._load_json(self.warnings_file)
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key not in data:
            data[guild_key] = {}
        if user_key not in data[guild_key]:
            data[guild_key][user_key] = []
        
        warning_id = len(data[guild_key][user_key]) + 1
        warning = {
            'id': warning_id,
            'reason': reason,
            'moderator_id': moderator_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        data[guild_key][user_key].append(warning)
        self._save_json(self.warnings_file, data)
        return warning_id
    
    def get_warnings(self, guild_id, user_id):
        """Get all warnings for a user in a guild"""
        data = self._load_json(self.warnings_file)
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key in data and user_key in data[guild_key]:
            return data[guild_key][user_key]
        return []
    
    def clear_warnings(self, guild_id, user_id):
        """Clear all warnings for a user"""
        data = self._load_json(self.warnings_file)
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key in data and user_key in data[guild_key]:
            data[guild_key][user_key] = []
            self._save_json(self.warnings_file, data)
            return True
        return False
    
    # Moderation Logs
    def log_moderation_action(self, guild_id, target_id, moderator_id, action, reason):
        """Log a moderation action"""
        data = self._load_json(self.moderation_logs_file)
        guild_key = str(guild_id)
        
        if guild_key not in data:
            data[guild_key] = []
        
        log_entry = {
            'target_id': target_id,
            'moderator_id': moderator_id,
            'action': action,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        data[guild_key].append(log_entry)
        self._save_json(self.moderation_logs_file, data)
    
    def get_moderation_logs(self, guild_id, limit=50):
        """Get recent moderation logs for a guild"""
        data = self._load_json(self.moderation_logs_file)
        guild_key = str(guild_id)
        
        if guild_key in data:
            return data[guild_key][-limit:]
        return []
    
    # Server Settings
    def get_server_settings(self, guild_id):
        """Get settings for a server"""
        data = self._load_json(self.server_settings_file)
        return data.get(str(guild_id), {})
    
    def update_server_settings(self, guild_id, settings):
        """Update settings for a server"""
        data = self._load_json(self.server_settings_file)
        data[str(guild_id)] = settings
        self._save_json(self.server_settings_file, data)
