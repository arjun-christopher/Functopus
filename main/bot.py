import discord
from discord.ext import commands
import os
import sys # Added for sys.path manipulation
from dotenv import load_dotenv
import asyncio

# Adjust sys.path to include the project root directory
# This allows Python to find the 'cogs' module when running bot.py from the 'main' subdirectory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def main():
    # Load environment variables from .env file in the project root
    # If running from 'main' dir, dotenv will search upwards or use the explicit path
    load_dotenv(dotenv_path=os.path.join(project_root, '.env'))
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in .env file.")
        print(f"Please ensure you have a .env file at {os.path.join(project_root, '.env')} with your bot token.")
        print("You can copy .env.example to .env and add your token there.")
        return

    intents = discord.Intents.default()
    intents.message_content = True # Enable message content intent
    intents.members = True         # Enable server members intent for on_member_join

    class CustomHelpCommand(commands.HelpCommand):
        async def send_group_help(self, group):
            embed = discord.Embed(
                title=f"📖 Help: !{group.name}",
                color=discord.Color.blue()
            )

            description = """Play Truth or Dare - The Classic Party Game!

                             Truth or Dare is an exciting party game where players take turns either
                             answering personal questions (Truth) or performing challenges (Dare).

                             Game Commands:
                             !tod start   - Start a new game session
                             !tod join    - Join an existing game
                             !tod leave   - Leave the current game
                             !tod play    - Begin playing with current players
                             !tod players - See who's playing
                             !tod end     - End the current game

                             Usage:
                                 !tod - Show this help message
                                 !tod <command> - Run a specific command
                             """

            embed.add_field(name="Description", value=description, inline=False)
            await self.get_destination().send(embed=embed)

        async def send_bot_help(self, mapping):
            embed = discord.Embed(
                title="📖 Bot Commands Guide",
                description="Here's everything I can do! Use `!help <command>` for more details.\n\u200b",
                color=discord.Color.blue()
            )

            for cog, commands in mapping.items():
                # Skip if no commands in this cog or if it's the help command
                filtered = await self.filter_commands(commands, sort=True)
                if not filtered:
                    continue
                
                # Get cog name and emoji
                cog_name = getattr(cog, "qualified_name", "Other")
                if cog_name == "FunCog":
                    cog_emoji = "🎉"  # 🎉
                    cog_display = "Fun Commands"
                elif cog_name == "GamesCog":
                    cog_emoji = "🎮"  # 🎮
                    cog_display = "Games"
                elif cog_name == "AICog":
                    cog_emoji = "🤖"  # 🤖
                    cog_display = "AI Chat"
                else:
                    cog_emoji = "⚙️"  # ⚙️
                    cog_display = cog_name

                # Add field for each cog
                command_list = []
                for cmd in filtered:
                    signature = f"`!{cmd.name}`"
                    if cmd.aliases:
                        aliases = ", ".join(f"`!{alias}`" for alias in cmd.aliases)
                        signature += f" (aliases: {aliases})"
                    brief = cmd.help.split('\n')[0] if cmd.help else 'No description'
                    if cmd.name == 'help':
                        brief = "Shows all commands organized by category"
                    command_list.append(f"{signature}\n↳ {brief}")
                
                # Add empty field for spacing if not the first category
                if embed.fields:
                    embed.add_field(name="\u200b", value="\u200b", inline=False)
                
                embed.add_field(
                    name=f"{cog_emoji} {cog_display}",
                    value="\n\n".join(command_list),
                    inline=False
                )

            channel = self.get_destination()
            await channel.send(embed=embed)

        async def send_command_help(self, command):
            embed = discord.Embed(
                title=f"📖 Help: !{command.name}",
                color=discord.Color.blue()
            )
            
            # Command signature
            signature = f"`!{command.name}`"
            if command.aliases:
                aliases = ", ".join(f"`!{alias}`" for alias in command.aliases)
                signature += f"\nAliases: {aliases}"
            embed.add_field(name="Usage", value=signature, inline=False)
            
            # Command description
            if command.name == 'help':
                description = """Get help with all available commands and features.
                                 
                                 Usage:   
                                 `!help` - View all commands and categories
                                 `!help <command>` - Get detailed help for a command

                                 Example usage:
                                 `!help` - Show this help message
                                 `!help meme` - Learn about the meme command"""
                embed.add_field(name="Description", value=description, inline=False)
            elif command.help and command.name != 'help':
                embed.add_field(name="Description", value=command.help, inline=False)
            
            channel = self.get_destination()
            await channel.send(embed=embed)

    bot = commands.Bot(
        command_prefix='!',
        intents=intents,
        help_command=CustomHelpCommand()
    )

    @bot.event
    async def on_ready():
        print(f'Logged on as {bot.user}!')
        print(f'Bot ID: {bot.user.id}')
        print('Successfully loaded cogs:')
        for cog_name in bot.cogs:
            print(f'- {cog_name}')
        print('------')

    @bot.event
    async def on_guild_join(guild):
        # Find the first text channel we can send messages in
        channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
        
        if channel:
            embed = discord.Embed(
                title="👋 Hello, I'm Functopus, your new Discord Bot!",
                description="Thanks for adding me to your server!",
                color=discord.Color.blue()
            )
            
            features = (
                "🎮 **Fun Games**\n"
                "• Multiplayer Truth or Dare\n"
                "• Classic Hangman\n"
                "• Never Have I Ever\n\n"
                "🤖 **AI Chat**\n"
                "• Ask me anything (`!ask`)\n\n"
                "😄 **Fun Activities**\n"
                "• Random Memes\n"
                "• Compliments\n"
                "• Roasts\n"
                "• Jokes\n\n"
                "🎯 **Getting Started**\n"
                "• Discover even more activities\n"
                "• Type `!help` to see all commands\n"
                "• Use `!help <command>` for detailed info\n"
            )
            
            embed.add_field(
                name="Features & Commands",
                value=features,
                inline=False
            )
            
            embed.set_footer(text="Need help? Type !help for a list of commands!")
            
            await channel.send(embed=embed)

    # Load cogs
    async def load_extensions():
        """Discord Bot Help Guide

        Get help with all available commands and features.

        Usage:
            !help - View all command categories
            !help <command> - Get detailed help for a specific command
            !help <category> - View all commands in a category

        Examples:
            !help - Shows this overview
            !help meme - Learn about the meme command
            !help Games - See all available games

        All commands are organized into categories like:
        - Fun Commands (memes, jokes, etc.)
        - Games (Truth or Dare, Hangman, etc.)
        - AI Chat (ask questions, get help)
        """
        # Cogs directory is now one level up from this script's location
        cogs_dir = os.path.join(project_root, "cogs") 
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py"):
                # Construct the module name (e.g., cogs.fun_cog)
                # The import system will use sys.path to find 'cogs'
                module_name = f"cogs.{filename[:-3]}"
                try:
                    await bot.load_extension(module_name)
                except Exception as e:
                    print(f"Failed to load extension {module_name}.")
                    print(f"[ERROR] {e}")
    
    await load_extensions()
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    # For Windows, the default event loop policy can cause issues with discord.py
    # Setting it to WindowsSelectorEventLoopPolicy can resolve these.
    if os.name == 'nt': # nt is for Windows
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
