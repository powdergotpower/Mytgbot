#!/usr/bin/env python3
"""
Simple working Telegram bot - Termux compatible
"""

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load .env file
load_dotenv()  # Make sure your .env is in the same folder

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Please set BOT_TOKEN in your environment variables")
    exit(1)

# === Command Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hello! I am your bot.\nUse /help to see commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
    )

# === Main Function ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    print("✅ Bot is starting...")
    app.run_polling()  # This will keep the bot running

if __name__ == "__main__":
    main()
