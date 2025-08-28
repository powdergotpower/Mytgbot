import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, filters

# --- CONFIG ---
CAPTCHA_WAIT = 60  # seconds to solve captcha

# Track users who need verification
pending_captcha = {}

WELCOME_TEXT = "👋 Hello {name}!\nPlease solve this captcha to continue in the group."


# --- COMMANDS ---
async def captcha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /captcha command for testing"""
    user = update.effective_user
    chat = update.effective_chat

    # Generate simple math captcha
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    answer = a + b
    pending_captcha[user.id] = {"chat_id": chat.id, "answer": answer}

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{a} + {b} = ?", callback_data=f"captcha:{answer}")]]
    )

    await update.message.reply_text(
        WELCOME_TEXT.format(name=user.first_name),
        reply_markup=keyboard
    )

    # Wait for CAPTCHA_WAIT seconds, then kick if not verified
    await asyncio.sleep(CAPTCHA_WAIT)
    if user.id in pending_captcha:
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.unban_chat_member(chat.id, user.id)  # just kick
            del pending_captcha[user.id]
        except:
            pass


async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle captcha button clicks"""
    query = update.callback_query
    user = query.from_user

    if not query.data.startswith("captcha:"):
        return

    expected = int(query.data.split(":")[1])
    if user.id not in pending_captcha:
        await query.answer("You are not pending verification or already verified!", show_alert=True)
        return

    # Correct answer
    del pending_captcha[user.id]
    await query.answer("✅ Captcha solved!")
    await query.edit_message_text(f"✅ {user.first_name} verified and allowed in the group!")


# --- SETUP ---
def setup(app):
    # Only allow /captcha in groups
    app.add_handler(CommandHandler("captcha", captcha_command, filters=filters.ChatType.GROUPS))
    app.add_handler(CallbackQueryHandler(captcha_callback, pattern=r"^captcha:"))
