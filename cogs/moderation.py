import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
from datetime import datetime, timedelta
from config import BOT_CONFIG, COLORS
from utils.database import Database
from utils.helpers import parse_time

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
    
    async def protect_owner(self, interaction, target):
        """Protect bot owner from moderation actions"""
        if target.id == BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ Cannot perform moderation actions on the bot owner!")
            return False
        return True

    async def create_mute_role(self, guild):
        """Create mute role if it doesn't exist"""
        mute_role = discord.utils.get(guild.roles, name=BOT_CONFIG['mute_role_name'])
        
        if not mute_role:
            mute_role = await guild.create_role(
                name=BOT_CONFIG['mute_role_name'],
                permissions=discord.Permissions(send_messages=False, speak=False),
                reason="Mute role for moderation"
            )
            
            # Update channel permissions
            for channel in guild.channels:
                await channel.set_permissions(
                    mute_role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False
                )
        
        return mute_role

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if not await self.protect_owner(interaction, member):
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ You cannot kick someone with equal or higher roles!")
            return
        
        try:
            await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=COLORS['moderation']
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.db.log_moderation_action(
                interaction.guild.id, member.id, interaction.user.id, 'kick', reason
            )
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this member!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error kicking member: {e}")

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if not await self.protect_owner(interaction, member):
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ You cannot ban someone with equal or higher roles!")
            return
        
        try:
            await member.ban(reason=f"Banned by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=COLORS['moderation']
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=True)
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.db.log_moderation_action(
                interaction.guild.id, member.id, interaction.user.id, 'ban', reason
            )
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this member!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error banning member: {e}")

    @app_commands.command(name="unban", description="Unban a member from the server")
    @app_commands.describe(user="The user to unban (format: username#1234)")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user: str):
        """Unban a member from the server"""
        banned_users = [entry async for entry in interaction.guild.bans()]
        
        member_name, member_discriminator = user.split('#')
        
        for ban_entry in banned_users:
            banned_user = ban_entry.user
            
            if (banned_user.name, banned_user.discriminator) == (member_name, member_discriminator):
                await interaction.guild.unban(banned_user)
                
                embed = discord.Embed(
                    title="✅ Member Unbanned",
                    color=COLORS['success']
                )
                embed.add_field(name="Member", value=f"{banned_user.mention} ({banned_user})", inline=False)
                embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                embed.timestamp = datetime.utcnow()
                
                await interaction.response.send_message(embed=embed)
                return
        
        await interaction.response.send_message("❌ Member not found in ban list!")

    @app_commands.command(name="mute", description="Mute a member")
    @app_commands.describe(member="The member to mute", time="Duration (e.g., 10m, 1h, 1d)", reason="Reason for the mute")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time: str = None, reason: str = "No reason provided"):
        """Mute a member"""
        if not await self.protect_owner(interaction, member):
            return
        
        if member.top_role >= interaction.user.top_role and interaction.user.id != BOT_CONFIG['owner_id']:
            await interaction.response.send_message("❌ You cannot mute someone with equal or higher roles!")
            return
        
        mute_role = await self.create_mute_role(interaction.guild)
        
        if mute_role in member.roles:
            await interaction.response.send_message("❌ Member is already muted!")
            return
        
        try:
            await member.add_roles(mute_role, reason=f"Muted by {interaction.user}: {reason}")
            
            # Parse time
            duration = None
            if time:
                duration = parse_time(time)
                if duration:
                    # Schedule unmute
                    asyncio.create_task(self.scheduled_unmute(member, mute_role, duration))
            
            embed = discord.Embed(
                title="🔇 Member Muted",
                color=COLORS['moderation']
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Duration", value=time or "Permanent", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
            # Log the action
            self.db.log_moderation_action(
                interaction.guild.id, member.id, interaction.user.id, 'mute', reason
            )
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute this member!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error muting member: {e}")

    async def scheduled_unmute(self, member, mute_role, duration):
        """Automatically unmute member after duration"""
        await asyncio.sleep(duration)
        try:
            if mute_role in member.roles:
                await member.remove_roles(mute_role, reason="Automatic unmute")
        except:
            pass  # Member might have left the server

    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="The member to unmute")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        """Unmute a member"""
        mute_role = discord.utils.get(interaction.guild.roles, name=BOT_CONFIG['mute_role_name'])
        
        if not mute_role or mute_role not in member.roles:
            await interaction.response.send_message("❌ Member is not muted!")
            return
        
        try:
            await member.remove_roles(mute_role, reason=f"Unmuted by {interaction.user}")
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                color=COLORS['success']
            )
            embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.timestamp = datetime.utcnow()
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unmute this member!")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error unmuting member: {e}")

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    @app_commands.default_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """Warn a member"""
        if not await self.protect_owner(interaction, member):
            return
        
        # Add warning to database
        warning_id = self.db.add_warning(interaction.guild.id, member.id, interaction.user.id, reason)
        
        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=COLORS['warning']
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Warning ID", value=warning_id, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed)
        
        # Check if member has too many warnings
        warnings = self.db.get_warnings(interaction.guild.id, member.id)
        if len(warnings) >= BOT_CONFIG['max_warnings']:
            await interaction.followup.send(f"⚠️ {member.mention} has reached the maximum number of warnings!")

    @app_commands.command(name="warnings", description="Check a member's warnings")
    @app_commands.describe(member="The member to check warnings for")
    @app_commands.default_permissions(kick_members=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        """Check member's warnings"""
        warnings = self.db.get_warnings(interaction.guild.id, member.id)
        
        if not warnings:
            await interaction.response.send_message(f"✅ {member.mention} has no warnings!")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Warnings for {member}",
            color=COLORS['warning']
        )
        
        for warning in warnings[-5:]:  # Show last 5 warnings
            moderator = self.bot.get_user(warning['moderator_id'])
            mod_name = moderator.name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning #{warning['id']}",
                value=f"**Moderator:** {mod_name}\n**Reason:** {warning['reason']}\n**Date:** {warning['timestamp']}",
                inline=False
            )
        
        embed.set_footer(text=f"Total warnings: {len(warnings)}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
