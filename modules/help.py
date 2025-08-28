from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# --- HELP TEXTS ---

HOME_TEXT = """
<b>👋 Hello, welcome to MaxBot!</b>

I'm here to make managing your groups easier.  
Choose a section below to learn about my features:
"""

ADMIN_TEXT = """
<b>🔐 Admin Commands</b>

These tools help admins manage the group effectively:

- /promote <reply>: Promote a user to admin
- /demote <reply>: Demote an admin
- /pin <reply>: Pin a message
- /unpin: Unpin the last pinned message
"""

ANTIFLOOD_TEXT = """
<b>🚫 AntiFlood System</b>

You know how sometimes people join, send 100 messages, and ruin your chat?  
With <b>AntiFlood</b>, that happens no more!  
This system helps control spammers by muting, banning, or kicking them when they flood messages.

<b>📌 Available Commands:</b>
- <code>/flood</code> → Show the current antiflood settings.
- <code>/setflood &lt;number/off/no&gt;</code> → Set the number of consecutive messages to trigger antiflood.  
   • Example: <code>/setflood 7</code> → Triggers antiflood after 7 messages.  
   • Example: <code>/setflood off</code> → Disable antiflood.

- <code>/setfloodtimer &lt;count&gt; &lt;duration&gt;</code> → Timed antiflood. Triggers if a user sends X messages in Y seconds.  
   • Example: <code>/setfloodtimer 10 30s</code> → Triggers after 10 messages in 30 seconds.  
   • Example: <code>/setfloodtimer off</code> → Disable timed antiflood.

- <code>/floodmode &lt;action&gt;</code> → Choose action for flooders: ban / mute / kick / tban / tmute.  
   • Example: <code>/floodmode mute</code> → Mutes spammers.  
   • Example: <code>/floodmode tban 3d</code> → Temporary ban for 3 days.

- <code>/clearflood &lt;yes/no&gt;</code> → Delete the spam messages that triggered antiflood.  
   • Example: <code>/clearflood yes</code> → Auto delete flood messages.

<b>✨ Tip:</b> With antiflood, your group will stay spam-free and peaceful.
"""

ABOUT_TEXT = """
<b>ℹ️ About MaxBot</b>

👤 Developer: <a href="tg://user?id=123456789">Max</a>  
💡 Built with love to help manage your groups.  
Feel free to try all the commands and explore the features!
"""

# --- KEYBOARDS ---

def home_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Admin", callback_data="help:admin")],
        [InlineKeyboardButton("🚫 AntiFlood", callback_data="help:antiflood")],
        [InlineKeyboardButton("ℹ️ About", callback_data="help:about")],
        [InlineKeyboardButton("❌ Close", callback_data="help:close")]
    ])

def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="help:home")]
    ])

# --- HANDLERS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HOME_TEXT,
        parse_mode="HTML",
        reply_markup=home_kb()
    )

async def help_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "help:home":
        await q.edit_message_text(HOME_TEXT, parse_mode="HTML", reply_markup=home_kb())
    elif data == "help:admin":
        await q.edit_message_text(ADMIN_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:antiflood":
        await q.edit_message_text(ANTIFLOOD_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:about":
        await q.edit_message_text(ABOUT_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:close":
        try:
            await q.message.delete()
        except Exception:
            await q.edit_message_text("Closed. Open again with /help", parse_mode="HTML")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callbacks, pattern=r"^help:"))
