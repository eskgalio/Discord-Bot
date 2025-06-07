import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
from collections import Counter

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command()
    async def stats(self, ctx):
        """Display server statistics"""
        guild = ctx.guild
        
        # Get member counts
        total_members = len(guild.members)
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        # Get channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Get role count
        role_count = len(guild.roles) - 1  # Subtract @everyone role
        
        # Get server age
        server_age = (datetime.utcnow() - guild.created_at).days
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 Server Statistics for {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Add server icon if it exists
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Members section
        embed.add_field(
            name="👥 Members",
            value=f"Total: {total_members}\n"
                  f"Online: {online_members}\n"
                  f"Humans: {human_count}\n"
                  f"Bots: {bot_count}",
            inline=True
        )
        
        # Channels section
        embed.add_field(
            name="📝 Channels",
            value=f"Text: {text_channels}\n"
                  f"Voice: {voice_channels}\n"
                  f"Categories: {categories}\n"
                  f"Total: {text_channels + voice_channels}",
            inline=True
        )
        
        # Server info section
        embed.add_field(
            name="ℹ️ Server Info",
            value=f"Age: {server_age} days\n"
                  f"Roles: {role_count}\n"
                  f"Boost Level: {guild.premium_tier}\n"
                  f"Boosters: {guild.premium_subscription_count}",
            inline=True
        )
        
        # Get active channels
        async with ctx.typing():
            message_counts = Counter()
            for channel in guild.text_channels:
                try:
                    async for message in channel.history(limit=100, after=datetime.utcnow() - timedelta(days=7)):
                        if not message.author.bot:
                            message_counts[channel.name] += 1
                except discord.Forbidden:
                    continue
            
            if message_counts:
                top_channels = message_counts.most_common(3)
                active_channels = "\n".join(f"#{channel}: {count} messages" 
                                          for channel, count in top_channels)
                embed.add_field(
                    name="📈 Most Active Channels (7 days)",
                    value=active_channels,
                    inline=False
                )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def leaderboard(self, ctx, page: int = 1):
        """Display the XP leaderboard"""
        if page < 1:
            await ctx.send("Page number must be 1 or higher!")
            return
            
        items_per_page = 10
        offset = (page - 1) * items_per_page
        
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            
            # Get total number of ranked users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id)
                FROM user_xp
                WHERE guild_id = ?
            ''', (ctx.guild.id,))
            total_users = cursor.fetchone()[0]
            
            if total_users == 0:
                await ctx.send("No users have earned XP yet!")
                return
            
            # Calculate total pages
            total_pages = (total_users + items_per_page - 1) // items_per_page
            
            if page > total_pages:
                await ctx.send(f"There are only {total_pages} pages!")
                return
            
            # Get leaderboard data
            cursor.execute('''
                SELECT user_id, xp, level
                FROM user_xp
                WHERE guild_id = ?
                ORDER BY xp DESC
                LIMIT ? OFFSET ?
            ''', (ctx.guild.id, items_per_page, offset))
            
            leaderboard_data = cursor.fetchall()
            
            if not leaderboard_data:
                await ctx.send("No data found for this page!")
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"🏆 XP Leaderboard - Page {page}/{total_pages}",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            # Add leaderboard entries
            description = ""
            for i, (user_id, xp, level) in enumerate(leaderboard_data, start=offset + 1):
                member = ctx.guild.get_member(user_id)
                name = member.display_name if member else f"User {user_id}"
                
                if i == 1:
                    medal = "🥇"
                elif i == 2:
                    medal = "🥈"
                elif i == 3:
                    medal = "🥉"
                else:
                    medal = "👤"
                
                description += f"{medal} **#{i}** {name}\n"
                description += f"Level: {level} | XP: {xp}\n\n"
            
            embed.description = description
            
            # Add navigation footer
            embed.set_footer(text=f"Use {ctx.prefix}leaderboard <page> to view other pages")
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Analytics(bot)) 