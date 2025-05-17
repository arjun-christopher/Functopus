# Functopus - Your Fun Discord Bot

<p align="center">
  <img src="media/Functopus%20Icon.png" alt="Bot Icon" width="200">
</p>

Functopus is a multi-functional Discord bot built with Python using the `discord.py` library. This friendly bot brings games, AI chat, and utility commands to your server, making it more engaging and fun!

## Features Implemented

*   **Help Commands**:
    *   `!help` - View all commands organized by category
    *   `!help <command>` - Get detailed help for a specific command (e.g., `!help meme`, `!help tod`)

*   **Meme Generation**: 
    *   `!meme`: Fetches a random meme from a predefined list of subreddits.

*   **AI Chat (powered by Gemini API)**:
    *   `!ask <prompt>` (aliases: `!chat`, `!q`): Sends a prompt to the Gemini AI and returns its response.

*   **Games**:
    *   **Truth or Dare** - Interactive multiplayer game:
        *   `!tod`: Show all available Truth or Dare commands
        *   `!tod start`: Start a new Truth or Dare game in the channel
        *   `!tod join`: Join the current game
        *   `!tod leave`: Leave the current game
        *   `!tod play`: Begin playing with current players
        *   `!tod players`: List all players in the game
        *   `!tod end`: End the current game (game starter or moderator only)
    *   **Never Have I Ever** - Party game with reaction tracking:
        *   `!nhie`: Get a random "Never Have I Ever" statement
        *   React with ✅ if you have done it
        *   After 30 seconds, see who has done it!
    *   `!hangman` (alias: `!hg`): Starts a game of Hangman.
        *   `!guess <letter>`: Allows users to guess a letter in the Hangman game.
        *   `!hstop` (alias: `!hangmanstop`): Stops the current Hangman game (can be used by the game starter or a moderator).
    *   `!roll <dice_notation>` (alias: `!r`): Rolls dice using standard D&D notation (e.g., `d6`, `2d10+5`, `3d8-2`). Defaults to `1d6` if no notation is provided.
    *   `!flip` (alias: `!toss`): Flips a coin and returns "Heads" or "Tails".

*   **Fun Commands**:
    *   `!gif <search_term>` (alias: `!g`): Fetches a GIF from Tenor based on the search term and posts it.
    *   `!joke` (alias: `!j`): Fetches and displays a random joke from the Official Joke API.
    *   `!uselessfact` (aliases: `!uf`, `!fact`): Shares a random useless fact that will blow your mind 🤯.
    *   `!compliment <@user>` (alias: `!comp`): Sends kind compliments to users. You can mention multiple users or use `@everyone` to compliment everyone in the channel 🌸.
    *   `!roast <@user>`: Sends playful roasts to users. You can mention multiple users or use `@everyone` to roast everyone in the channel 🔥. Remember to use this command responsibly and only with friends who are okay with it!

*   **Automated Events**:
    *   **Server Welcome**: When Functopus joins a new server, it introduces itself with a beautiful embedded message showcasing its features and commands.
    *   **Member Welcome**: Automatically greets new members when they join the server. Sends a customizable welcome message and a random animated welcome sticker (waving/hello themed) to a designated channel (defaults to `#general`, with fallbacks to the system channel or the first available text channel).

## Setup and Installation

1.  **Clone the Repository (or download the files):**
    ```bash
    # If it were a git repo:
    # git clone <repository_url>
    # cd <repository_name>
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Make sure you have a `requirements.txt` file with at least:
    ```
    discord.py
    python-dotenv
    requests
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    *   Create the `.env` file and add your Discord Bot Token and Gemini API Key:
        ```
        DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE  # For AI chat feature
        TENOR_API_KEY=YOUR_TENOR_API_KEY_HERE    # For !gif command
        GIPHY_API_KEY=YOUR_GIPHY_API_KEY_HERE    # For welcome stickers
        ```
    *   **Important**: 
        *   Ensure your `GEMINI_API_KEY` is active and that the "Generative Language API" (or the specific Gemini model API) is enabled in your Google Cloud Project.
        *   Ensure your `TENOR_API_KEY` is active and the Tenor API is enabled in your Google Cloud Project for the `!gif` command and welcome message GIFs.
        *   Keep your `.env` file secure and do not commit it to version control if you are using Git.

5.  **Run the Bot:**
    Navigate to the project root directory in your terminal and run:
    ```bash
    python main/bot.py
    ```
    Alternatively, you can navigate into the `main` directory and run `python bot.py`.

## Usage

Once the bot is running and has joined your Discord server, you can use the commands listed in the "Features Implemented" section. For example:
*   `!ask What is the capital of France?`
*   `!hangman`
*   `!roll d6`
*   `!flip`
*   `!meme`

---

*Last modified: May 17, 2025*
