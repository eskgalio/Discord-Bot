import cmd
import shlex
import random
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class LocalDiscordBot(cmd.Cmd):
    intro = """
    🤖 Welcome to Local Discord Bot Simulator! 🤖
    Type 'help' to see available commands.
    Type '!help' to see bot commands.
    Type 'quit' to exit.
    
    📝 Note: This is a local simulator that mimics Discord bot functionality.
    """
    prompt = '> '
    
    def __init__(self):
        super().__init__()
        self.current_user = "User123"
        self.server_name = "Test Server"
        self.prefix = "!"
        # User data storage
        self.xp = defaultdict(int)
        self.levels = defaultdict(int)
        self.roles = defaultdict(list)
        self.custom_commands = {}
        self.reminders = []
        self.banned_users = set()
        self.muted_users = set()
        self.server_settings = {
            'welcome_channel': 'welcome',
            'log_channel': 'mod-logs',
            'prefix': '!',
            'slowmode': 0
        }
        # Server stats
        self.message_count = defaultdict(int)
        self.active_users = set()
        self.join_dates = {
            'User123': datetime.now() - timedelta(days=30),
            'Mod1': datetime.now() - timedelta(days=60),
            'Admin1': datetime.now() - timedelta(days=90)
        }
        # Initialize some roles
        self.roles['Admin1'] = ['admin', 'moderator']
        self.roles['Mod1'] = ['moderator']
        
    def default(self, line):
        """Handle bot commands that start with !"""
        if line.startswith(self.prefix):
            command = line[1:].split()
            if command:
                cmd_name = command[0]
                args = command[1:]
                method_name = f'bot_{cmd_name}'
                
                if hasattr(self, method_name):
                    if cmd_name in ['ban', 'kick', 'mute', 'unmute'] and 'moderator' not in self.roles[self.current_user]:
                        print("❌ You don't have permission to use this command!")
                        return
                    
                    # Simulate message activity
                    self.message_count[self.current_user] += 1
                    self.active_users.add(self.current_user)
                    
                    getattr(self, method_name)(args)
                elif cmd_name in self.custom_commands:
                    print(f"🤖 {self.custom_commands[cmd_name]}")
                else:
                    print(f"❌ Unknown command: {cmd_name}")
        else:
            print(f"❌ Unknown command: {line}")
    
    def do_quit(self, arg):
        """Exit the bot simulator"""
        print("👋 Goodbye!")
        return True
        
    def do_setuser(self, arg):
        """Set current user (e.g., setuser NewUser)"""
        if arg:
            self.current_user = arg
            if arg not in self.join_dates:
                self.join_dates[arg] = datetime.now()
            print(f"✅ Current user set to: {self.current_user}")
        else:
            print("❌ Please provide a username")
    
    def bot_help(self, args):
        """Show bot commands"""
        print(f"""
📚 Available Bot Commands (Prefix: {self.server_settings['prefix']})

⚙️ General Utility:
  !help - Show this message
  !ping - Check bot latency
  !prefix <new_prefix> - Change server prefix
  !remind <time> <message> - Set a reminder
  !reminders - List your reminders
  !getrole <role> - Get a role
  !roles - List available roles

🛠️ Moderation (Moderator only):
  !kick <user> [reason] - Kick a user
  !ban <user> [reason] - Ban a user
  !unban <user> - Unban a user
  !mute <user> [duration] - Mute a user
  !unmute <user> - Unmute a user
  !slowmode <seconds> - Set channel slowmode
  !clear <amount> - Clear messages
  !warn <user> <reason> - Warn a user

🎉 Fun & Engagement:
  !say <message> - Make the bot say something
  !roll [number] - Roll a dice
  !8ball <question> - Ask the magic 8-ball
  !coin - Flip a coin
  !poll "title" "option1" "option2" - Create a poll
  !trivia - Start a trivia game

📈 Analytics & Stats:
  !stats - View server statistics
  !level - Check your XP level
  !leaderboard - View XP leaderboard
  !activity - View server activity
  !userinfo [user] - Get user information

🎮 Custom Commands:
  !addcmd <name> <response> - Create custom command
  !listcmd - List all custom commands
  !delcmd <name> - Delete a custom command
        """)
    
    def bot_ping(self, args):
        """Simulate ping command"""
        print("🏓 Pong! Latency: 42ms")

    def bot_prefix(self, args):
        """Change the server prefix"""
        if not args:
            print("❌ Please provide a new prefix")
            return
        if 'admin' not in self.roles[self.current_user]:
            print("❌ Only administrators can change the prefix!")
            return
        self.server_settings['prefix'] = args[0]
        print(f"✅ Server prefix changed to: {args[0]}")
    
    def bot_ban(self, args):
        """Ban a user"""
        if not args:
            print("❌ Please specify a user to ban")
            return
        user = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else "No reason provided"
        self.banned_users.add(user)
        print(f"🔨 Banned {user} | Reason: {reason}")
        self._log_action("ban", user, reason)
    
    def bot_unban(self, args):
        """Unban a user"""
        if not args:
            print("❌ Please specify a user to unban")
            return
        user = args[0]
        if user in self.banned_users:
            self.banned_users.remove(user)
            print(f"✅ Unbanned {user}")
            self._log_action("unban", user)
        else:
            print(f"❌ {user} is not banned")
    
    def bot_mute(self, args):
        """Mute a user"""
        if not args:
            print("❌ Please specify a user to mute")
            return
        user = args[0]
        duration = args[1] if len(args) > 1 else "indefinitely"
        self.muted_users.add(user)
        print(f"🔇 Muted {user} for {duration}")
        self._log_action("mute", user, f"Duration: {duration}")
    
    def bot_unmute(self, args):
        """Unmute a user"""
        if not args:
            print("❌ Please specify a user to unmute")
            return
        user = args[0]
        if user in self.muted_users:
            self.muted_users.remove(user)
            print(f"🔊 Unmuted {user}")
            self._log_action("unmute", user)
        else:
            print(f"❌ {user} is not muted")
    
    def bot_warn(self, args):
        """Warn a user"""
        if len(args) < 2:
            print("❌ Please specify a user and warning reason")
            return
        user = args[0]
        reason = ' '.join(args[1:])
        print(f"⚠️ Warned {user} | Reason: {reason}")
        self._log_action("warn", user, reason)
    
    def bot_slowmode(self, args):
        """Set slowmode"""
        if not args or not args[0].isdigit():
            print("❌ Please specify seconds for slowmode")
            return
        seconds = int(args[0])
        self.server_settings['slowmode'] = seconds
        print(f"🕒 Set slowmode to {seconds} seconds")
    
    def bot_clear(self, args):
        """Simulate clearing messages"""
        amount = int(args[0]) if args and args[0].isdigit() else 10
        print(f"🗑️ Cleared {amount} messages")
    
    def bot_poll(self, args):
        """Create a poll"""
        if len(args) < 2:
            print("❌ Please provide a title and at least 2 options")
            return
        title = args[0]
        options = args[1:]
        print(f"\n📊 Poll: {title}")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print("\nReact with numbers to vote!")
    
    def bot_remind(self, args):
        """Set a reminder"""
        if len(args) < 2:
            print("❌ Usage: !remind <time> <message>")
            return
        time = args[0]
        message = ' '.join(args[1:])
        self.reminders.append((self.current_user, time, message))
        print(f"⏰ I'll remind you: {message} (in {time})")
    
    def bot_reminders(self, args):
        """List all reminders"""
        user_reminders = [r for r in self.reminders if r[0] == self.current_user]
        if user_reminders:
            print("\n📝 Your Reminders:")
            for i, (_, time, message) in enumerate(user_reminders, 1):
                print(f"{i}. In {time}: {message}")
        else:
            print("❌ You have no reminders")
    
    def bot_stats(self, args):
        """Show server statistics"""
        print(f"""
📊 Server Statistics for {self.server_name}:

👥 Members:
  Total Members: {len(self.join_dates)}
  Active Today: {len(self.active_users)}
  Banned Users: {len(self.banned_users)}
  Muted Users: {len(self.muted_users)}

📈 Activity:
  Total Messages: {sum(self.message_count.values())}
  Most Active User: {max(self.message_count.items(), key=lambda x: x[1])[0]}
  Custom Commands: {len(self.custom_commands)}

⚙️ Settings:
  Prefix: {self.server_settings['prefix']}
  Slowmode: {self.server_settings['slowmode']}s
  Welcome Channel: #{self.server_settings['welcome_channel']}
  Log Channel: #{self.server_settings['log_channel']}
        """)
    
    def bot_userinfo(self, args):
        """Show user information"""
        user = args[0] if args else self.current_user
        join_date = self.join_dates.get(user, datetime.now())
        roles_list = self.roles.get(user, [])
        print(f"""
👤 User Information for {user}:

📅 Join Date: {join_date.strftime('%Y-%m-%d')}
👑 Roles: {', '.join(roles_list) if roles_list else 'No roles'}
📊 Messages Sent: {self.message_count[user]}
⭐ Level: {self.levels[user]}
🏆 XP: {self.xp[user]}
        """)
    
    def bot_activity(self, args):
        """Show server activity"""
        print("\n📈 Server Activity:")
        for user, count in sorted(self.message_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {user}: {count} messages")
    
    def bot_leaderboard(self, args):
        """Show XP leaderboard"""
        print("\n🏆 XP Leaderboard:")
        sorted_users = sorted(self.xp.items(), key=lambda x: x[1], reverse=True)[:5]
        for i, (user, xp) in enumerate(sorted_users, 1):
            print(f"{i}. {user}: Level {self.levels[user]} ({xp} XP)")
    
    def _log_action(self, action, target, reason=None):
        """Log moderator actions"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {action.upper()}: {target}"
        if reason:
            log_message += f" | Reason: {reason}"
        print(f"\n📝 #{self.server_settings['log_channel']}: {log_message}")

    # Include all previous commands (say, roll, 8ball, coin, level, addxp, etc.)
    def bot_say(self, args):
        """Make the bot say something"""
        if args:
            message = ' '.join(args)
            print(f"🤖 {message}")
        else:
            print("❌ Please provide a message")
    
    def bot_roll(self, args):
        """Roll a dice"""
        sides = int(args[0]) if args and args[0].isdigit() else 6
        result = random.randint(1, sides)
        print(f"🎲 You rolled a {result} (d{sides})!")
    
    def bot_8ball(self, args):
        """Magic 8-ball"""
        responses = [
            "It is certain.", "Without a doubt.", "Yes, definitely.",
            "Don't count on it.", "My sources say no.", "Very doubtful.",
            "Cannot predict now.", "Ask again later.", "Better not tell you now."
        ]
        if args:
            print(f"🎱 {random.choice(responses)}")
        else:
            print("❌ Please ask a question")
    
    def bot_coin(self, args):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        print(f"🪙 {result}!")
    
    def bot_level(self, args):
        """Check XP level"""
        user = args[0] if args else self.current_user
        xp = self.xp[user]
        level = self.levels[user]
        print(f"""
📊 Level Stats for {user}:
Level: {level}
XP: {xp}
Progress to Next Level: {xp % 100}/100 XP
        """)
    
    def bot_addxp(self, args):
        """Simulate gaining XP"""
        if args and args[0].isdigit():
            amount = int(args[0])
            self.xp[self.current_user] += amount
            new_level = self.xp[self.current_user] // 100
            if new_level > self.levels[self.current_user]:
                self.levels[self.current_user] = new_level
                print(f"🎉 Level Up! You are now level {new_level}!")
            print(f"✨ Gained {amount} XP!")
        else:
            print("❌ Please provide a valid XP amount")
    
    def bot_addcmd(self, args):
        """Add a custom command"""
        if len(args) >= 2:
            cmd_name = args[0]
            response = ' '.join(args[1:])
            self.custom_commands[cmd_name] = response
            print(f"✅ Added custom command: !{cmd_name}")
        else:
            print("❌ Usage: !addcmd <name> <response>")
    
    def bot_listcmd(self, args):
        """List all custom commands"""
        if self.custom_commands:
            print("\n📝 Custom Commands:")
            for cmd, response in self.custom_commands.items():
                print(f"!{cmd} -> {response}")
        else:
            print("❌ No custom commands found")
    
    def bot_delcmd(self, args):
        """Delete a custom command"""
        if not args:
            print("❌ Please specify a command to delete")
            return
        cmd_name = args[0]
        if cmd_name in self.custom_commands:
            del self.custom_commands[cmd_name]
            print(f"✅ Deleted command: !{cmd_name}")
        else:
            print("❌ Command not found")

if __name__ == "__main__":
    LocalDiscordBot().cmdloop() 