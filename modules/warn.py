# modules/warn.py
import json
import os
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes, filters

# -------- Storage --------
DATA_FILE = "data/warnings.json"

if not os.path.exists("data"):
    os.makedirs("data")

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        WARNINGS = json.load(f)
else:
    WARNINGS = {}  # Structure: {str(chat_id): {str(user_id): {"count": int, "reasons": []}}}

def save_warnings():
    with open(DATA_FILE, "w") as f:
        json.dump(WARNINGS, f, indent=2)

# -------- Helper Functions --------
def get_user_warn(chat_id: int, user_id: int):
    chat_id, user_id = str(chat_id), str(user_id)
    return WARNINGS.setdefault(chat_id, {}).setdefault(user_id, {"count": 0, "reasons": []})

async def apply_mute(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=datetime.utcnow() + timedelta(minutes=10)  # mute 10 min
        )
        await update.effective_chat.send_message(f"⚠️ User has been muted for 10 minutes due to 3 warnings!")
    except Exception as e:
        await update.effective_chat.send_message(f"❌ Failed to mute user: {e}")

# -------- Commands --------
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to the user's message to warn them.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    reason = " ".join(context.args) or "No reason provided"

    user_warn = get_user_warn(chat_id, user.id)
    user_warn["count"] += 1
    user_warn["reasons"].append(reason)
    save_warnings()

    await update.effective_chat.send_message(
        f"⚠️ {user.mention_html()} has been warned!\n"
        f"Reason: {reason}\n"
        f"Total Warnings: {user_warn['count']}",
        parse_mode="HTML"
    )

    # Auto-mute after 3 warnings
    if user_warn["count"] >= 3:
        await apply_mute(update, context, user.id)
        user_warn["count"] = 0
        user_warn["reasons"] = []
        save_warnings()

async def show_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    elif context.args:
        user_id = context.args[0]
        user = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        user = user.user
    else:
        await update.message.reply_text("❌ Reply to a user or provide user ID to see warnings.")
        return

    user_warn = get_user_warn(update.effective_chat.id, user.id)
    count = user_warn["count"]
    reasons = user_warn["reasons"]
    text = f"⚠️ {user.mention_html()} has {count} warnings.\n"
    if reasons:
        text += "Reasons:\n" + "\n".join(f"- {r}" for r in reasons)
    else:
        text += "No reasons recorded."
    await update.message.reply_text(text, parse_mode="HTML")

async def reset_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to a user to reset their warnings.")
        return

    user = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    if chat_id in WARNINGS and str(user.id) in WARNINGS[chat_id]:
        del WARNINGS[chat_id][str(user.id)]
        save_warnings()
        await update.message.reply_text(f"✅ Warnings for {user.mention_html()} have been reset.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"ℹ️ {user.mention_html()} has no warnings.", parse_mode="HTML")

# -------- Setup --------
def setup(app):
    app.add_handler(CommandHandler("warn", warn_user, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("warnings", show_warnings, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("resetwarnings", reset_warnings, filters=filters.ChatType.GROUPS))
