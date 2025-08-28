from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext.dispatcher import run_async

# Simulated database for storing settings per chat
welcome_settings = {}  # {chat_id: {"enabled": True/False, "message": str, "clean": True/False}}
goodbye_settings = {}  # {chat_id: {"enabled": True/False, "message": str}}

@run_async
def welcome_toggle(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": "Welcome!", "clean": False})
    
    if text in ["no", "off"]:
        welcome_settings[chat_id]["enabled"] = False
        update.message.reply_text("Welcome messages disabled.")
    else:
        welcome_settings[chat_id]["enabled"] = True
        update.message.reply_text("Welcome messages enabled.")

@run_async
def goodbye_toggle(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    goodbye_settings.setdefault(chat_id, {"enabled": True, "message": "Goodbye!"})
    
    if text in ["no", "off"]:
        goodbye_settings[chat_id]["enabled"] = False
        update.message.reply_text("Goodbye messages disabled.")
    else:
        goodbye_settings[chat_id]["enabled"] = True
        update.message.reply_text("Goodbye messages enabled.")

@run_async
def set_welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        update.message.reply_text("Please provide a welcome message text.")
        return
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": text, "clean": False})
    welcome_settings[chat_id]["message"] = text
    update.message.reply_text("Welcome message set!")

@run_async
def reset_welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    welcome_settings[chat_id]["message"] = "Welcome!"
    update.message.reply_text("Welcome message reset to default.")

@run_async
def set_goodbye(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = " ".join(context.args)
    if not text:
        update.message.reply_text("Please provide a goodbye message text.")
        return
    goodbye_settings.setdefault(chat_id, {"enabled": True, "message": text})
    goodbye_settings[chat_id]["message"] = text
    update.message.reply_text("Goodbye message set!")

@run_async
def reset_goodbye(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    goodbye_settings[chat_id]["message"] = "Goodbye!"
    update.message.reply_text("Goodbye message reset to default.")

@run_async
def clean_welcome(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = context.args[0].lower() if context.args else "on"
    welcome_settings.setdefault(chat_id, {"enabled": True, "message": "Welcome!", "clean": False})
    if text in ["no", "off"]:
        welcome_settings[chat_id]["clean"] = False
        update.message.reply_text("Old welcome messages will not be deleted.")
    else:
        welcome_settings[chat_id]["clean"] = True
        update.message.reply_text("Old welcome messages will be automatically deleted.")

def __help__():
    return """
Greetings Module: Give your members a warm welcome or a sad goodbye.

Admin commands:
- /welcome <yes/no/on/off>: Enable/disable welcome messages.
- /goodbye <yes/no/on/off>: Enable/disable goodbye messages.
- /setwelcome <text>: Set a new welcome message. Supports markdown and buttons.
- /resetwelcome: Reset the welcome message.
- /setgoodbye <text>: Set a new goodbye message.
- /resetgoodbye: Reset the goodbye message.
- /cleanwelcome <yes/no/on/off>: Delete old welcome messages automatically.
"""

__mod_name__ = "Greetings"

def setup(app):
    app.add_handler(CommandHandler("welcome", welcome_toggle))
    app.add_handler(CommandHandler("goodbye", goodbye_toggle))
    app.add_handler(CommandHandler("setwelcome", set_welcome))
    app.add_handler(CommandHandler("resetwelcome", reset_welcome))
    app.add_handler(CommandHandler("setgoodbye", set_goodbye))
    app.add_handler(CommandHandler("resetgoodbye", reset_goodbye))
    app.add_handler(CommandHandler("cleanwelcome", clean_welcome))
