"""
Configuration file for the Discord bot
"""

BOT_CONFIG = {
    'prefix': '!',
    'owner_id': 1342772842424438806,
    'owner_username': 'nikutemporary_1',
    'max_queue_size': 50,
    'default_volume': 50,
    'command_cooldown': 3,  # seconds
    'music_timeout': 300,   # seconds (5 minutes)
    'max_warnings': 5,
    'mute_role_name': 'Muted',
    'log_channel_name': 'bot-logs'
}

# YouTube DL options for music
YTDL_OPTS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

# FFmpeg options
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Embed colors
COLORS = {
    'success': 0x00ff00,
    'error': 0xff0000,
    'warning': 0xffff00,
    'info': 0x0099ff,
    'music': 0x9b59b6,
    'moderation': 0xe74c3c
}
