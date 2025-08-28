from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# --- Help Texts ---
HOME_TEXT = """
<b>👋 Hello, Welcome!</b>

I am <b>Max</b> — your smart group management assistant.  
I help you manage groups easily, keep things clean, and make your community safe.  

⚡ Built in India 🇮🇳 with love ❤️  
🔗 Owner: <a href="https://t.me/YourUsername">Max</a>  

Use the buttons below to explore everything I can do for you.
"""

ADMIN_TEXT = """
<b>🛡 Admin Tools</b>

Make it easy to manage your group admins!

<b>Commands:</b>
- /adminlist → List all admins in the chat
- /pin → Pin a replied message (silent by default)
- /unpin → Unpin the current pinned message
- /invitelink → Get the group’s invite link
- /promote → Promote a replied user
- /demote → Demote a replied user

✨ Stay in control of your community!
"""

UTILS_TEXT = """
<b>⚙️ Utility Tools</b>

Simple tools that make your life easier.

<b>Commands:</b>
- /alive → Check if I’m alive
- /id → Get your Telegram ID

🚀 More coming soon!
"""

ABOUT_TEXT = """
<b>ℹ️ About Max Bot</b>

🤖 Smart, fast and secure group manager.  
⚡ Designed to protect, manage, and power up your community.  

💡 Version: 1.0  
👤 Developer: <a href="https://t.me/YourUsername">Max</a>  
❤️ Built with love and passion.
"""

# --- Keyboards ---
def home_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡 Admin", callback_data="help:admin")],
        [InlineKeyboardButton("⚙️ Utils", callback_data="help:utils")],
        [InlineKeyboardButton("ℹ️ About", callback_data="help:about")],
        [InlineKeyboardButton("❌ Close", callback_data="help:close")],
    ])

def back_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="help:home")],
        [InlineKeyboardButton("❌ Close", callback_data="help:close")],
    ])

# --- Commands ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HOME_TEXT,
        parse_mode="HTML",
        reply_markup=home_kb()
    )

async def help_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "help:home":
        await q.edit_message_text(HOME_TEXT, parse_mode="HTML", reply_markup=home_kb())
    elif data == "help:admin":
        await q.edit_message_text(ADMIN_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:utils":
        await q.edit_message_text(UTILS_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:about":
        await q.edit_message_text(ABOUT_TEXT, parse_mode="HTML", reply_markup=back_kb())
    elif data == "help:close":
        try:
            await q.message.delete()
        except Exception:
            await q.edit_message_text("❌ Closed. Open again with /help", parse_mode="HTML")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callbacks, pattern=r"^help:"))
