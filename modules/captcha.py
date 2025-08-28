from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Example captcha text
CAPTCHA_TEXT = "Please solve this captcha to continue!"

async def captcha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Hello {update.effective_user.first_name}!\n\n{CAPTCHA_TEXT}"
    )

async def captcha_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Captcha verified! Welcome to the group.")

def setup(app):
    app.add_handler(CommandHandler("captcha", captcha_command))
    app.add_handler(CallbackQueryHandler(captcha_button_callback, pattern=r"^captcha:"))
