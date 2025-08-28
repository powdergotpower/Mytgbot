# modules/alive.py
from telegram.ext import CommandHandler

async def alive(update, context):
    """
    Responds with a simple 'I am alive!' message.
    """
    await update.message.reply_text("I am alive!")

def setup(app):
    """
    Registers the /alive command with the bot.
    """
    app.add_handler(CommandHandler("alive", alive))
