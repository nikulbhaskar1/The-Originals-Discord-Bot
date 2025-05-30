import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
import os
import json
from config import BOT_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

class MusicBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=BOT_CONFIG['prefix'],
            intents=intents,
            help_command=None
        )
        self.owner_id = BOT_CONFIG['owner_id']
        
    async def setup_hook(self):
        """Load all cogs when bot starts"""
        try:
            await self.load_extension('cogs.music')
            await self.load_extension('cogs.moderation')
            await self.load_extension('cogs.owner')
            logger.info("All cogs loaded successfully")
            
            # Sync slash commands
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")
                
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="/help | Music & Moderation"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command!")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param}`")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command on cooldown! Try again in {error.retry_after:.2f} seconds")
        else:
            logger.error(f"Unhandled error: {error}")
            await ctx.send("❌ An unexpected error occurred!")
    
    def is_owner_check(self, user_id):
        """Check if user is the bot owner"""
        return user_id == self.owner_id

# Custom help slash command
@app_commands.command(name="help", description="Display help information")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    embed = discord.Embed(
        title="🤖 Bot Commands Help",
        description="Multi-purpose Discord bot with music and moderation features",
        color=discord.Color.blue()
    )
    
    # Music commands
    music_commands = [
        "`/play <song>` - Play a song from YouTube",
        "`/pause` - Pause current song",
        "`/resume` - Resume paused song",
        "`/stop` - Stop music and disconnect",
        "`/skip` - Skip current song",
        "`/queue` - Show current queue",
        "`/volume <1-100>` - Set volume",
        "`/nowplaying` - Show current song"
    ]
    embed.add_field(
        name="🎵 Music Commands",
        value="\n".join(music_commands),
        inline=False
    )
    
    # Moderation commands
    mod_commands = [
        "`/kick <user> [reason]` - Kick a user",
        "`/ban <user> [reason]` - Ban a user",
        "`/unban <user>` - Unban a user",
        "`/mute <user> [time] [reason]` - Mute a user",
        "`/unmute <user>` - Unmute a user",
        "`/warn <user> <reason>` - Warn a user",
        "`/warnings <user>` - Check user warnings"
    ]
    embed.add_field(
        name="🔨 Moderation Commands",
        value="\n".join(mod_commands),
        inline=False
    )
    
    # Owner commands
    bot = interaction.client
    if interaction.user.id == BOT_CONFIG['owner_id']:
        owner_commands = [
            "`/gban <user> [reason]` - Global ban across all servers",
            "`/gunban <user>` - Remove global ban",
            "`/gkick <user> [reason]` - Global kick from all servers",
            "`/gmute <user> [time]` - Global mute across all servers",
            "`/gbans` - List all global bans",
            "`/reload <cog>` - Reload a cog",
            "`/servers` - List all servers",
            "`/leave <server_id>` - Leave a server"
        ]
        embed.add_field(
            name="👑 Owner Commands",
            value="\n".join(owner_commands),
            inline=False
        )
    
    embed.set_footer(text="All commands are slash commands - type / to see them!")
    await interaction.response.send_message(embed=embed)

def main():
    """Main function to run the bot"""
    # Create data directories if they don't exist
    os.makedirs('data', exist_ok=True)
    
    # Initialize data files
    if not os.path.exists('data/global_bans.json'):
        with open('data/global_bans.json', 'w') as f:
            json.dump({}, f)
    
    if not os.path.exists('data/server_settings.json'):
        with open('data/server_settings.json', 'w') as f:
            json.dump({}, f)
    
    # Get bot token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not found!")
        return
    
    # Create and run bot
    bot = MusicBot()
    bot.tree.add_command(help_command)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token!")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    main()
