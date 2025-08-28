from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
)

# --- simulated storage ---
welcome_settings = {}  # {chat_id: {"enabled": True/False, "message": str, "clean": True/False}}
goodbye_settings = {}  # {chat_id: {"enabled": True/False, "message": str}}


# --- admin commands ---

async def welcome_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": "Hey {name}, welcome in the chat!!!", "clean": False})

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
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": text, "clean": False})
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


# --- auto greeting handler ---

async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMemberUpdated = update.chat_member
    chat_id = update.effective_chat.id
    user = result.new_chat_member.user
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status

    # Member joined
    if old_status in ("left", "kicked") and new_status in ("member", "restricted"):
        cfg = welcome_settings.get(chat_id)
        if cfg and cfg.get("enabled", True):
            text = cfg.get("message", "Hey {name}, welcome in the chat!!!").format(name=user.mention_html())
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

    # Member left
    elif old_status in ("member", "restricted", "administrator") and new_status in ("left", "kicked"):
        cfg = goodbye_settings.get(chat_id)
        if cfg and cfg.get("enabled", True):
            text = cfg.get("message", "Achha aadmi thaa")
            await context.bot.send_message(chat_id=chat_id, text=text)


# --- setup handlers ---

def setup(app):
    # Admin commands
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("goodbye", goodbye_toggle))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("setgoodbye", set_goodbye))

    # Auto greet on join/leave
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))
