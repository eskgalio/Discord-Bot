import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import json
import asyncio
from better_profanity import profanity

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize default prefix
DEFAULT_PREFIX = '!'

# Function to get custom prefix for a server
async def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    
    try:
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT prefix FROM guild_settings WHERE guild_id = ?', 
                         (message.guild.id,))
            result = cursor.fetchone()
            return result[0] if result else DEFAULT_PREFIX
    except:
        return DEFAULT_PREFIX

# Initialize bot with custom prefix and remove default help command
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Database initialization
def init_db():
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        
        # Guild settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '!',
                welcome_channel_id INTEGER,
                log_channel_id INTEGER
            )
        ''')
        
        # User XP table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_xp (
                user_id INTEGER,
                guild_id INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        
        # Custom commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                guild_id INTEGER,
                command TEXT,
                response TEXT,
                PRIMARY KEY (guild_id, command)
            )
        ''')
        
        # Reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                user_id INTEGER,
                guild_id INTEGER,
                reminder_text TEXT,
                reminder_time TIMESTAMP
            )
        ''')
        
        conn.commit()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    init_db()
    # Load all cogs
    for cog in ['moderation', 'fun', 'analytics']:
        try:
            await bot.load_extension(f'cogs.{cog}')
            print(f'Loaded {cog} cog')
        except Exception as e:
            print(f'Failed to load {cog} cog: {str(e)}')
    await bot.change_presence(activity=discord.Game(name=f"Type {DEFAULT_PREFIX}help"))

@bot.event
async def on_guild_join(guild):
    # Initialize guild settings when bot joins a new server
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO guild_settings (guild_id, prefix) VALUES (?, ?)',
                      (guild.id, DEFAULT_PREFIX))
        conn.commit()

@bot.event
async def on_member_join(member):
    # Welcome message
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT welcome_channel_id FROM guild_settings WHERE guild_id = ?',
                      (member.guild.id,))
        result = cursor.fetchone()
        
        if result and result[0]:
            welcome_channel = member.guild.get_channel(result[0])
            if welcome_channel:
                welcome_msg = f"Welcome {member.mention} to {member.guild.name}! 🎉"
                await welcome_channel.send(welcome_msg)

@bot.command(name='help')
async def help_command(ctx):
    prefix = await get_prefix(bot, ctx.message)
    embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())
    
    # General Utility
    embed.add_field(name="⚙️ General Utility", value=f"""
        `{prefix}help` - Show this message
        `{prefix}ping` - Check bot latency
        `{prefix}prefix <new_prefix>` - Change server prefix
        `{prefix}getrole <role>` - Get a role
        `{prefix}remind <time> <reminder>` - Set a reminder
        `{prefix}poll "<title>" "<option1>" "<option2>"` - Create a poll
    """, inline=False)
    
    # Moderation
    embed.add_field(name="🛠️ Moderation", value=f"""
        `{prefix}kick <user> [reason]` - Kick a user
        `{prefix}ban <user> [reason]` - Ban a user
        `{prefix}mute <user> [duration]` - Mute a user
        `{prefix}unmute <user>` - Unmute a user
        `{prefix}slowmode <seconds>` - Set slowmode
    """, inline=False)
    
    # Fun/Engagement
    embed.add_field(name="🎉 Fun & Engagement", value=f"""
        `{prefix}trivia` - Start a trivia game
        `{prefix}meme` - Get a random meme
        `{prefix}addcommand <name> <response>` - Add custom command
        `{prefix}level` - Check your level
    """, inline=False)
    
    # Analytics
    embed.add_field(name="📈 Analytics", value=f"""
        `{prefix}stats` - View server stats
        `{prefix}leaderboard` - View XP leaderboard
    """, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='prefix')
@commands.has_permissions(administrator=True)
async def change_prefix(ctx, new_prefix: str):
    with sqlite3.connect('bot.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE guild_settings SET prefix = ? WHERE guild_id = ?',
                      (new_prefix, ctx.guild.id))
        conn.commit()
    await ctx.send(f'Prefix has been updated to: {new_prefix}')

@bot.command(name='getrole')
async def get_role(ctx, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        try:
            await ctx.author.add_roles(role)
            await ctx.send(f'✅ Added role: {role.name}')
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to assign that role.")
    else:
        await ctx.send("❌ Role not found.")

@bot.command(name='poll')
async def create_poll(ctx, title: str, *options):
    if len(options) < 2:
        await ctx.send("❌ Please provide at least 2 options!")
        return
    
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    description = '\n'.join(f'{emoji_numbers[idx]} {option}' 
                           for idx, option in enumerate(options[:10]))
    
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    poll_message = await ctx.send(embed=embed)
    
    for idx in range(min(len(options), 10)):
        await poll_message.add_reaction(emoji_numbers[idx])

# Run the bot
if __name__ == "__main__":
    bot.run(TOKEN) 