import discord
from discord.ext import commands
import os
import requests
import json
import random
from typing import Optional

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giphy_api_key = os.getenv("GIPHY_API_KEY")
        
        if not self.giphy_api_key:
            print("Warning: GIPHY_API_KEY not found in .env. Welcome stickers will not work.")
            
        self.giphy_sticker_url = "https://api.giphy.com/v1/stickers/translate"
        self.welcome_channel_name = "general"  # Target channel for welcome messages

    async def _fetch_welcome_sticker(self) -> Optional[str]:
        """Fetch a random welcome sticker from GIPHY."""
        if not self.giphy_api_key:
            return None

        # First, search for waving welcome stickers to get total count
        search_params = {
            "api_key": self.giphy_api_key,
            "q": "welcome wave hi hello greeting",
            "limit": 1,  # We only need the total count
            "rating": "g",
            "lang": "en",
            "bundle": "messaging_non_clips"  # Focus on messaging/sticker content
        }
        
        try:
            # Get total count of available stickers
            search_url = "https://api.giphy.com/v1/stickers/search"
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            total_count = search_data.get("pagination", {}).get("total_count", 0)
            if total_count == 0:
                return None
                
            # Get a random offset (limited to first 1000 results as per GIPHY API)
            offset = min(random.randint(0, total_count - 1), 1000)
            
            # Now fetch a random waving sticker
            params = {
                "api_key": self.giphy_api_key,
                "s": "welcome wave hi",
                "weirdness": 5,  # Keep it more focused on the query
                "rating": "g",
                "bundle": "messaging_non_clips",
                "offset": offset
            }
            
            response = requests.get(self.giphy_sticker_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("data", {}).get("images", {}).get("original", {}).get("url"):
                return data["data"]["images"]["original"]["url"]
                
        except requests.exceptions.RequestException as e:
            print(f"[EventsCog] GIPHY API request error for welcome sticker: {e}")
        except json.JSONDecodeError as e:
            print(f"[EventsCog] GIPHY API JSON decode error: {e}")
        except Exception as e:
            print(f"[EventsCog] Unexpected error fetching GIPHY sticker: {e}")
            
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"{member.name}#{member.discriminator} (ID: {member.id}) just joined {member.guild.name} (ID: {member.guild.id})")

        welcome_channel = discord.utils.get(member.guild.text_channels, name=self.welcome_channel_name)

        if not welcome_channel:
            print(f"[EventsCog] Primary welcome channel '{self.welcome_channel_name}' not found in guild '{member.guild.name}'. Trying fallbacks...")
            # Fallback 1: System Channel
            welcome_channel = member.guild.system_channel
            if welcome_channel and welcome_channel.permissions_for(member.guild.me).send_messages:
                print(f"[EventsCog] Using system channel '{welcome_channel.name}' as fallback.")
            else:
                if welcome_channel: # System channel exists but bot can't send to it
                    print(f"[EventsCog] System channel '{welcome_channel.name}' found, but bot lacks send permissions. Looking for other channels...")
                else: # No system channel
                    print(f"[EventsCog] No system channel found. Looking for other text channels...")
                welcome_channel = None # Reset for next fallback
                # Fallback 2: First available text channel where bot can send messages
                for channel in member.guild.text_channels:
                    if channel.permissions_for(member.guild.me).send_messages:
                        welcome_channel = channel
                        print(f"[EventsCog] Using first available text channel '{welcome_channel.name}' as fallback.")
                        break
            
            if not welcome_channel:
                print(f"[EventsCog] No suitable fallback channel found in '{member.guild.name}' to send welcome message.")
                return

        welcome_message = f"Welcome {member.mention} to **{member.guild.name}**! 👋 We're excited to have you here!"
        
        try:
            await welcome_channel.send(welcome_message)
            print(f"[EventsCog] Sent welcome message for {member.name} to #{welcome_channel.name} in {member.guild.name}.")

            # Send a welcome sticker from GIPHY
            sticker_url = await self._fetch_welcome_sticker()
            if sticker_url:
                await welcome_channel.send(sticker_url)
                print(f"[EventsCog] Sent welcome sticker for {member.name} to #{welcome_channel.name} in {member.guild.name}.")
            else:
                print(f"[EventsCog] No welcome sticker found or API key missing for {member.name}.")

        except discord.errors.Forbidden:
            print(f"[EventsCog] Bot missing permissions to send messages in #{welcome_channel.name} of {member.guild.name}.")
        except Exception as e:
            print(f"[EventsCog] Error sending welcome message/GIF for {member.name}: {e}")

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
