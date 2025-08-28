from telegram.ext import CommandHandler

async def help_command(update, context):
    message = (
        "📜 **Max Bot Commands:**\n\n"
        "• /start — Welcome message\n"
        "• /alive — Check if I am alive\n"
        "• /help — Show this help message\n"
        "• More commands coming soon! 🚀"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
