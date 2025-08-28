from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import CommandHandler, ContextTypes
from telegram.helpers import mention_html


# /promote command
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    bot = context.bot
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to a user's message to promote them 🚀")
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    try:
        bot_member = await chat.get_member(bot.id)
        if not bot_member.can_promote_members:
            await message.reply_text("I don't have permission to promote members 😢")
            return

        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_delete_messages=bot_member.can_delete_messages,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_promote_members=bot_member.can_promote_members,
        )
        await message.reply_text(f"✅ Promoted {user_name} to admin!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to promote: {e}")


# /demote command
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    bot = context.bot
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to a user's message to demote them 👎")
        return

    user_id = message.reply_to_message.from_user.id
    user_name = message.reply_to_message.from_user.first_name

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
        )
        await message.reply_text(f"✅ Demoted {user_name} from admin.")
    except Exception as e:
        await message.reply_text(f"❌ Failed to demote: {e}")


# /pin command
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to a message to pin it 📌")
        return

    try:
        await chat.pin_message(message.reply_to_message.message_id)
        await message.reply_text("📌 Message pinned!")
    except Exception as e:
        await message.reply_text(f"❌ Failed to pin: {e}")


# /unpin command
async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        await chat.unpin_message()
        await update.message.reply_text("📍 Message unpinned!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to unpin: {e}")


# /adminlist command
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    admins = await chat.get_administrators()
    text = f"👮 Admins in {chat.title}:\n\n"
    for admin in admins:
        user = admin.user
        text += f"• {user.mention_html()} ({admin.status})\n"
    await update.message.reply_html(text)


# /invitelink command
async def invitelink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    bot = context.bot

    try:
        link = await bot.export_chat_invite_link(chat.id)
        await update.message.reply_text(f"🔗 Invite link: {link}")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to get invite link: {e}")


# Register handlers
def setup(app):
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("unpin", unpin))
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("invitelink", invitelink))
