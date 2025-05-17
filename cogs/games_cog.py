import discord
from discord.ext import commands
import random
import requests # For HTTP requests to Gemini and old API
import json     # For parsing JSON responses
import os       # To load environment variables
import re
import asyncio  # For async/await operations

class TruthOrDareGame:
    def __init__(self, ctx):
        self.ctx = ctx
        self.players = []
        self.current_player_index = 0
        self.is_active = False
        
    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)
            return True
        return False
        
    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)
            return True
        return False
        
    def next_player(self):
        if len(self.players) == 0:
            return None
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        return self.players[self.current_player_index]
        
    def current_player(self):
        if len(self.players) == 0:
            return None
        return self.players[self.current_player_index]

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hangman_games = {}  # Stores active hangman games {channel_id: game_state}
        self.active_tod_games = {}
        self.fallback_word_list = ["python", "discord", "hangman", "bot", "developer", "coding", "cascade", "paradigm", "magic", "wizard", "google", "gemini"]
        # Hangman drawing stages (simple text based)
        self.hangman_stages = [
            r""" 
            --------
            |      |
            |      O
            |     \|/
            |      |
            |     / \
            --------
            """,
            r"""
            --------
            |      |
            |      O
            |     \|/
            |      |
            |     /
            --------
            """,
            r"""
            --------
            |      |
            |      O
            |     \|/
            |      |
            |
            --------
            """,
            r"""
            --------
            |      |
            |      O
            |     \|/
            |
            |
            --------
            """,
            r"""
            --------
            |      |
            |      O
            |      |
            |      |
            |
            --------
            """,
            r"""
            --------
            |      |
            |      O
            |
            |
            |
            --------
            """,
            r"""
            --------
            |      |
            |
            |
            |
            |
            --------
            """
        ]
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_api_url = None
        if self.gemini_api_key:
            # Using gemini-1.5-flash as it's often good for quick, specific text generation tasks.
            # You can change to gemini-pro or other models if preferred.
            self.gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        else:
            print("GEMINI_API_KEY not found in .env. Hangman will rely on fallback list or secondary API.")

    async def _get_random_word(self):
        """Fetches a random word, prioritizing Gemini (HTTP), then old API, then fallback list."""
        # 1. Try Gemini API (HTTP)
        if self.gemini_api_url:
            prompt = ("Provide a single, common, lowercase English word between 5 and 10 letters long, suitable for a game of Hangman. "
                      "The word must be purely alphabetic. Do not include any other text, numbers, or punctuation, just the word itself. Example: 'banana'")
            
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.8, # Add some creativity
                    "maxOutputTokens": 10 # Ensure it's a short response
                }
            }

            try:
                # Note: requests.post is synchronous. For a truly async call here in an async function,
                # you'd typically use a library like httpx. For simplicity with current dependencies,
                # we'll use requests.post. If this causes blocking issues, consider httpx.
                response = requests.post(self.gemini_api_url, headers=headers, data=json.dumps(payload), timeout=10) # 10 second timeout
                response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
                
                result = response.json()
                if result and 'candidates' in result and result['candidates']:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                        word = candidate['content']['parts'][0]['text'].strip().lower()
                        # Basic validation
                        if ' ' not in word and word.isalpha() and 5 <= len(word) <= 10:
                            print(f"Gemini API (HTTP) word: {word}")
                            return word
                        else:
                            print(f"Gemini API (HTTP) returned an unsuitable word: {word}")
                    else:
                        print("Gemini API (HTTP) response missing content parts.")
                else:
                    print("Gemini API (HTTP) response missing candidates.")
            except requests.exceptions.Timeout:
                print("Gemini API (HTTP) request timed out.")
            except requests.exceptions.RequestException as e:
                print(f"Error calling Gemini API (HTTP): {e} - Response: {e.response.text if e.response else 'No response'}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from Gemini API (HTTP): {e}")
            except Exception as e:
                print(f"An unexpected error occurred with Gemini API (HTTP): {e}")
        else:
            print("Gemini API (HTTP) URL not configured.")

        # 2. Try old random word API (as a secondary option)
        try:
            response = requests.get("https://random-word-api.herokuapp.com/word", timeout=5) # 5 second timeout
            response.raise_for_status()
            word_data = response.json()
            if word_data and isinstance(word_data, list) and len(word_data) > 0:
                api_word = word_data[0].lower()
                if api_word.isalpha() and 3 <= len(api_word) <= 12:
                    print(f"Using word from random-word-api: {api_word}")
                    return api_word
        except requests.exceptions.Timeout:
            print("Old random word API request timed out.")
        except Exception as e:
            print(f"Old random word API failed: {e}")

        # 3. Fallback to local list
        fallback_word = random.choice(self.fallback_word_list)
        print(f"Using fallback word: {fallback_word}")
        return fallback_word

    def generate_hangman_display(self, word, guessed_letters):
        display = ""
        for letter in word:
            if letter in guessed_letters:
                display += letter + " "
            else:
                display += "_ "
        return display.strip()

    def get_hangman_drawing(self, attempts_left):
        # Attempts map to inverted stage index (6 attempts = stage 6, 0 attempts = stage 0)
        # Max attempts is 6, so 6 stages + initial empty stage (not used here)
        # if stages are 0 (full hangman) to 6 (empty gallows)
        # attempts_left 6 -> show empty (or almost empty)
        # attempts_left 0 -> show full hangman (index 0 of self.hangman_stages)
        stage_index = max(0, attempts_left) # Ensure index is not negative
        if stage_index < len(self.hangman_stages):
             # Invert index because more attempts left means an earlier stage (less drawing)
            return self.hangman_stages[len(self.hangman_stages) - 1 - stage_index]
        return self.hangman_stages[0] # Default to full hangman if out of bounds

    @commands.command(name='hangman', aliases=['hg'])
    async def hangman_start(self, ctx):
        """Play Hangman - Guess the Word!

        Start a classic game of Hangman where you try to guess a hidden word
        one letter at a time. You have 6 lives before the game is over!

        Game Commands:
        !hangman (or !hg) - Start a new game
        !guess <letter>   - Guess a letter
        !hstop           - Stop the current game

        How to Play:
        1. Start a game with !hangman
        2. Guess letters using !guess <letter>
        3. Try to solve the word before running out of lives!

        Game Rules:
        - One game per channel
        - 6 wrong guesses allowed
        - Only single letters accepted
        - Anyone can guess!

        Aliases:
            !hg - Short command for starting game

        Usage:
            !hangman - Start a new game
            !hg - Same as !hangman
        """
        channel_id = ctx.channel.id
        if channel_id in self.hangman_games:
            await ctx.send("A Hangman game is already in progress in this channel! Use `!guess <letter>` or `!hstop` to stop.")
            return

        chosen_word = await self._get_random_word()
        if not chosen_word:
            await ctx.send("Sorry, I couldn't fetch a random word to start the game. Please try again later.")
            return
        
        self.hangman_games[channel_id] = {
            "word": chosen_word,
            "guessed_letters": set(),
            "incorrect_guesses": set(), # Keep track of wrong letters too
            "attempts_left": 6, 
            "host": ctx.author.id 
        }

        game_state = self.hangman_games[channel_id]
        display_word = self.generate_hangman_display(chosen_word, game_state["guessed_letters"])
        drawing = self.get_hangman_drawing(game_state["attempts_left"])
        
        embed = discord.Embed(title="Hangman Game Started!", description=f"```{drawing}```", color=discord.Color.blue())
        embed.add_field(name="Word", value=f"`{display_word}`", inline=False)
        embed.add_field(name="Attempts Left", value=str(game_state["attempts_left"]), inline=True)
        embed.add_field(name="Guessed Letters", value="None yet", inline=True)
        embed.set_footer(text=f"Game started by {ctx.author.display_name}. Use !guess <letter> to play.")
        
        await ctx.send(embed=embed)

    @commands.command(name='guess')
    async def hangman_guess(self, ctx, *, letter_input: str):
        """Make a guess in the current Hangman game.

        Guess a single letter in the active Hangman game. The bot will show:
        - If the letter is in the word
        - Where the letter appears
        - How many lives are left
        - The current state of the word

        Rules:
        - Must be a single letter
        - Not case sensitive
        - Can't guess same letter twice
        - Must have active game

        Usage:
            !guess a - Guess the letter 'a'
            !guess B - Guess the letter 'b'
        """
        channel_id = ctx.channel.id
        if channel_id not in self.hangman_games:
            await ctx.send("No Hangman game is currently active in this channel. Start one with `!hangman`.")
            return

        game_state = self.hangman_games[channel_id]
        word_to_guess = game_state["word"]

        if not letter_input or len(letter_input.strip()) == 0:
            await ctx.send("Please provide a letter to guess!")
            return
            
        guess = letter_input.strip().lower()

        if len(guess) != 1 or not guess.isalpha():
            await ctx.send("Invalid guess. Please enter a single letter.")
            return

        if guess in game_state["guessed_letters"] or guess in game_state["incorrect_guesses"]:
            await ctx.send(f"You've already guessed the letter '{guess}'. Try a different one.")
            return

        message = ""
        if guess in word_to_guess:
            game_state["guessed_letters"].add(guess)
            message = f"Good guess! '{guess}' is in the word."
            # Check for win
            if all(char in game_state["guessed_letters"] for char in word_to_guess):
                drawing = self.get_hangman_drawing(game_state["attempts_left"])
                embed = discord.Embed(title="🎉 You Won! 🎉", description=f"```{drawing}```", color=discord.Color.green())
                embed.add_field(name="Word", value=f"`{word_to_guess.upper()}`", inline=False)
                embed.add_field(name="Guessed by", value=ctx.author.mention, inline=False)
                embed.set_footer(text="Game Over. Play again with !hangman")
                await ctx.send(embed=embed)
                del self.hangman_games[channel_id]
                return
        else:
            game_state["incorrect_guesses"].add(guess)
            game_state["attempts_left"] -= 1
            message = f"Sorry, '{guess}' is not in the word."
            # Check for loss
            if game_state["attempts_left"] == 0:
                drawing = self.get_hangman_drawing(game_state["attempts_left"])
                embed = discord.Embed(title="💀 You Lost! 💀", description=f"```{drawing}```", color=discord.Color.red())
                embed.add_field(name="The word was", value=f"`{word_to_guess.upper()}`", inline=False)
                embed.set_footer(text="Game Over. Play again with !hangman")
                await ctx.send(embed=embed)
                del self.hangman_games[channel_id]
                return

        # Send update message
        display_word = self.generate_hangman_display(word_to_guess, game_state["guessed_letters"])
        drawing = self.get_hangman_drawing(game_state["attempts_left"])
        guessed_so_far = ", ".join(sorted(list(game_state["guessed_letters"].union(game_state["incorrect_guesses"])))) or "None yet"

        embed = discord.Embed(title="Hangman Update", description=f"```{drawing}```\n{message}", color=discord.Color.blue())
        embed.add_field(name="Word", value=f"`{display_word}`", inline=False)
        embed.add_field(name="Attempts Left", value=str(game_state["attempts_left"]), inline=True)
        embed.add_field(name="Guessed Letters", value=guessed_so_far, inline=True)
        embed.set_footer(text=f"Guessed by {ctx.author.display_name}. Use !guess <letter>.")
        await ctx.send(embed=embed)

    @commands.command(name='hstop', aliases=['hangmanstop'])
    async def hangman_stop(self, ctx):
        """Stop the current Hangman game.

        Ends the active Hangman game in the current channel.
        The word will be revealed when the game is stopped.

        Can be used by:
        - Anyone, if they want to give up
        - Moderators to clear stuck games

        Usage:
            !hstop - Stop the current game
            !hangmanstop - Alternative command
        """
        channel_id = ctx.channel.id
        if channel_id not in self.hangman_games:
            await ctx.send("No Hangman game is currently active in this channel.")
            return

        game_state = self.hangman_games[channel_id]
        # Check permissions: game host or user with manage_messages
        can_stop = (ctx.author.id == game_state["host"] or 
                    ctx.channel.permissions_for(ctx.author).manage_messages)

        if not can_stop:
            await ctx.send("You don't have permission to stop this game. Only the starter or a moderator can.")
            return

        word_was = game_state["word"]
        del self.hangman_games[channel_id]
        await ctx.send(f"Hangman game stopped by {ctx.author.mention}. The word was: `{word_was.upper()}`")

    @commands.command(name='roll', aliases=['dice'])
    async def roll_dice(self, ctx, dice_notation: str = '1d6'):
        """Roll dice using standard notation!

        Roll any number and type of dice using standard dice notation.
        Format: NdS where N is number of dice and S is sides per die.
            NdX+M - Roll N dice with X sides and add M
            NdX-M - Roll N dice with X sides and subtract M

        Usage:
            !roll - Roll 1d6 (default)
            !roll <dice notation> - Roll specific dice

        Examples:
            !roll d20 - Roll a 20-sided die
            !roll 2d6 - Roll two 6-sided dice
            !roll 1d10+3 - Roll a 10-sided die and add 3
            !roll 3d8-2 - Roll three 8-sided dice and subtract 2
        """
        # Regex to parse dice notation: (num_dice)d(num_sides)(+/-modifier_value)
        # Examples: d6, 2d10, d20+5, 3d8-2
        pattern = re.compile(r"^(?:(\d+)?[dD])?(\d+)(?:([+-])(\d+))?$", re.IGNORECASE)
        match = pattern.match(dice_notation.strip())

        if not match:
            await ctx.send(f"Invalid dice notation: `{dice_notation}`. Examples: `d6`, `2d10`, `d20+5`.")
            return

        num_dice_str, num_sides_str, modifier_sign_str, modifier_val_str = match.groups()

        try:
            num_dice = int(num_dice_str) if num_dice_str else 1
            num_sides = int(num_sides_str)

            modifier = 0
            if modifier_sign_str and modifier_val_str:
                mod_val = int(modifier_val_str)
                if modifier_sign_str == '-':
                    modifier = -mod_val
                else:
                    modifier = mod_val
        except ValueError:
            await ctx.send("Invalid numbers in dice notation.")
            return

        # Validation
        MAX_DICE = 100
        MAX_SIDES = 1000
        MIN_SIDES = 2 # A die must have at least 2 sides

        if not (1 <= num_dice <= MAX_DICE):
            await ctx.send(f"Number of dice must be between 1 and {MAX_DICE}.")
            return
        if not (MIN_SIDES <= num_sides <= MAX_SIDES):
            await ctx.send(f"Number of sides must be between {MIN_SIDES} and {MAX_SIDES}.")
            return
        # Optional: Modifier limit if desired (e.g., +/- 1000)

        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total_sum = sum(rolls) + modifier

        original_input_notation = dice_notation.strip()
        result_str = f"{ctx.author.mention} rolled `{original_input_notation}`"

        is_simple_roll = (num_dice == 1 and modifier == 0)

        if is_simple_roll:
            result_str += f" and got: **{total_sum}** 🎲"
        else:
            rolls_display = ' + '.join(map(str, rolls))
            result_str += f":\nRolls: `{rolls_display}`"
            if modifier != 0:
                mod_op = modifier_sign_str if modifier_sign_str else ("+" if modifier > 0 else "")
                mod_val_display = abs(modifier)
                result_str += f" (Modifier: `{mod_op}{mod_val_display}`)"
            result_str += f"\nTotal: **{total_sum}** 🎲"

        if len(result_str) > 1900: # Discord message limit is 2000 characters
            result_str = f"{ctx.author.mention} rolled `{original_input_notation}`:\nTotal: **{total_sum}** 🎲\n(Individual rolls not shown due to length)"

        await ctx.send(result_str)

    @commands.command(name='flip', aliases=['toss'])
    async def flip_coin(self, ctx):
        """Flip a virtual coin!

        A simple game of chance that flips a coin and tells you if it landed
        on heads or tails. Great for making quick decisions!

        Aliases:
            !toss - Alternative command

        Usage:
            !flip - Flip a coin and see heads/tails
            !toss - Same as !flip
        """
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" 
        await ctx.send(f"{ctx.author.mention} flipped a coin and got: **{result}** {emoji}")

    @commands.group(name='tod', invoke_without_command=True, brief="Play Truth or Dare - The Classic Party Game!")
    async def truth_or_dare(self, ctx):
        """Play Truth or Dare - The Classic Party Game!

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
        await ctx.send("🎮 Truth or Dare Commands:\n"
                      "`!tod start` - Start a new game\n"
                      "`!tod play` - Begin playing\n"
                      "`!tod join` - Join the current game\n"
                      "`!tod leave` - Leave the game\n"
                      "`!tod end` - End the current game\n"
                      "`!tod players` - List current players")

    @truth_or_dare.command(name='start', brief="Start a new Truth or Dare game")
    async def tod_start(self, ctx):
        """Start a new Truth or Dare game
        
        Creates a new game session in the current channel.
        You'll be the game host and first player.
        Other players can join with !tod join
        
        Usage:
            !tod start - Start a new game session
        """
        if ctx.channel.id in self.active_tod_games:
            await ctx.send("❌ A game is already in progress in this channel!")
            return

        game = TruthOrDareGame(ctx)
        game.is_active = True
        game.add_player(ctx.author)
        self.active_tod_games[ctx.channel.id] = game

        await ctx.send(f"🎮 {ctx.author.mention} has started a new Truth or Dare game!\n"
                      "Others can join using `!tod join`\n"
                      "Start playing with `!tod play` once everyone has joined!")

    @truth_or_dare.command(name='join', brief="Join an active Truth or Dare game")
    async def tod_join(self, ctx):
        """Join an existing Truth or Dare game
        
        Join a game that's already been started in this channel.
        You can join anytime before the game begins.
        
        Usage:
            !tod join - Join the current game session
        """
        game = self.active_tod_games.get(ctx.channel.id)
        if not game or not game.is_active:
            await ctx.send("❌ No active game in this channel! Start one with `!tod start`")
            return

        if game.add_player(ctx.author):
            await ctx.send(f"✅ {ctx.author.mention} has joined the game!")
        else:
            await ctx.send(f"❌ {ctx.author.mention}, you're already in the game!")

    @truth_or_dare.command(name='leave', brief="Leave the current Truth or Dare game")
    async def tod_leave(self, ctx):
        """Leave the current Truth or Dare game
        
        Exit from the game you're currently in.
        If you're the last player, the game will end.
        
        Usage:
            !tod leave - Exit the current game
        """
        game = self.active_tod_games.get(ctx.channel.id)
        if not game or not game.is_active:
            await ctx.send("❌ No active game in this channel!")
            return

        if game.remove_player(ctx.author):
            await ctx.send(f"👋 {ctx.author.mention} has left the game!")
            if len(game.players) == 0:
                del self.active_tod_games[ctx.channel.id]
                await ctx.send("Game ended as there are no more players!")
        else:
            await ctx.send(f"❌ {ctx.author.mention}, you're not in the game!")

    @truth_or_dare.command(name='end', brief="End the current Truth or Dare game")
    async def tod_end(self, ctx):
        """End the current Truth or Dare game
        
        Stop the game in this channel.
        Only the game host or moderators can use this.
        
        Usage:
            !tod end - Stop and end the current game
        """
        game = self.active_tod_games.get(ctx.channel.id)
        if not game or not game.is_active:
            await ctx.send("❌ No active game in this channel!")
            return

        if ctx.author != game.players[0] and not ctx.author.guild_permissions.manage_messages:
            await ctx.send("❌ Only the game starter or moderators can end the game!")
            return
            
        # Set game as inactive first to stop any ongoing turns
        game.is_active = False
        
        # Remove the game from active games
        if ctx.channel.id in self.active_tod_games:
            del self.active_tod_games[ctx.channel.id]
            
        await ctx.send("🎮 Truth or Dare game has been ended!")

    @truth_or_dare.command(name='players', brief="See who's playing Truth or Dare")
    async def tod_players(self, ctx):
        """See who's playing Truth or Dare
        
        Shows a list of all players in the current game.
        The game host is marked with a star.
        
        Usage:
            !tod players - View the player list
        """
        game = self.active_tod_games.get(ctx.channel.id)
        if not game or not game.is_active:
            await ctx.send("❌ No active game in this channel!")
            return

        players_list = "\n".join([f"{'⭐ ' if i == 0 else '👤 '}{player.display_name}"
                                for i, player in enumerate(game.players)])
        await ctx.send(f"**Current Players:**\n{players_list}")

    @truth_or_dare.command(name='play', brief="Start playing Truth or Dare with current players")
    async def tod_play(self, ctx):
        """Begin the Truth or Dare game
        
        Start playing with everyone who has joined.
        Requires at least 2 players to begin.
        Each player will choose Truth or Dare on their turn.
        
        Usage:
            !tod play - Start playing the game
        """
        game = self.active_tod_games.get(ctx.channel.id)
        if not game or not game.is_active:
            await ctx.send("❌ No active game in this channel! Start one with `!tod start`")
            return

        if len(game.players) < 2:
            await ctx.send("❌ Need at least 2 players to play! Others can join with `!tod join`")
            return

        # Create buttons for Truth or Dare choice
        class TruthDareView(discord.ui.View):
            def __init__(self, current_player):
                super().__init__(timeout=30.0)
                self.value = None
                self.current_player = current_player

            @discord.ui.button(label='Truth 🤔', style=discord.ButtonStyle.green)
            async def truth(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.current_player:
                    await interaction.response.send_message("This is not your turn!", ephemeral=True)
                    return
                self.value = 'truth'
                self.stop()
                await interaction.response.defer()

            @discord.ui.button(label='Dare 😈', style=discord.ButtonStyle.red)
            async def dare(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != self.current_player:
                    await interaction.response.send_message("This is not your turn!", ephemeral=True)
                    return
                self.value = 'dare'
                self.stop()
                await interaction.response.defer()

        while ctx.channel.id in self.active_tod_games and game.is_active and len(game.players) >= 2:
            current_player = game.current_player()
            if current_player not in game.players:  # In case player left mid-game
                game.next_player()
                continue
                
            view = TruthDareView(current_player)
            
            # Ask player to choose
            try:
                prompt_msg = await ctx.send(
                    f"🎮 {current_player.mention}'s turn! Choose: Truth or Dare?",
                    view=view
                )

                # Wait for button press
                await view.wait()
                
                try:
                    await prompt_msg.delete()
                except:
                    pass  # Message already deleted or missing

                if not game.is_active or ctx.channel.id not in self.active_tod_games:
                    return  # Game was ended

                if view.value is None:
                    await ctx.send(f"❌ {current_player.mention} took too long to choose! Skipping...")
                    game.next_player()
                    continue

                # Get truth or dare question from API
                try:
                    response = requests.get(
                        f"https://api.truthordarebot.xyz/v1/{view.value}?rating=pg",
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Send the question/challenge
                    emoji = "🤔" if view.value == 'truth' else "😈"
                    await ctx.send(f"{emoji} {current_player.mention}: {data['question']}")
                    
                    # Wait for player to complete
                    await ctx.send("Type `!done` when you've completed your truth/dare!")
                    
                    def check(m):
                        return m.author == current_player and m.content.lower() == "!done" and m.channel == ctx.channel
                    
                    try:
                        done_msg = await self.bot.wait_for('message', timeout=300.0, check=check)
                        try:
                            await done_msg.delete()
                        except:
                            pass
                        await ctx.send(f"✅ {current_player.mention} has completed their {view.value}!")
                    except asyncio.TimeoutError:
                        await ctx.send(f"❌ {current_player.mention} took too long to complete their {view.value}! Skipping...")
                    
                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                    await ctx.send("❌ Failed to get a question. Skipping this turn...")
                    print(f"Truth or Dare API error: {e}")
                
                # Move to next player
                game.next_player()
                
                # Add a small delay between turns
                await asyncio.sleep(2)
                
            except discord.NotFound:
                # Message was deleted or channel is gone
                return
            except Exception as e:
                print(f"Error in Truth or Dare game: {e}")
                await ctx.send("❌ An error occurred. The game has been ended.")
                if ctx.channel.id in self.active_tod_games:
                    del self.active_tod_games[ctx.channel.id]
                return

    @commands.command(name='nhie', aliases=['neverhaveiever'])
    async def never_have_i_ever(self, ctx):
        """Play Never Have I Ever with friends!

        A fun party game where players reveal things they've never done!
        The bot will send a random statement, and players react if they HAVE done it.

        How to play:
        1. Bot sends a 'Never Have I Ever' statement
        2. React with ✅ if you have done it
        3. Wait 30 seconds to see who else has done it!
        4. Compare results and have fun discussing!

        Game Rules:
        - All statements are kept PG-13
        - You have 30 seconds to react
        - Be honest with your reactions!

        Aliases:
            !neverhaveiever - Full command version

        Usage:
            !nhie - Start a new round
            !neverhaveiever - Same as !nhie
        """
        try:
            response = requests.get("https://api.truthordarebot.xyz/v1/nhie?rating=pg13", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Create and send the message with the statement
            embed = discord.Embed(
                title="🙈 Never Have I Ever...",
                description=f"{data['question']}\n\n**React with ✅ below if you have done this!**",
                color=discord.Color.purple()
            )
            embed.set_footer(text="Results will be shown in 30 seconds...")
            
            message = await ctx.send(embed=embed)
            
            # Countdown timer (30 seconds)
            countdown_msg = await ctx.send("Time remaining: 30 seconds")
            for i in range(25, 0, -5):  # Update every 5 seconds
                await asyncio.sleep(5)
                await countdown_msg.edit(content=f"Time remaining: {i} seconds")
            
            # Final 5 seconds countdown
            for i in range(5, 0, -1):  # Update every second for last 5 seconds
                await asyncio.sleep(1)
                await countdown_msg.edit(content=f"Time remaining: {i} seconds")
            
            await countdown_msg.edit(content="Time's up! Tallying results...")
            await asyncio.sleep(1)
            await countdown_msg.delete()
            
            # Fetch the message again to get updated reactions
            message = await ctx.channel.fetch_message(message.id)
            
            # Count reactions and get users who reacted
            users = []
            reaction = discord.utils.get(message.reactions, emoji='✅')
            if reaction:
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)
            
            # Create result message
            count = len(users)
            if count == 0:
                result = "Nobody has done this! 😇"
            else:
                user_list = ", ".join([user.display_name for user in users])
                result = f"**{count}** {'person has' if count == 1 else 'people have'} done this!"
                result += f"\n👥 Who did it: {user_list}"
            
            # Send results
            result_embed = discord.Embed(
                title="Results",
                description=result,
                color=discord.Color.green() if count > 0 else discord.Color.blue()
            )
            await ctx.send(embed=result_embed)
                
        except requests.exceptions.Timeout:
            await ctx.send("The service is taking too long to respond. Please try again later.")
        except requests.exceptions.RequestException as e:
            await ctx.send("Failed to fetch a statement. Please try again later.")
            print(f"Never Have I Ever API error: {e}")
        except Exception as e:
            await ctx.send("An error occurred while running the game.")
            print(f"Never Have I Ever game error: {e}")

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
