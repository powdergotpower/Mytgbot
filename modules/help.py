from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# Main /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👮 Admin", callback_data="help_admin")],
        [InlineKeyboardButton("📑 Logs", callback_data="help_logs")],
        [InlineKeyboardButton("🛠 Utilities", callback_data="help_utils")],
        [InlineKeyboardButton("ℹ️ About", callback_data="help_about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 **Max Bot Help Menu**\n\nChoose a category below to see available commands 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

# Handle button presses
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help_admin":
        text = (
            "👮 **Admin Commands**\n\n"
            "• /promote <user> — Promote a user\n"
            "• /demote <user> — Demote a user\n"
            "• /adminlist — List admins\n"
            "• /admincache — Refresh admin list\n"
            "• /anonadmin <on/off> — Allow anonymous admins\n"
            "• /adminerror <on/off> — Toggle admin error messages\n"
        )
    elif query.data == "help_logs":
        text = (
            "📑 **Log Commands**\n\n"
            "• /setlog — Set log group\n"
            "• /unsetlog — Remove log group\n"
            "• /logstatus — Show log group status\n"
        )
    elif query.data == "help_utils":
        text = (
            "🛠 **Utility Commands**\n\n"
            "• /id — Get user/chat ID\n"
            "• /ping — Check bot latency\n"
            "• /stats — Show bot stats\n"
        )
    elif query.data == "help_about":
        text = (
            "ℹ️ **About Max Bot**\n\n"
            "Made with ❤️ in India 🇮🇳\n"
            "Max Bot is a powerful group management bot.\n"
            "Stay tuned for more features 🚀"
        )
    else:
        text = "❌ Unknown option."

    await query.edit_message_text(text, parse_mode="Markdown")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_button, pattern="help_"))
