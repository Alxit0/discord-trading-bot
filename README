# Discord Stock Trading Bot

This is a Discord bot that allows users to buy and sell stocks, view their profiles and portfolios, and check the ranking of the richest members in the server. It leverages the Discord API, yfinance API for stock data, and an in-memory database to manage user data.

Visit [Trading Game](https://discord.gg/zanbJqyHW4) **discord server** to try out the bot. 

## Features

- **Buy/Sell Stocks**: Users can buy and sell stocks based on either price or quantity.
- **Profile**: View the profile of any user, displaying their stock holdings and net worth.
- **Portfolio**: Detailed view of a user's stock portfolio with pagination support.
- **Ranking**: Server-wide ranking of users based on their net worth.
- **Sync Commands**: Easily sync bot commands with Discord.

## Installation

### Prerequisites

- Python 3.8 or higher
- A Discord bot token. You can create a bot and get a token from the [Discord Developer Portal](https://discord.com/developers/applications).

### Setup

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/discord-stock-trading-bot.git
    cd discord-stock-trading-bot
    ```

2. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Configure the bot:**

    - Create a file named `creds.py` in the project directory.
    - Add the following content to `creds.py`:

        ```python
        BOT_TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
        OWNER_ID = YOUR_DISCORD_USER_ID
        ```

4. **Run the bot:**

    ```sh
    python main.py
    ```

## Commands

### Slash Commands

- **/profile [member]**: Displays the profile of the specified member, or the command user if no member is specified.
- **/stock <name> [range]**: Provides information and history of a stock for the past 6 months by default.
- **/portfolio [member]**: View detailed information about your stock portfolio.
- **/ranking**: Shows server members ranking by net worth.

### Buy/Sell Commands

- **/buy price <symbol> <value>**: Buy stocks worth a specified value.
- **/buy quantity <symbol> <quantity>**: Buy a specified quantity of stocks.
- **/sell price <symbol> <value>**: Sell stocks worth a specified value.
- **/sell quantity <symbol> <quantity>**: Sell a specified quantity of stocks.

### Text Commands

- **!sync**: Syncs the bot's commands with Discord. Only the bot owner can use this command.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue on GitHub.

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Discord.py](https://github.com/Rapptz/discord.py): Python wrapper for the Discord API.
- [yfinance](https://github.com/ranaroussi/yfinance): Yahoo! Finance market data downloader.
