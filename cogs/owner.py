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
    @app_commands.describe(user_id="The user ID to kick", reason="Reason for the global kick")
    async def global_kick(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        """Globally kick a user from all servers"""
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
            await interaction.response.send_message("❌ Cannot kick the bot owner!")
            return

        # Defer response since this might take time
        await interaction.response.defer()

        # Kick from all servers
        kicked_servers = []
        failed_servers = []

        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id)
                if member:
                    await member.kick(reason=f"Global kick by owner: {reason}")
                    kicked_servers.append(guild.name)
            except (discord.Forbidden, discord.HTTPException):
                failed_servers.append(guild.name)

        embed = discord.Embed(
            title="🌍 Global Kick Executed",
            color=COLORS['moderation']
        )
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Kicked from", value=f"{len(kicked_servers)} servers", inline=True)
        embed.add_field(name="Failed", value=f"{len(failed_servers)} servers", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gmute", description="Globally mute a user across all servers")
    @app_commands.describe(user_id="The user ID to mute", time="Duration (e.g., 10m, 1h, 1d)", reason="Reason for the global mute")
    async def global_mute(self, interaction: discord.Interaction, user_id: str, time: str = None, reason: str = "No reason provided"):
        """Globally mute a user across all servers"""
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
            await interaction.response.send_message("❌ Cannot mute the bot owner!")
            return

        # Defer response since this might take time
        await interaction.response.defer()

        # Add to global mute list
        self.db.add_global_mute(user.id, reason, interaction.user.id, time)

        # Mute in all servers
        muted_servers = []
        failed_servers = []

        for guild in self.bot.guilds:
            try:
                member = guild.get_member(user.id)
                if member:
                    # Create or get mute role
                    mute_role = discord.utils.get(guild.roles, name=BOT_CONFIG['mute_role_name'])
                    if not mute_role:
                        mute_role = await guild.create_role(
                            name=BOT_CONFIG['mute_role_name'],
                            permissions=discord.Permissions(send_messages=False, speak=False)
                        )

                    await member.add_roles(mute_role, reason=f"Global mute by owner: {reason}")
                    muted_servers.append(guild.name)
            except (discord.Forbidden, discord.HTTPException):
                failed_servers.append(guild.name)

        embed = discord.Embed(
            title="🌍 Global Mute Executed",
            color=COLORS['moderation']
        )
        embed.add_field(name="User", value=f"{user.mention} ({user})", inline=False)
        embed.add_field(name="Duration", value=time or "Permanent", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Muted in", value=f"{len(muted_servers)} servers", inline=True)
        embed.add_field(name="Failed", value=f"{len(failed_servers)} servers", inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="gbans", description="List all globally banned users")
    async def global_bans(self, interaction: discord.Interaction):
        """List all globally banned users"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        global_bans = self.db.get_global_bans()

        if not global_bans:
            await interaction.response.send_message("✅ No global bans found!")
            return

        embed = discord.Embed(
            title="🌍 Global Bans",
            color=COLORS['moderation']
        )

        for ban in global_bans[-10:]:  # Show last 10 bans
            try:
                user = await self.bot.fetch_user(ban['user_id'])
                user_info = f"{user.name}#{user.discriminator}"
            except:
                user_info = f"Unknown User ({ban['user_id']})"

            embed.add_field(
                name=user_info,
                value=f"**Reason:** {ban['reason']}\n**Date:** {ban['timestamp']}",
                inline=False
            )

        embed.set_footer(text=f"Total global bans: {len(global_bans)}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reload", description="Reload a specific cog")
    @app_commands.describe(cog_name="The name of the cog to reload")
    async def reload_cog(self, interaction: discord.Interaction, cog_name: str):
        """Reload a specific cog"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        try:
            await self.bot.reload_extension(f'cogs.{cog_name}')
            await interaction.response.send_message(f"✅ Successfully reloaded `{cog_name}` cog!")
        except commands.ExtensionNotFound:
            await interaction.response.send_message(f"❌ Cog `{cog_name}` not found!")
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(f"❌ Cog `{cog_name}` is not loaded!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error reloading cog: {e}")

    @app_commands.command(name="servers", description="List all servers the bot is in")
    async def list_servers(self, interaction: discord.Interaction):
        """List all servers the bot is in"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        embed = discord.Embed(
            title="🌍 Bot Servers",
            color=COLORS['info']
        )

        server_list = []
        for guild in self.bot.guilds:
            server_list.append(f"**{guild.name}** ({guild.id}) - {guild.member_count} members")

        # Split into chunks if too long
        for i in range(0, len(server_list), 10):
            chunk = server_list[i:i+10]
            embed.add_field(
                name=f"Servers {i+1}-{min(i+10, len(server_list))}",
                value="\n".join(chunk),
                inline=False
            )

        embed.set_footer(text=f"Total servers: {len(self.bot.guilds)}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leave", description="Leave a specific server")
    @app_commands.describe(guild_id="The server ID to leave")
    async def leave_server(self, interaction: discord.Interaction, guild_id: str):
        """Leave a specific server"""
        if interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Only the bot owner can use this command!")
            return
            
        try:
            guild_id_int = int(guild_id)
            guild = self.bot.get_guild(guild_id_int)
        except ValueError:
            await interaction.response.send_message("❌ Invalid server ID!")
            return
            
        if not guild:
            await interaction.response.send_message("❌ Server not found!")
            return

        guild_name = guild.name
        await guild.leave()
        await interaction.response.send_message(f"✅ Left server: **{guild_name}**")

async def setup(bot):
    await bot.add_cog(Owner(bot))
