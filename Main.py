#!/usr/bin/env python3
"""
Simple Telegram Bot - Single File Version
Using Pyrogram
"""

import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Load environment variables from .env file
def load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"')

load_env()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Please set API_ID, API_HASH, BOT_TOKEN in a .env file")
    exit(1)

# Initialize bot
app = Client("mybot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== Commands =====
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply("🤖 Hello! I am your Telegram bot. Use /help to see commands.")

@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    help_text = (
        "/start - Start bot\n"
        "/help - Show this message\n"
        "/ping - Check bot status"
    )
    await message.reply(help_text)

@app.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    await message.reply("🏓 Pong!")

# ===== Main =====
async def main():
    print("🚀 Bot is starting...")
    await app.start()
    print("✅ Bot is running!")
    await asyncio.Event().wait()  # Keeps bot running

if __name__ == "__main__":
    asyncio.run(main())
