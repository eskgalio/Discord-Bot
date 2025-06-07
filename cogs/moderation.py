import discord
from discord.ext import commands
import asyncio
from better_profanity import profanity
import sqlite3

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        profanity.load_censor_words()
        
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        await member.kick(reason=reason)
        await ctx.send(f'👢 Kicked {member.mention}' + (f' for: {reason}' if reason else ''))
        
        # Log the kick
        await self.log_action(ctx.guild, 'Kick', member, reason)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        await member.ban(reason=reason)
        await ctx.send(f'🔨 Banned {member.mention}' + (f' for: {reason}' if reason else ''))
        
        # Log the ban
        await self.log_action(ctx.guild, 'Ban', member, reason)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None):
        """Mute a member"""
        # Get or create muted role
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            
            # Set up permissions for the muted role
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, speak=False, send_messages=False)
        
        await member.add_roles(muted_role)
        
        if duration:
            # Convert duration string to seconds
            time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            try:
                time = int(duration[:-1]) * time_convert[duration[-1]]
                await ctx.send(f'🔇 Muted {member.mention} for {duration}')
                await asyncio.sleep(time)
                await member.remove_roles(muted_role)
                await ctx.send(f'🔊 Unmuted {member.mention}')
            except:
                await ctx.send("Invalid duration format. Use: number + s/m/h/d (e.g., 30s, 5m, 1h, 1d)")
                return
        else:
            await ctx.send(f'🔇 Muted {member.mention} indefinitely')
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            await ctx.send(f'🔊 Unmuted {member.mention}')
        else:
            await ctx.send(f'{member.mention} is not muted')
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Set slowmode for the current channel"""
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send('Slowmode disabled')
        else:
            await ctx.send(f'Slowmode set to {seconds} seconds')
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def massrole(self, ctx, role: discord.Role, action: str):
        """Mass assign or remove a role from all members"""
        if action.lower() not in ['add', 'remove']:
            await ctx.send('Please specify "add" or "remove"')
            return
        
        async with ctx.typing():
            if action.lower() == 'add':
                for member in ctx.guild.members:
                    if role not in member.roles:
                        await member.add_roles(role)
            else:
                for member in ctx.guild.members:
                    if role in member.roles:
                        await member.remove_roles(role)
        
        await ctx.send(f'✅ Mass role {action} completed for role: {role.name}')
    
    async def log_action(self, guild, action_type, target, reason=None):
        """Log moderation actions to the designated logging channel"""
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT log_channel_id FROM guild_settings WHERE guild_id = ?',
                         (guild.id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                log_channel = guild.get_channel(result[0])
                if log_channel:
                    embed = discord.Embed(
                        title=f"📝 {action_type} Log",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(name="Target", value=str(target), inline=True)
                    embed.add_field(name="Action", value=action_type, inline=True)
                    if reason:
                        embed.add_field(name="Reason", value=reason, inline=False)
                    
                    await log_channel.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Message filter for profanity and spam"""
        if message.author.bot:
            return
            
        # Profanity check
        if profanity.contains_profanity(message.content):
            await message.delete()
            await message.channel.send(f"{message.author.mention} Watch your language!", delete_after=5)
            return
            
        # Basic spam check (placeholder - you might want to implement more sophisticated spam detection)
        # This is a very basic example checking for repeated messages
        messages = [msg async for msg in message.channel.history(limit=5)]
        if len(messages) >= 3:
            if all(msg.content == message.content and msg.author == message.author 
                   for msg in messages[:3]):
                await message.delete()
                await message.channel.send(f"{message.author.mention} Please don't spam!", 
                                         delete_after=5)

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 