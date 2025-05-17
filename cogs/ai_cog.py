import discord
from discord.ext import commands
import os
import requests
import json

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            # Construct the full API URL with the key
            self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        else:
            self.gemini_api_url = None
            print("AICog WARNING: GEMINI_API_KEY not found in .env. AI chat features will not work.")

    @commands.command(name='ask', aliases=['chat', 'q'])
    async def ask_gemini(self, ctx, *, prompt: str):
        """Sends a prompt to the Gemini AI and returns the response.

        Example: 
        !ask What is the capital of France?
        """
        if not self.gemini_api_key:
            await ctx.send("Error: GEMINI_API_KEY not configured. Please contact the bot owner.")
            return

        if not prompt:
            await ctx.send("Please provide a question or prompt after the command. Example: `!ask Who are you?`")
            return

        headers = {
            'Content-Type': 'application/json',
        }
        # Basic payload structure for gemini-pro
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
              "temperature": 0.7, # A balance between creativity and predictability for chat
              "maxOutputTokens": 1024, # Max tokens for the response
            }
        }
        
        # self.gemini_api_url now contains the key, so we use it directly

        if not self.gemini_api_url: # Check if URL was constructed (i.e. API key was present)
            await ctx.send("Error: GEMINI_API_KEY not configured or missing. AI chat is unavailable.")
            return

        try:
            async with ctx.typing(): # Show "Bot is typing..."
                # self.gemini_api_url now contains the API key
                response = requests.post(self.gemini_api_url, headers=headers, data=json.dumps(payload), timeout=30) 
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
                
                response_json = response.json()
                
                # print(json.dumps(response_json, indent=2)) # For debugging the full response

                if response_json.get("candidates") and response_json["candidates"][0].get("content", {}).get("parts"):
                    generated_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Send response in chunks if it's too long for a single Discord message
                    if len(generated_text) > 2000:
                        for i in range(0, len(generated_text), 2000):
                            await ctx.send(generated_text[i:i+2000])
                    else:
                        await ctx.send(generated_text)
                elif response_json.get("promptFeedback"):
                    feedback = response_json.get("promptFeedback")
                    block_reason = feedback.get("blockReason", "No specific reason provided.")
                    safety_ratings = feedback.get("safetyRatings", [])
                    await ctx.send(f"Sorry, your prompt was blocked. Reason: {block_reason}. Safety Ratings: {safety_ratings}")
                else:
                    await ctx.send("Sorry, I couldn't get a valid response from the AI. The response format might have changed or an unknown error occurred.")
                    print(f"Gemini API unexpected response: {json.dumps(response_json, indent=2)}")

        except requests.exceptions.Timeout:
            await ctx.send("The request to the AI service timed out. Please try again later.")
            print("Gemini API (AICog) request timed out.")
        except requests.exceptions.HTTPError as e: # Handles 4xx/5xx from raise_for_status()
            error_message = "No response details available."
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_message = error_details.get("error", {}).get("message", e.response.text)
                except json.JSONDecodeError:
                    error_message = e.response.text
            else:
                error_message = str(e)
            await ctx.send(f"An HTTP error occurred with the AI service. Status: {e.response.status_code if e.response else 'N/A'}. Please check logs.")
            print(f"Gemini API (AICog) HTTPError: {e} - Status: {e.response.status_code if e.response else 'N/A'} - Response: {error_message}")
        except requests.exceptions.RequestException as e: # Other network issues
            error_text = e.response.text if hasattr(e, 'response') and e.response is not None else 'No response data'
            await ctx.send(f"An error occurred while communicating with the AI service. Please check logs.")
            print(f"Error calling Gemini API (AICog): {e} - Response: {error_text}")
        except json.JSONDecodeError as e:
            await ctx.send("There was an issue processing the AI's response. Please try again.")
            print(f"Error decoding JSON from Gemini API (AICog): {e}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred with the AI service. Please check logs.")
            print(f"An unexpected error occurred with Gemini API (AICog): {e}")

async def setup(bot):
    await bot.add_cog(AICog(bot))
