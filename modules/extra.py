from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, run_async
import json
import os

LOG_FILE = "data/log_channels.json"

# Load existing log channels
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        LOG_CHANNELS = json.load(f)
else:
    LOG_CHANNELS = {}

def save_log_channels():
    with open(LOG_FILE, "w") as f:
        json.dump(LOG_CHANNELS, f, indent=2)

@run_async
def set_log(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    # Check if user is admin
    member = chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        update.message.reply_text("Only admins can set a log channel!")
        return

    if not context.args:
        update.message.reply_text("Usage: /setlog <channel_id or @channelusername>")
        return

    log_channel = context.args[0]
    LOG_CHANNELS[str(chat.id)] = log_channel
    save_log_channels()
    update.message.reply_text(f"✅ Log channel set to {log_channel}.")

@run_async
def remove_log(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    # Check if user is admin
    member = chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        update.message.reply_text("Only admins can remove the log channel!")
        return

    if str(chat.id) in LOG_CHANNELS:
        del LOG_CHANNELS[str(chat.id)]
        save_log_channels()
        update.message.reply_text("✅ Log channel removed.")
    else:
        update.message.reply_text("No log channel was set for this chat.")

def setup(app):
    app.add_handler(CommandHandler("setlog", set_log, pass_args=True))
    app.add_handler(CommandHandler("removelog", remove_log))

__help__ = """
**Extra Connections / Log Channels**
- /setlog <channel_id/@username> — Set a log channel for this group
- /removelog — Remove the log channel
"""

__mod_name__ = "Connections"
