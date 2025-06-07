import discord
from discord.ext import commands
import random
import aiohttp
import sqlite3
import json
import praw
import os
from datetime import datetime

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_sessions = {}
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent="discord_bot:v1.0"
        )
        
    @commands.command()
    async def trivia(self, ctx):
        """Start a trivia game"""
        if ctx.channel.id in self.trivia_sessions:
            await ctx.send("A trivia game is already running in this channel!")
            return
            
        async with aiohttp.ClientSession() as session:
            async with session.get('https://opentdb.com/api.php?amount=1&type=multiple') as response:
                data = await response.json()
                
        if data['response_code'] == 0:
            question_data = data['results'][0]
            
            # Format question and answers
            question = discord.utils.escape_markdown(question_data['question'])
            correct_answer = question_data['correct_answer']
            answers = question_data['incorrect_answers'] + [correct_answer]
            random.shuffle(answers)
            
            # Create embed
            embed = discord.Embed(title="Trivia Time!", color=discord.Color.blue())
            embed.add_field(name="Category", value=question_data['category'], inline=False)
            embed.add_field(name="Question", value=question, inline=False)
            
            # Add answers with letters
            answer_text = ""
            for idx, answer in enumerate(answers):
                letter = chr(65 + idx)  # A, B, C, D
                answer_text += f"{letter}. {discord.utils.escape_markdown(answer)}\n"
            embed.add_field(name="Answers", value=answer_text, inline=False)
            
            # Store session data
            self.trivia_sessions[ctx.channel.id] = {
                'correct_answer': correct_answer,
                'answers': answers
            }
            
            await ctx.send(embed=embed)
            
            def check(m):
                return (m.channel == ctx.channel and 
                       m.content.upper() in ['A', 'B', 'C', 'D'])
            
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                
                # Get selected answer
                selected_idx = ord(msg.content.upper()) - 65
                selected_answer = answers[selected_idx]
                
                if selected_answer == correct_answer:
                    await ctx.send(f"🎉 Correct, {msg.author.mention}! The answer was: {correct_answer}")
                    await self.add_xp(msg.author.id, ctx.guild.id, 10)
                else:
                    await ctx.send(f"❌ Sorry, that's wrong! The correct answer was: {correct_answer}")
            except:
                await ctx.send(f"Time's up! The correct answer was: {correct_answer}")
            
            del self.trivia_sessions[ctx.channel.id]
    
    @commands.command()
    async def meme(self, ctx):
        """Get a random meme from Reddit"""
        subreddit = self.reddit.subreddit('memes')
        memes = []
        
        async with ctx.typing():
            for submission in subreddit.hot(limit=50):
                if not submission.stickied and submission.url.endswith(('.jpg', '.png', '.gif')):
                    memes.append(submission)
            
            if memes:
                meme = random.choice(memes)
                embed = discord.Embed(title=meme.title, url=f"https://reddit.com{meme.permalink}")
                embed.set_image(url=meme.url)
                embed.set_footer(text=f"👍 {meme.score} | 💬 {meme.num_comments}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("Couldn't fetch any memes right now. Try again later!")
    
    @commands.command()
    async def addcommand(self, ctx, command_name: str, *, response: str):
        """Add a custom command"""
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO custom_commands (guild_id, command, response)
                    VALUES (?, ?, ?)
                ''', (ctx.guild.id, command_name.lower(), response))
                conn.commit()
                await ctx.send(f"✅ Custom command `{command_name}` added successfully!")
            except sqlite3.IntegrityError:
                await ctx.send("This command already exists!")
    
    @commands.command()
    async def level(self, ctx, member: discord.Member = None):
        """Check your or someone else's level"""
        member = member or ctx.author
        
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT xp, level FROM user_xp
                WHERE user_id = ? AND guild_id = ?
            ''', (member.id, ctx.guild.id))
            result = cursor.fetchone()
            
            if result:
                xp, level = result
                embed = discord.Embed(
                    title=f"Level Stats for {member.display_name}",
                    color=member.color
                )
                embed.add_field(name="Level", value=level, inline=True)
                embed.add_field(name="XP", value=xp, inline=True)
                embed.add_field(
                    name="Progress to Next Level",
                    value=f"{xp % 100}/100 XP",
                    inline=False
                )
                embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"{member.display_name} hasn't earned any XP yet!")
    
    async def add_xp(self, user_id, guild_id, xp_amount):
        """Add XP to a user"""
        with sqlite3.connect('bot.db') as conn:
            cursor = conn.cursor()
            
            # Get current XP and level
            cursor.execute('''
                INSERT OR IGNORE INTO user_xp (user_id, guild_id, xp, level)
                VALUES (?, ?, 0, 0)
            ''', (user_id, guild_id))
            
            cursor.execute('''
                SELECT xp, level FROM user_xp
                WHERE user_id = ? AND guild_id = ?
            ''', (user_id, guild_id))
            
            current_xp, current_level = cursor.fetchone()
            new_xp = current_xp + xp_amount
            
            # Check for level up (every 100 XP)
            new_level = new_xp // 100
            if new_level > current_level:
                # Get the channel to send level up message
                guild = self.bot.get_guild(guild_id)
                if guild:
                    member = guild.get_member(user_id)
                    if member:
                        # Try to find a suitable channel to send the message
                        for channel in guild.text_channels:
                            try:
                                await channel.send(
                                    f"🎉 Congratulations {member.mention}! "
                                    f"You've reached level {new_level}!"
                                )
                                break
                            except:
                                continue
            
            # Update the database
            cursor.execute('''
                UPDATE user_xp
                SET xp = ?, level = ?
                WHERE user_id = ? AND guild_id = ?
            ''', (new_xp, new_level, user_id, guild_id))
            
            conn.commit()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Add XP for messages"""
        if not message.author.bot and message.guild:
            await self.add_xp(message.author.id, message.guild.id, random.randint(1, 5))
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Process custom commands"""
        if ctx.command is None and not ctx.author.bot:
            with sqlite3.connect('bot.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT response FROM custom_commands
                    WHERE guild_id = ? AND command = ?
                ''', (ctx.guild.id, ctx.invoked_with.lower()))
                result = cursor.fetchone()
                
                if result:
                    await ctx.send(result[0])

async def setup(bot):
    await bot.add_cog(Fun(bot)) 