import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    BOT_USERNAME = os.getenv("BOT_USERNAME")
    ADMIN_ID = int(os.getenv("ADMIN_ID")) if os.getenv("ADMIN_ID") else None
    ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID")) if os.getenv("ALERT_CHANNEL_ID") else None

    # Multi-Chain RPC (Mainnet)
    ETH_RPC = os.getenv("ETH_RPC")
    SOLANA_RPC = os.getenv("SOLANA_RPC")
    BSC_RPC = os.getenv("BSC_RPC") # Keep it here, but it's only loaded if present in .env

    # Owner Wallet Addresses (for project's own funds/operations)
    OWNER_WALLET_ETH = os.getenv("OWNER_WALLET_ETH")
    OWNER_WALLET_SOL = os.getenv("OWNER_WALLET_SOL")
    OWNER_WALLET_BTC = os.getenv("OWNER_WALLET_BTC")
    OWNER_WALLET_BNB = os.getenv("OWNER_WALLET_BNB") # Keep it here, loaded if present

    # API Keys (for block explorers, price aggregators, etc.)
    ETHERSCAN_API = os.getenv("ETHERSCAN_API")
    SOLSCAN_API = os.getenv("SOLSCAN_API")
    BSCSCAN_API = os.getenv("BSCSCAN_API") # Keep it here, loaded if present

    # Payment Settings for Subscriptions
    ENABLE_SUBSCRIPTIONS = os.getenv("ENABLE_SUBSCRIPTIONS", "false").lower() == "true"
    PAYMENT_METHOD = os.getenv("PAYMENT_METHOD")

    # Database Configuration (Placeholder - we'll set this up properly later)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@host:port/dbname")

    @classmethod
    def validate(cls):
        """Ensures critical configurations are present."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in the .env file.")
        if not cls.ADMIN_ID:
            print("Warning: ADMIN_ID is not set in .env. Admin features may not function.")
        if not cls.ETH_RPC:
            print("Warning: ETH_RPC is not set. Ethereum features will be limited.")
        if not cls.SOLANA_RPC:
            print("Warning: SOLANA_RPC is not set. Solana features will be limited.")
        # Add more validation as features are implemented

# Validate configurations on startup
Config.validate()
