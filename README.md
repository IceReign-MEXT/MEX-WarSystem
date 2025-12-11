# MEX WarSystem Bot

A powerful multi-chain cryptocurrency tracking and alert bot designed for Telegram.
This bot allows users to track their wallets across various blockchain networks (Ethereum, Solana, Bitcoin)
and receive real-time updates and alerts.

## Features

*   **Multi-Chain Wallet Tracking:** Monitor balances and activity for ETH, SOL, BTC addresses.
*   **User Management:** Securely register and manage user profiles.
*   **Wallet Management:** Add, view, and remove tracked cryptocurrency wallets.
*   **Price Alerts (Coming Soon):** Set custom price alerts for various cryptocurrencies.
*   **Subscription System (Coming Soon):** Premium features via a cryptocurrency-based subscription model.

## Technologies Used

*   **Python:** The core programming language.
*   **python-telegram-bot:** For Telegram Bot API integration.
*   **SQLAlchemy:** ORM for database interactions (SQLite for local development, PostgreSQL for production).
*   **Web3.py:** For Ethereum blockchain interaction.
*   **base58:** For Solana address validation.
*   **python-dotenv:** For secure environment variable management.
*   **APScheduler:** For background tasks (e.g., wallet monitoring, price checking).

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/IceReign-MEXT/MEX-WarSystem.git
cd MEX-WarSystem
