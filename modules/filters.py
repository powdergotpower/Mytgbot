from telegram import Update
from telegram.ext import MessageHandler, Filters, CommandHandler, CallbackContext, run_async
import json
import os

FILTER_FILE = "data/filters.json"

# Load existing filters
if os.path.exists(FILTER_FILE):
    with open(FILTER_FILE, "r") as f:
        FILTERS = json.load(f)
else:
    FILTERS = {}

def save_filters():
    with open(FILTER_FILE, "w") as f:
        json.dump(FILTERS, f, indent=2)

@run_async
def add_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if not context.args or len(context.args) < 1:
        update.message.reply_text("Usage: /addfilter <word or phrase>")
        return

    # Only admin can add
    member = chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        update.message.reply_text("Only admins can add filters!")
        return

    keyword = " ".join(context.args).lower()
    FILTERS.setdefault(str(chat.id), [])
    if keyword in FILTERS[str(chat.id)]:
        update.message.reply_text("This filter already exists!")
        return

    FILTERS[str(chat.id)].append(keyword)
    save_filters()
    update.message.reply_text(f"✅ Filter added: {keyword}")

@run_async
def remove_filter(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if not context.args or len(context.args) < 1:
        update.message.reply_text("Usage: /removefilter <word or phrase>")
        return

    member = chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        update.message.reply_text("Only admins can remove filters!")
        return

    keyword = " ".join(context.args).lower()
    if str(chat.id) in FILTERS and keyword in FILTERS[str(chat.id)]:
        FILTERS[str(chat.id)].remove(keyword)
        save_filters()
        update.message.reply_text(f"✅ Filter removed: {keyword}")
    else:
        update.message.reply_text("That filter does not exist!")

@run_async
def list_filters(update: Update, context: CallbackContext):
    chat = update.effective_chat
    filters_list = FILTERS.get(str(chat.id), [])
    if not filters_list:
        update.message.reply_text("No filters are set for this group.")
        return
    message = "**Filters for this group:**\n"
    message += "\n".join([f"• {f}" for f in filters_list])
    update.message.reply_text(message)

@run_async
def check_filters(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg_text = update.effective_message.text
    if not msg_text:
        return

    chat_filters = FILTERS.get(str(chat.id), [])
    for keyword in chat_filters:
        if keyword.lower() in msg_text.lower():
            try:
                update.effective_message.delete()
            except:
                pass
            return

def setup(app):
    app.add_handler(CommandHandler("addfilter", add_filter, pass_args=True))
    app.add_handler(CommandHandler("removefilter", remove_filter, pass_args=True))
    app.add_handler(CommandHandler("filters", list_filters))
    app.add_handler(MessageHandler(Filters.text & ~Filters.command, check_filters))

__help__ = """
**Filters Module**
- /addfilter <word/phrase> — Block a specific word or phrase
- /removefilter <word/phrase> — Remove a filter
- /filters — List all active filters
"""

__mod_name__ = "Filters"
