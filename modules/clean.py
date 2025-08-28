from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, run_async
from telegram.error import BadRequest

@run_async
def clean_messages(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    # Check if user is admin
    member = chat.get_member(user.id)
    if member.status not in ["administrator", "creator"]:
        update.message.reply_text("Only admins can clean messages!")
        return

    args = context.args
    count = 10  # default delete 10 messages
    if args and args[0].isdigit():
        count = int(args[0])

    deleted = 0
    for msg in reversed(list(context.bot.get_chat(chat.id).get_history(limit=count))):
        try:
            msg.delete()
            deleted += 1
        except BadRequest:
            continue

    update.message.reply_text(f"✅ Cleaned {deleted} messages!", quote=False)

def setup(app):
    app.add_handler(CommandHandler("clean", clean_messages, pass_args=True))

__help__ = """
**Clean Module**
- /clean <number> — Delete last <number> messages (default 10). Admins only.
"""

__mod_name__ = "Clean"
