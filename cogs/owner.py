import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from config import BOT_CONFIG, COLORS
from utils.database import Database

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="gban", description="Globally ban a user across all servers")
    @app_commands.describe(user_id="The user ID to ban", reason="Reason for the global ban")
    async def global_ban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Globally ban a user across all servers"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        try:
            user_id_int = int(user_id)
            user = await self.bot.fetch_user(user_id_int)
        except (ValueError, discord.NotFound):
            await interaction.response.send_message("❌ Invalid user ID or user not found!")
            return

        if user.id == BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Cannot ban the bot owner!")
            return

        # Defer response since this might take time
        await interaction.response.defer()

        # Add to global ban list
        self.db.add_global_ban(user.id, reason, interaction.user.id)

        # Ban from all servers where bot has permission
        banned_servers = []
        failed_servers = []

        for guild in self.bot.guilds:
            try:
                await guild.ban(user, reason=f"Global ban by owner: {reason}")
                banned_servers.append(guild.name)
            except (discord.Forbidden, discord.HTTPException):
                failed_servers.append(guild.name)

        embed = discord.Embed(
            title="🌍 Global Ban Executed",
            color=COLORS['moderation']
        )
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Banned from", value=f"{len(banned_servers)} servers", inline=True)
        embed.add_field(name="Failed", value=f"{len(failed_servers)} servers", inline=True)

        if failed_servers and len(failed_servers) <= 5:
            embed.add_field(name="Failed servers", value="\n".join(failed_servers), inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gunban", description="Remove a user from global ban list")
    @app_commands.describe(user_id="The user ID to unban")
    async def global_unban(self, interaction: discord.Interaction, user_id: str):
        """Remove a user from global ban list"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        try:
            user_id_int = int(user_id)
            user = await self.bot.fetch_user(user_id_int)
        except (ValueError, discord.NotFound):
            await interaction.response.send_message("❌ Invalid user ID or user not found!")
            return

        # Remove from global ban list
        if self.db.remove_global_ban(user.id):
            embed = discord.Embed(
                title="✅ Global Ban Removed",
                description=f"Removed {user.mention} ({user}) from global ban list",
                color=COLORS['success']
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ User is not globally banned!")

    @app_commands.command(name="gkick", description="Globally kick a user from all servers")
    @app_commands.describe(user_id="The user ID to
