import json
import os
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

LOG_FILE = "data/log_channels.json"

# Load existing log channels
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        LOG_CHANNELS = json.load(f)
else:
    LOG_CHANNELS = {}

def save_log_channels():
    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(LOG_CHANNELS, f, indent=2)

# ---------- commands ----------

async def set_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Admin check
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❌ Only admins can set a log channel!")
            return
    except:
        await update.message.reply_text("❌ Failed to verify admin status.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /setlog <channel_id or @channelusername>")
        return

    log_channel = context.args[0]
    LOG_CHANNELS[str(chat.id)] = log_channel
    save_log_channels()
    await update.message.reply_text(f"✅ Log channel set to {log_channel}.")

async def remove_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Admin check
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❌ Only admins can remove the log channel!")
            return
    except:
        await update.message.reply_text("❌ Failed to verify admin status.")
        return

    if str(chat.id) in LOG_CHANNELS:
        del LOG_CHANNELS[str(chat.id)]
        save_log_channels()
        await update.message.reply_text("✅ Log channel removed.")
    else:
        await update.message.reply_text("ℹ️ No log channel was set for this chat.")

# ---------- setup ----------

def setup(app):
    app.add_handler(CommandHandler("setlog", set_log))
    app.add_handler(CommandHandler("removelog", remove_log))

# ---------- help ----------
__help__ = """
**Extra Connections / Log Channels**
- /setlog <channel_id/@username> — Set a log channel for this group
- /removelog — Remove the log channel
"""

__mod_name__ = "Connections"
