import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
from config import BOT_CONFIG, YTDL_OPTS, FFMPEG_OPTS, COLORS
from utils.helpers import time_format

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.voice_clients = {}
        self.current_songs = {}
        
        # Create ytdl instance
        self.ytdl = yt_dlp.YoutubeDL(YTDL_OPTS)
    
    def get_queue(self, guild_id):
        """Get or create queue for guild"""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]
    
    async def search_song(self, query):
        """Search for a song on YouTube"""
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ytdl.extract_info(f"ytsearch:{query}", download=False)
            )
            
            if data and 'entries' in data and len(data['entries']) > 0:
                return data['entries'][0]
            return None
        except Exception as e:
            print(f"Error searching song: {e}")
            return None
    
    async def play_next(self, guild_id):
        """Play next song in queue"""
        queue = self.get_queue(guild_id)
        
        if not queue:
            # No more songs, disconnect after timeout
            await asyncio.sleep(BOT_CONFIG['music_timeout'])
            if guild_id in self.voice_clients and not queue:
                await self.voice_clients[guild_id].disconnect()
                del self.voice_clients[guild_id]
                if guild_id in self.current_songs:
                    del self.current_songs[guild_id]
            return
        
        song = queue.pop(0)
        voice_client = self.voice_clients[guild_id]
        
        try:
            # Create audio source with proper URL
            if 'url' in song:
                url = song['url']
            elif 'webpage_url' in song:
                # Extract direct audio URL
                info = self.ytdl.extract_info(song['webpage_url'], download=False)
                url = info['url']
            else:
                print("No valid URL found for song")
                await self.play_next(guild_id)
                return
            
            # Create audio source
            source = discord.FFmpegPCMAudio(
                url,
                before_options=FFMPEG_OPTS['before_options'],
                options=FFMPEG_OPTS['options']
            )
            
            # Play the song
            voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(guild_id), self.bot.loop
                )
            )
            
            self.current_songs[guild_id] = song
            
        except Exception as e:
            print(f"Error playing song: {e}")
            await self.play_next(guild_id)
    
    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(query="The song name or YouTube URL to play")
    async def play(self, interaction: discord.Interaction, query: str):
        """Play a song from YouTube"""
        if not interaction.user.voice:
            await interaction.response.send_message("❌ You need to be in a voice channel to use this command!")
            return
        
        # Defer response since searching might take time
        await interaction.response.defer()
        
        # Search for the song
        song = await self.search_song(query)
        
        if not song:
            await interaction.followup.send("❌ No results found!")
            return
        
        # Connect to voice channel if not connected
        if interaction.guild.id not in self.voice_clients:
            voice_channel = interaction.user.voice.channel
            voice_client = await voice_channel.connect()
            self.voice_clients[interaction.guild.id] = voice_client
        
        # Add to queue
        queue = self.get_queue(interaction.guild.id)
        queue.append(song)
        
        embed = discord.Embed(
            title="🎵 Added to Queue",
            description=f"**[{song['title']}]({song['webpage_url']})**",
            color=COLORS['music']
        )
        embed.add_field(name="Duration", value=time_format(song.get('duration', 0)), inline=True)
        embed.add_field(name="Position in Queue", value=len(queue), inline=True)
        embed.set_thumbnail(url=song.get('thumbnail', ''))
        
        await interaction.followup.send(embed=embed)
        
        # Start playing if not already playing
        voice_client = self.voice_clients[interaction.guild.id]
        if not voice_client.is_playing():
            await self.play_next(interaction.guild.id)
    
    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song"""
        if interaction.guild.id not in self.voice_clients:
            await interaction.response.send_message("❌ Not connected to a voice channel!")
            return
        
        voice_client = self.voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("⏸️ Paused the music!")
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!")
    
    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        """Resume the paused song"""
        if interaction.guild.id not in self.voice_clients:
            await interaction.response.send_message("❌ Not connected to a voice channel!")
            return
        
        voice_client = self.voice_clients[interaction.guild.id]
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("▶️ Resumed the music!")
        else:
            await interaction.response.send_message("❌ Music is not paused!")
    
    @app_commands.command(name="stop", description="Stop music and disconnect")
    async def stop(self, interaction: discord.Interaction):
        """Stop music and disconnect"""
        if interaction.guild.id not in self.voice_clients:
            await interaction.response.send_message("❌ Not connected to a voice channel!")
            return
        
        voice_client = self.voice_clients[interaction.guild.id]
        
        # Clear queue and disconnect
        self.queues[interaction.guild.id] = []
        if interaction.guild.id in self.current_songs:
            del self.current_songs[interaction.guild.id]
        
        await voice_client.disconnect()
        del self.voice_clients[interaction.guild.id]
        
        await interaction.response.send_message("⏹️ Stopped music and disconnected!")
    
    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        """Skip the current song"""
        if interaction.guild.id not in self.voice_clients:
            await interaction.response.send_message("❌ Not connected to a voice channel!")
            return
        
        voice_client = self.voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏭️ Skipped the current song!")
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!")
    
    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: discord.Interaction):
        """Show the current queue"""
        queue = self.get_queue(interaction.guild.id)
        
        if not queue and interaction.guild.id not in self.current_songs:
            await interaction.response.send_message("❌ Queue is empty!")
            return
        
        embed = discord.Embed(
            title="🎵 Music Queue",
            color=COLORS['music']
        )
        
        # Show current song
        if interaction.guild.id in self.current_songs:
            current = self.current_songs[interaction.guild.id]
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**[{current['title']}]({current['webpage_url']})**",
                inline=False
            )
        
        # Show queue
        if queue:
            queue_text = ""
            for i, song in enumerate(queue[:10], 1):  # Show first 10 songs
                queue_text += f"{i}. **{song['title']}** ({time_format(song.get('duration', 0))})\n"
            
            if len(queue) > 10:
                queue_text += f"\n... and {len(queue) - 10} more songs"
            
            embed.add_field(
                name=f"📋 Queue ({len(queue)} songs)",
                value=queue_text,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="nowplaying", description="Show the currently playing song")
    async def nowplaying(self, interaction: discord.Interaction):
        """Show current playing song"""
        if interaction.guild.id not in self.current_songs:
            await interaction.response.send_message("❌ Nothing is currently playing!")
            return
        
        song = self.current_songs[interaction.guild.id]
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{song['title']}]({song['webpage_url']})**",
            color=COLORS['music']
        )
        embed.add_field(name="Duration", value=time_format(song.get('duration', 0)), inline=True)
        embed.add_field(name="Uploader", value=song.get('uploader', 'Unknown'), inline=True)
        embed.set_thumbnail(url=song.get('thumbnail', ''))
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="volume", description="Set the music volume")
    @app_commands.describe(volume="Volume level (1-100)")
    async def volume(self, interaction: discord.Interaction, volume: int):
        """Set the volume (1-100)"""
        if not 1 <= volume <= 100:
            await interaction.response.send_message("❌ Volume must be between 1 and 100!")
            return
        
        if interaction.guild.id not in self.voice_clients:
            await interaction.response.send_message("❌ Not connected to a voice channel!")
            return
        
        voice_client = self.voice_clients[interaction.guild.id]
        if voice_client.source:
            voice_client.source.volume = volume / 100
            await interaction.response.send_message(f"🔊 Volume set to {volume}%!")
        else:
            await interaction.response.send_message("❌ Nothing is currently playing!")

async def setup(bot):
    await bot.add_cog(Music(bot))
