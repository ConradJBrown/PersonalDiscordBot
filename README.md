# Bot README

## Table of Contents

*   [Overview](#overview)
*   [Features](#features)
*   [Usage](#usage)
*   [Configuration](#configuration)
*   [Running the Bot](#running-the-bot)
*   [Contributing](#contributing)

## Overview

This is a simple Todo bot built using Discord.py. It allows users to add, complete, and view tasks in their Discord server.

## Features

*   **Task Management**: Users can add new tasks using the `!todo add <task>` command.
*   **Task Completion**: Users can mark tasks as completed using the `!todo complete <index>` command.
*   **Task List**: The bot displays a list of all tasks, including their completion status.

## Usage

To use this bot in your Discord server:

1.  Create a new application on the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Invite the bot to your server using the link provided by the Developer Portal.
3.  Configure the bot's settings, such as its prefix and token, in the `config.py` file.

## Configuration

This bot stores its configuration in a `config.py` file. You'll need to update this file with your own settings:

*   **TOKEN**: Your bot's Discord API token.
*   **CLIENT_ID**: Your bot's client ID from the Developer Portal.
*   **PERMISSIONS_VALUE**: The permissions value for your bot, also found on the Developer Portal.

## Running the Bot

To run the bot, simply execute `python main.py` in your terminal. Make sure you have Python 3.x installed and Discord.py is up to date.

## Contributing

If you'd like to contribute to this project or use it as a starting point for your own bot:

1.  Fork this repository on GitHub.
2.  Update the `config.py` file with your own settings.
3.  Modify the `main.py` file to suit your needs.
4.  Run `python main.py` to start the bot.

Note: This bot is intended for personal use only and may not work as-is in production environments. You'll need to adapt it to fit your specific requirements.

## License

This project uses the [MIT License](https://opensource.org/licenses/MIT). See the LICENSE file for more information.
