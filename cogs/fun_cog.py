import discord
from discord.ext import commands
import requests
import json
import os
import random

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tenor_api_key = os.getenv("TENOR_API_KEY")
        if not self.tenor_api_key:
            print("Warning: TENOR_API_KEY not found in .env. The !gif command will not work.")
        self.tenor_search_url = "https://tenor.googleapis.com/v2/search" 

    def get_meme_url(self): # Renamed to avoid conflict if we add other get_meme functions
        response = requests.get('https://meme-api.com/gimme')
        json_data = json.loads(response.text)
        return json_data['url']

    @commands.command(name='meme')
    async def meme(self, ctx):
        """Get a random meme from Reddit.

        This command fetches a random meme from popular meme subreddits.
        The memes are family-friendly and safe for work.

        Usage:
            !meme - Get a random meme

        Example:
            !meme
        """
        await ctx.send(self.get_meme_url())

    @commands.command(name='joke', aliases=['j'])
    async def joke(self, ctx):
        """Get a random joke to make you laugh!

        This command fetches a random joke from the Official Joke API.
        All jokes are family-friendly and clean.

        Usage:
            !joke - Get a random joke
            !j - Shortcut for !joke

        Example:
            !joke
            !j
        """
        try:
            response = requests.get('https://official-joke-api.appspot.com/jokes/random', timeout=10)
            response.raise_for_status()
            joke_data = response.json()
            
            # Format the joke with setup and punchline
            joke_text = f"**{joke_data['setup']}**\n\n{joke_data['punchline']}"
            await ctx.send(joke_text)
            
        except requests.exceptions.Timeout:
            await ctx.send("The joke service is taking too long to respond. Please try again later.")
        except requests.exceptions.RequestException as e:
            await ctx.send("Failed to fetch a joke. Please try again later.")
            print(f"Joke API error: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            await ctx.send("Received an invalid response from the joke service.")
            print(f"Joke API response error: {e}")
            
    @commands.command(name='uselessfact', aliases=['uf', 'fact'])
    async def useless_fact(self, ctx):
        """Learn a random useless but interesting fact!

        This command fetches a random fact that might be useless
        but is definitely interesting to know.

        Usage:
            !fact - Get a random fact
            !uf - Shortcut for !fact
            !uselessfact - Full command name

        Example:
            !fact
            !uf
            !uselessfact
        """
        try:
            response = requests.get('https://uselessfacts.jsph.pl/random.json?language=en', timeout=10)
            response.raise_for_status()
            fact_data = response.json()
            
            # Format the fact with an emoji
            fact_text = f"🤯 **Useless Fact:**\n{fact_data['text']}"
            await ctx.send(fact_text)
            
        except requests.exceptions.Timeout:
            await ctx.send("The fact service is taking too long to respond. Please try again later.")
        except requests.exceptions.RequestException as e:
            await ctx.send("Failed to fetch a fact. Please try again later.")
            print(f"Useless Facts API error: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            await ctx.send("Received an invalid response from the fact service.")
            print(f"Useless Facts API response error: {e}")
            
    @commands.command(name='compliment', aliases=['comp'])
    async def compliment(self, ctx, *, members: str = None):
        """Send a nice compliment to brighten someone's day!

        This command generates a friendly compliment. You can either get
        a compliment for yourself or send one to multiple users.
        Use @everyone to compliment everyone in the channel!

        Usage:
            !compliment - Get a compliment for yourself
            !compliment @user - Send a compliment to someone else
            !compliment @user1 @user2 - Compliment multiple users
            !compliment @everyone - Compliment everyone in the channel
            !comp - Shortcut for !compliment

        Example:
            !compliment
            !compliment @FriendlyUser
            !compliment @User1 @User2
            !compliment @everyone
            !comp
            !comp @FriendlyUser
        """
        # Get all mentioned users
        mentioned_users = ctx.message.mentions
        
        # Handle @everyone case
        if ctx.message.content.lower().strip().endswith('@everyone'):
            mentioned_users = [m for m in ctx.channel.members if not m.bot]
        
        # If no users mentioned, compliment the author
        if not mentioned_users:
            mentioned_users = [ctx.author]
        
        # Remove bot from the list if present
        mentioned_users = [m for m in mentioned_users if m != self.bot.user]
        
        if not mentioned_users:
            await ctx.send("No valid users to compliment!")
            return
            
        try:
            # Get a unique compliment for each user
            compliments = []
            for _ in range(len(mentioned_users)):
                response = requests.get('https://compliments-api.vercel.app/random', timeout=10)
                response.raise_for_status()
                compliment_data = response.json()
                compliments.append(f"🌸 {compliment_data['compliment']}")
            
            # Send compliments to each user
            for user, compliment in zip(mentioned_users, compliments):
                await ctx.send(f"{user.mention} {compliment}")
            
        except requests.exceptions.Timeout:
            await ctx.send("The compliment service is taking too long to respond. Please try again later.")
        except requests.exceptions.RequestException as e:
            await ctx.send("Failed to fetch compliments. Please try again later.")
            print(f"Complimentr API error: {e}")
            
    @commands.command(name='roast')
    async def roast(self, ctx, *, members: str = None):
        """Send a playful roast (keep it friendly!).

        This command generates a light-hearted roast. All roasts are meant
        to be funny and not hurtful. You can roast yourself, multiple users,
        or use @everyone to roast everyone in the channel.

        Usage:
            !roast - Get roasted yourself
            !roast @user - Playfully roast someone else
            !roast @user1 @user2 - Roast multiple users
            !roast @everyone - Roast everyone in the channel

        Example:
            !roast
            !roast @FriendlyUser
            !roast @User1 @User2
            !roast @everyone
        """
        # Get all mentioned users
        mentioned_users = ctx.message.mentions
        
        # Handle @everyone case
        if ctx.message.content.lower().strip().endswith('@everyone'):
            mentioned_users = [m for m in ctx.channel.members if not m.bot]
        
        # If no users mentioned, roast the author
        if not mentioned_users:
            mentioned_users = [ctx.author]
        
        # Remove bot from the list if present
        mentioned_users = [m for m in mentioned_users if m != self.bot.user]
        
        if not mentioned_users:
            await ctx.send("No valid users to roast!")
            return
            
        # Add warning about mean content
        warning = "⚠️ **Warning**: Roasts can be mean-spirited. Please use this command responsibly and only with friends who are okay with it!"
        
        try:
            # Get a unique roast for each user
            roasts = []
            for _ in range(len(mentioned_users)):
                response = requests.get('https://evilinsult.com/generate_insult.php?lang=en&type=json', timeout=10)
                response.raise_for_status()
                roast_data = response.json()
                roasts.append(f"🔥 {roast_data['insult']}")
            
            # Send warning first
            await ctx.send(warning)
            
            # Send roasts to each user
            for user, roast in zip(mentioned_users, roasts):
                await ctx.send(f"{user.mention} {roast}")
            
        except requests.exceptions.Timeout:
            await ctx.send("The roast service is taking too long to respond. Please try again later.")
        except requests.exceptions.RequestException as e:
            await ctx.send("Failed to fetch roasts. Please try again later.")
            print(f"Evil Insult API error: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            await ctx.send("Received an invalid response from the roast service.")
            print(f"Evil Insult API response error: {e}")
            

    @commands.command(name='gif', aliases=['g'])
    async def gif(self, ctx, *, search_term):
        """Search and send a random GIF.

        This command searches Tenor for GIFs matching your search term
        and sends a random one from the results.

        Usage:
            !gif <search term> - Search for a GIF
            !g <search term> - Shortcut for !gif

        Example:
            !gif cute cats
            !g happy dance
        """
        if not self.tenor_api_key:
            await ctx.send("Sorry, the GIF search service is not configured. (Missing API Key)")
            return

        if not search_term:
            await ctx.send("Please provide a search term for the GIF. Example: `!gif dancing`")
            return

        params = {
            "q": search_term,
            "key": self.tenor_api_key,
            "client_key": "my_discord_bot_v1", # Recommended by Tenor for identification
            "limit": 20,  # Number of GIFs to fetch (we'll pick one randomly)
            "media_filter": "minimal", # To get GIF URLs directly, can also use basic, etc.
            "contentfilter": "medium" # Safety filter: high, medium, low, off
        }

        try:
            response = requests.get(self.tenor_search_url, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()

            if data.get("results") and len(data["results"]) > 0:
                gif_choice = random.choice(data["results"])
                # The URL for the actual GIF is usually in media_formats -> gif -> url
                # Or sometimes a direct URL under a .url or .itemurl key for simpler formats
                # For minimal filter, it's often under `url` for the result object
                # or in media_formats -> gif -> url
                gif_url = gif_choice.get('url') # Direct URL if available from "minimal" filter
                if not gif_url and 'media_formats' in gif_choice and 'gif' in gif_choice['media_formats']:
                     gif_url = gif_choice['media_formats']['gif'].get('url')
                
                if gif_url:
                    await ctx.send(gif_url)
                else:
                    await ctx.send(f"Sorry, I found GIFs but couldn't get a valid URL for '{search_term}'.")
                    print(f"Tenor API response for '{search_term}' missing expected GIF URL structure: {gif_choice}")
            else:
                await ctx.send(f"Sorry, I couldn't find any GIFs for '{search_term}'.")

        except requests.exceptions.Timeout:
            await ctx.send("The GIF search request timed out. Please try again later.")
            print("Tenor API request timed out.")
        except requests.exceptions.HTTPError as e:
            await ctx.send(f"An HTTP error occurred with the GIF service. Please try again later.")
            print(f"Tenor API HTTPError: {e} - Response: {e.response.text if e.response else 'No response'}")
        except requests.exceptions.RequestException as e:
            await ctx.send("An error occurred while trying to reach the GIF service.")
            print(f"Tenor API RequestException: {e}")
        except json.JSONDecodeError as e:
            await ctx.send("There was an issue processing the GIF search results.")
            print(f"Tenor API JSONDecodeError: {e}")
        except Exception as e:
            await ctx.send("An unexpected error occurred while searching for a GIF.")
            print(f"Unexpected error in !gif command: {e}")


async def setup(bot):
    await bot.add_cog(FunCog(bot))
