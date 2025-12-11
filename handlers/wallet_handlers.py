from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy.orm import Session
from database import SessionLocal
from services import user_service, wallet_service
from utils.validators import is_valid_address
import logging

logger = logging.getLogger(__name__)

# State for ConversationHandler
ADD_WALLET_ADDRESS, ADD_WALLET_CHAIN, ADD_WALLET_NAME = range(3)

# --- Helper function to get DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- /add_wallet command ---
async def add_wallet_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation for adding a new wallet."""
    await update.message.reply_text(
        "Okay, let's add a new wallet. Please send me the **wallet address** you want to track."
    )
    return ADD_WALLET_ADDRESS

async def add_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the wallet address and asks for the chain."""
    address = update.message.text.strip()
    context.user_data['new_wallet_address'] = address
    await update.message.reply_text(
        f"Got the address: `{address}`.\n\n"
        "Now, please specify the **blockchain network** for this wallet (e.g., `ETH`, `SOL`, `BTC`).",
        parse_mode="Markdown"
    )
    return ADD_WALLET_CHAIN

async def add_wallet_chain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the chain and validates the address, then asks for a name."""
    chain = update.message.text.strip().upper()
    address = context.user_data.get('new_wallet_address')

    if not address:
        await update.message.reply_text("It seems I lost the address. Please start again with /add_wallet.")
        return ConversationHandler.END

    if not is_valid_address(address, chain):
        await update.message.reply_text(
            f"The address `{address}` is not a valid {chain} address. "
            "Please check the address and chain, and start again with /add_wallet.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    context.user_data['new_wallet_chain'] = chain
    await update.message.reply_text(
        f"Address `{address}` on {chain} looks valid! "
        "Finally, you can give this wallet a **short name** (e.g., 'My DeFi Wallet'). "
        "Or send /skip if you don't want to name it.",
        parse_mode="Markdown"
    )
    return ADD_WALLET_NAME

async def add_wallet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the optional wallet name and saves the wallet."""
    name = update.message.text.strip()
    address = context.user_data.get('new_wallet_address')
    chain = context.user_data.get('new_wallet_chain')
    telegram_user = update.effective_user

    if not address or not chain:
        await update.message.reply_text("Something went wrong. Please start again with /add_wallet.")
        return ConversationHandler.END

    # Get a database session
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        user = user_service.get_or_create_user(
            db,
            telegram_user.id,
            telegram_user.username,
            telegram_user.first_name,
            telegram_user.last_name
        )
        db.commit() # Commit user creation/update before adding wallet

        tracked_wallet = wallet_service.add_tracked_wallet(db, user, address, chain, name if name != "/skip" else None)

        if tracked_wallet:
            await update.message.reply_text(
                f"✅ Wallet `{address}` on {chain} {'(named: ' + tracked_wallet.name + ')' if tracked_wallet.name else ''} "
                "has been successfully added for tracking!"
                "\n\nUse /my_wallets to see all your tracked wallets.",
                parse_mode="Markdown"
            )
            logger.info(f"User {telegram_user.id} added wallet {address} on {chain}.")
        else:
            await update.message.reply_text(
                f"❗️ This wallet (`{address}` on {chain}) is already being tracked by you.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error adding wallet for user {telegram_user.id}: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while adding your wallet. Please try again later.")
    finally:
        next(db_gen, None) # Close the DB session

    context.user_data.clear() # Clear conversation data
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current conversation."""
    await update.message.reply_text("Operation cancelled. You can start again with /add_wallet.")
    context.user_data.clear()
    return ConversationHandler.END

# --- /my_wallets command ---
async def my_wallets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all wallets tracked by the user."""
    telegram_user = update.effective_user
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        user = user_service.get_user_by_telegram_id(db, telegram_user.id)
        if not user:
            await update.message.reply_text("You haven't registered with the bot yet. Please use /start.")
            return

        wallets = wallet_service.get_user_wallets(db, user.id)

        if not wallets:
            await update.message.reply_text("You are not tracking any wallets yet. Use /add_wallet to add one!")
            return

        response_text = "Your Tracked Wallets:\n\n"
        for i, wallet in enumerate(wallets):
            name_display = f" (`{wallet.name}`)" if wallet.name else ""
            response_text += (
                f"{i+1}. *Chain:* {wallet.chain}\n"
                f"   *Address:* `{wallet.address}`{name_display}\n"
                f"   ID: `{wallet.id}`\n\n"
            )
        response_text += "Use /remove_wallet <ID or address> to stop tracking a wallet."
        await update.message.reply_text(response_text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error fetching wallets for user {telegram_user.id}: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while fetching your wallets. Please try again later.")
    finally:
        next(db_gen, None)

# --- /remove_wallet command ---
async def remove_wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Removes a tracked wallet by ID or address."""
    if not context.args:
        await update.message.reply_text("Please provide the wallet ID or address to remove. Example: `/remove_wallet 1` or `/remove_wallet 0xAbc...`", parse_mode="Markdown")
        return

    identifier = context.args[0].strip()
    telegram_user = update.effective_user
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        user = user_service.get_user_by_telegram_id(db, telegram_user.id)
        if not user:
            await update.message.reply_text("You haven't registered with the bot yet. Please use /start.")
            return

        wallet_to_remove = None
        try:
            # Try to remove by ID
            wallet_id = int(identifier)
            wallet_to_remove = db.query(TrackedWallet).filter(
                TrackedWallet.id == wallet_id,
                TrackedWallet.user_id == user.id
            ).first()
        except ValueError:
            # If not an ID, try to remove by address
            wallet_to_remove = db.query(TrackedWallet).filter(
                TrackedWallet.address == identifier,
                TrackedWallet.user_id == user.id
            ).first()

        if wallet_to_remove:
            wallet_address = wallet_to_remove.address # Store for confirmation message
            wallet_service.remove_tracked_wallet(db, wallet_to_remove)
            await update.message.reply_text(f"🗑️ Wallet `{wallet_address}` has been removed from tracking.", parse_mode="Markdown")
            logger.info(f"User {telegram_user.id} removed wallet {wallet_address}.")
        else:
            await update.message.reply_text("Wallet not found or you don't have permission to remove it. Please check the ID or address.", parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error removing wallet for user {telegram_user.id}: {e}", exc_info=True)
        await update.message.reply_text("An error occurred while removing your wallet. Please try again later.")
    finally:
        next(db_gen, None)
