import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler, # New: For multi-step commands
    MessageHandler,      # New: For handling text messages
    filters              # New: For filtering message types
)

from config import Config
from database import init_db # Import to initialize the database
from handlers.wallet_handlers import ( # New: Import handlers for wallet commands
    add_wallet_start, add_wallet_address, add_wallet_chain, add_wallet_name,
    cancel_command, my_wallets_command, remove_wallet_command,
    ADD_WALLET_ADDRESS, ADD_WALLET_CHAIN, ADD_WALLET_NAME # Import conversation states
)

# --- Logging Setup ---
# Configure basic logging to console. For production, consider file logging or a service.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hello {user.mention_html()}! 👋\n\n"
        "I'm the MEX Tracker Bot, designed to help you monitor your crypto wallets across multiple chains and get real-time alerts.\n\n"
        "Here's how to get started:\n"
        "Use /add_wallet to start tracking your first wallet.\n"
        "Use /help to see all available commands.\n\n"
        "I'm here to make your crypto tracking easy and professional!"
    )
    logger.info(f"User {user.id} ({user.username}) started the bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message."""
    help_text = (
        "🚀 *MEX Tracker Bot Help Menu* 🚀\n\n"
        "Here are the commands you can use:\n"
        "• /start - Welcome message and introduction.\n"
        "• /help - Display this help message.\n"
        "• /add_wallet - Start tracking a new wallet (multi-step process).\n"
        "• /my_wallets - View all your tracked wallets.\n"
        "• /remove_wallet <ID or address> - Stop tracking a wallet.\n"
        "• /set_alert <address> <price> <currency> - Set a price alert (coming soon).\n"
        "• /my_alerts - View your active price alerts (coming soon).\n"
        "• /subscribe - Information about premium features and subscriptions (coming soon).\n\n"
        "🌐 *Supported Chains*: Ethereum (ETH), Solana (SOL), Bitcoin (BTC)\n\n"
        "Feel free to reach out if you have any questions!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info(f"User {update.effective_user.id} requested help.")

# --- Main Bot Function ---
def main() -> None:
    """Starts the bot."""
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN is missing. Please set it in your .env file.")
        return

    # Initialize the database (create tables if they don't exist)
    init_db()

    # Create the Application and pass your bot's token.
    # We are including increased timeouts as a precaution for network stability.
    application = Application.builder().token(Config.BOT_TOKEN).read_timeout(20).connect_timeout(20).build()

    # Register core command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # ConversationHandler for adding wallets (multi-step process)
    add_wallet_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add_wallet", add_wallet_start)],
        states={
            # State 1: Awaiting wallet address
            ADD_WALLET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_wallet_address)],
            # State 2: Awaiting blockchain chain
            ADD_WALLET_CHAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_wallet_chain)],
            # State 3: Awaiting optional wallet name or /skip
            ADD_WALLET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_wallet_name),
                              CommandHandler("skip", add_wallet_name)], # Allow /skip for name
        },
        fallbacks=[CommandHandler("cancel", cancel_command)], # Handler to cancel the conversation
    )
    application.add_handler(add_wallet_conv_handler)

    # Register regular command handlers for wallet management
    application.add_handler(CommandHandler("my_wallets", my_wallets_command))
    application.add_handler(CommandHandler("remove_wallet", remove_wallet_command))


    # Start the Bot
    logger.info("MEX Tracker Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
