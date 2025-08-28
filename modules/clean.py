# modules/clean.py
from telegram import Update, Chat
from telegram.ext import CommandHandler, ContextTypes, filters
from telegram.error import BadRequest

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete last N messages in a group."""
    chat: Chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    # Only admins
    member = await chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await message.reply_text("❌ You need to be an admin to use this command.")
        return

    if not context.args:
        await message.reply_text("Usage: /clean <number of messages>")
        return

    try:
        limit = int(context.args[0])
        if limit <= 0:
            await message.reply_text("❌ Number must be > 0.")
            return
    except ValueError:
        await message.reply_text("❌ Invalid number.")
        return

    deleted = 0
    # Fetch recent messages using get_chat_history
    try:
        # Fetch messages via bot.get_chat in v20+ doesn't support history,
        # so we must delete messages from the update.message.message_id backward
        current_msg_id = message.message_id
        for msg_id in range(current_msg_id, current_msg_id - limit - 1, -1):
            try:
                await context.bot.delete_message(chat.id, msg_id)
                deleted += 1
            except BadRequest:
                continue
    except Exception as e:
        await message.reply_text(f"❌ Error deleting messages: {e}")
        return

    await message.reply_text(f"✅ Deleted {deleted} messages.")


def setup(app):
    app.add_handler(CommandHandler("clean", clean, filters=filters.ChatType.GROUPS))
