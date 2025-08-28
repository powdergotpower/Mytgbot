from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters
from telegram.error import BadRequest

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete last N messages in a chat"""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # Only admins can use
    member = await chat.get_member(user.id)
    if not member.status in ("administrator", "creator"):
        await message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not context.args:
        await message.reply_text("Usage: /clean <number of messages>")
        return

    try:
        limit = int(context.args[0])
        if limit <= 0:
            await message.reply_text("❌ Number of messages must be greater than 0.")
            return
    except ValueError:
        await message.reply_text("❌ Invalid number provided.")
        return

    # Delete messages
    deleted = 0
    async for msg in chat.get_history(limit=limit+1):  # include the /clean command
        try:
            await msg.delete()
            deleted += 1
        except BadRequest:
            continue

    await message.reply_text(f"✅ Deleted {deleted} messages.")


def setup(app):
    app.add_handler(CommandHandler("clean", clean, filters=filters.ChatType.GROUPS))
