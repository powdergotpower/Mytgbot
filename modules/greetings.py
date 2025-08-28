from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import html

# --- In-memory settings ---
welcome_settings = {}  # {chat_id: {"enabled": True/False, "message": str}}
goodbye_settings = {}  # {chat_id: {"enabled": True/False, "message": str}}


# --- Admin commands ---
async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": "Hey @{username} welcome in our Gc🎀"})

    if text in ["no", "off"]:
        welcome_settings[chat_id]["enabled"] = False
        await update.message.reply_text("✅ Welcome messages disabled.")
    else:
        welcome_settings[chat_id]["enabled"] = True
        await update.message.reply_text("✅ Welcome messages enabled.")


async def goodbye_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    goodbye_settings.setdefault(chat_id, {"enabled": True, "message": "Achha aadmi thaa"})

    if text in ["no", "off"]:
        goodbye_settings[chat_id]["enabled"] = False
        await update.message.reply_text("✅ Goodbye messages disabled.")
    else:
        goodbye_settings[chat_id]["enabled"] = True
        await update.message.reply_text("✅ Goodbye messages enabled.")


async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Please provide a welcome message text.")
        return
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": text})
    welcome_settings[chat_id]["message"] = text
    await update.message.reply_text("✅ Welcome message set!")


async def set_goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Please provide a goodbye message text.")
        return
    goodbye_settings.setdefault(chat_id, {"enabled": True, "message": text})
    goodbye_settings[chat_id]["message"] = text
    await update.message.reply_text("✅ Goodbye message set!")


# --- Auto greet handlers ---
async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = welcome_settings.get(chat_id, {"enabled": True, "message": "Hey @{username} welcome in our Gc🎀"})
    if not cfg.get("enabled", True):
        return

    for member in update.message.new_chat_members:
        text = cfg["message"]
        # Replace placeholders
        text = text.replace("{id}", str(member.id))
        text = text.replace("{first}", html.escape(member.first_name))
        text = text.replace("{username}", member.mention_html())
        await update.message.reply_text(text, parse_mode="HTML")


async def goodbye_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    cfg = goodbye_settings.get(chat_id, {"enabled": True, "message": "Achha aadmi thaa"})
    if not cfg.get("enabled", True):
        return
    if update.message.left_chat_member:
        await update.message.reply_text(cfg["message"])


# --- Setup function to add handlers ---
def setup(app):
    # Commands
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("goodbye", goodbye_toggle))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("setgoodbye", set_goodbye))

    # Auto greetings
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_message))
