from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters, MessageHandler
from tg_bot import dispatcher

# Function to delete last X messages
async def clean_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    # Only admins can clean messages
    member = await chat.get_member(user.id)
    if not (member.status in ["administrator", "creator"]):
        await msg.reply_text("Only admins can use this command!")
        return

    args = context.args
    if not args or not args[0].isdigit():
        await msg.reply_text("Usage: /clean <number of messages>")
        return

    count = int(args[0])
    if count <= 0:
        await msg.reply_text("Please provide a number greater than 0.")
        return

    deleted = 0
    async for message in chat.get_history(limit=count + 1):
        try:
            await message.delete()
            deleted += 1
        except:
            continue

    await msg.reply_text(f"✅ Deleted {deleted} messages.", quote=False)

def setup(app):
    app.add_handler(CommandHandler("clean", clean_messages, filters=filters.ChatType.GROUPS, block=False))

__mod_name__ = "Clean"
__help__ = """
Clean module - remove unwanted messages easily.

Admin commands:
- /clean <number> : Delete the last <number> messages in the group. Only admins can use this.
"""

setup(dispatcher)
