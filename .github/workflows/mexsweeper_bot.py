
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "7488726944:AAEkA5Sfrnvq3Isou0xEAlJZf1E8bKyMQ9o"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Welcome to MexSweeper Bot!\nUse /track_eth or /track_sol to start tracking.")

async def track_eth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚧 ETH tracking coming soon.")

async def track_sol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚧 SOL tracking coming soon.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track_eth", track_eth))
    app.add_handler(CommandHandler("track_sol", track_sol))

    print("✅ MexSweeper Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
