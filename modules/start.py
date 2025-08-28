from telegram.ext import CommandHandler

async def start(update, context):
    message = (
        "👋 Hello! I am **Max** — a very pro bot built with ❤️ in India 🇮🇳\n\n"
        "I am designed to manage groups, perform extra-extra tasks, and make your life easier! 💪\n\n"
        "Here’s what you can do:\n"
        "• /alive — Check if I am alive\n"
        "• /help — See all my commands and features\n\n"
        "Stay tuned, I have more cool stuff coming soon! 🚀"
    )
    await update.message.reply_text(message, parse_mode="Markdown")

def setup(app):
    app.add_handler(CommandHandler("start", start))
