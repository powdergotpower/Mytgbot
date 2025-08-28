from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler, run_async

# In-memory storage for demonstration
# For permanent storage, we can later integrate JSON/SQL
captcha_settings = {}

CAPTCHA_TEXT = "🚨 **CAPTCHA PROTECTION**\n\nNew members must solve CAPTCHA to join the group safely."

def build_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Back", callback_data="help:main")]
    ])

@run_async
def captcha_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user

    # Admin check (replace with your own admin check)
    if not context.bot.get_chat_member(chat_id, user.id).status in ("administrator", "creator"):
        update.message.reply_text("Only admins can configure CAPTCHA.")
        return

    args = context.args
    if not args:
        status = "enabled ✅" if captcha_settings.get(chat_id, False) else "disabled ❌"
        update.message.reply_text(f"Current CAPTCHA status: {status}")
        return

    if args[0].lower() in ["on", "enable", "yes"]:
        captcha_settings[chat_id] = True
        update.message.reply_text("CAPTCHA has been **enabled** ✅", parse_mode="Markdown")
    elif args[0].lower() in ["off", "disable", "no"]:
        captcha_settings[chat_id] = False
        update.message.reply_text("CAPTCHA has been **disabled** ❌", parse_mode="Markdown")
    else:
        update.message.reply_text("Usage: /captcha <on/off>")

@run_async
def captcha_check(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if captcha_settings.get(chat_id, False):
        # Here you can implement real CAPTCHA (math, button, etc.)
        update.message.reply_text(f"{user.first_name}, please solve the CAPTCHA before sending messages!", reply_markup=build_kb())
        return "CaptchaTriggered"

def setup(app):
    app.add_handler(CommandHandler("captcha", captcha_command, pass_args=True))
    app.add_handler(MessageHandler(None, captcha_check))  # Simple catch-all for demonstration

__help__ = """
**CAPTCHA Commands**

- /captcha <on/off> — Enable or disable CAPTCHA for new members
- CAPTCHA triggers when new users join the group to prevent spam
"""

__mod_name__ = "CAPTCHA"
