# modules/filters_module.py
import os
import json
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

# File to store filters
DATA_DIR = "data"
FILTER_FILE = os.path.join(DATA_DIR, "filters.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Load filters from file
if os.path.exists(FILTER_FILE):
    with open(FILTER_FILE, "r", encoding="utf-8") as f:
        FILTERS = json.load(f)
else:
    FILTERS = {}  # {chat_id: {trigger: reply}}

def save_filters():
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump(FILTERS, f, indent=2)

# ---------- Admin commands ----------
async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    member = await chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await msg.reply_text("❌ You need to be an admin to add filters.")
        return

    if len(context.args) < 2:
        await msg.reply_text('Usage: /filter <trigger> <reply>. For multi-word triggers, quote them.')
        return

    trigger = context.args[0].lower()
    reply = " ".join(context.args[1:])
    FILTERS.setdefault(str(chat.id), {})[trigger] = reply
    save_filters()
    await msg.reply_text(f"✅ Filter added: '{trigger}' → '{reply}'")

async def list_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    filters_list = FILTERS.get(chat_id, {})
    if not filters_list:
        await update.effective_message.reply_text("No filters set for this chat.")
        return

    text = "📜 <b>Chat Filters:</b>\n\n"
    for trig, rep in filters_list.items():
        text += f"• <b>{trig}</b> → {rep}\n"
    await update.effective_message.reply_text(text, parse_mode="HTML")

async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await update.effective_chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await update.effective_message.reply_text("❌ You need to be an admin to remove filters.")
        return

    if not context.args:
        await update.effective_message.reply_text("Usage: /stop <trigger>")
        return

    trigger = context.args[0].lower()
    if chat_id in FILTERS and trigger in FILTERS[chat_id]:
        FILTERS[chat_id].pop(trigger)
        save_filters()
        await update.effective_message.reply_text(f"✅ Filter '{trigger}' removed.")
    else:
        await update.effective_message.reply_text("❌ This filter does not exist.")

async def stop_all_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = update.effective_user
    member = await update.effective_chat.get_member(user.id)
    if member.status not in ("administrator", "creator"):
        await update.effective_message.reply_text("❌ You need to be an admin to remove all filters.")
        return

    FILTERS[chat_id] = {}
    save_filters()
    await update.effective_message.reply_text("✅ All filters removed for this chat.")


# ---------- Message handler ----------
async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.effective_message.text
    if not text or chat_id not in FILTERS:
        return

    text_lower = text.lower()
    for trigger, reply in FILTERS[chat_id].items():
        if trigger in text_lower:
            await update.effective_message.reply_text(reply)
            break  # reply only once per message


# ---------- Register handlers ----------
def setup(app):
    app.add_handler(CommandHandler("filter", add_filter))
    app.add_handler(CommandHandler("filters", list_filters))
    app.add_handler(CommandHandler("stop", stop_filter))
    app.add_handler(CommandHandler("stopall", stop_all_filters))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_filters))


# ---------- Help text ----------
__help__ = """
Filters Module: Make your chat more lively!  
The bot will reply automatically to certain words.

Commands:
- /filter <trigger> <reply> — Bot replies with <reply> when someone says <trigger>.
- /filters — List all chat filters.
- /stop <trigger> — Remove a filter.
- /stopall — Remove ALL filters for this chat.
"""

__mod_name__ = "Filters"
