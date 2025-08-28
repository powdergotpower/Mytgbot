from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# --- HELP TEXTS ---

HOME_TEXT = """
🌟 <b>Welcome to MaxBot!</b> 🌟

Hey there! I am <b>Max</b>, your smart, friendly, and powerful group management assistant 🤖  
I help admins run their groups smoothly and keep spam under control!

Choose a section below to explore my amazing features:

🔹 <b>Admin Tools</b> – Manage your group like a pro  
🔹 <b>AntiFlood</b> – Stop spammers instantly  
🔹 <b>About</b> – Learn about me
"""

ADMIN_TEXT = """
🔐 <b>Admin Commands</b>

Keep your group safe and organized with these tools:

• <code>/promote &lt;reply&gt;</code> — Promote a member to admin  
• <code>/demote &lt;reply&gt;</code> — Demote an admin  
• <code>/pin &lt;reply&gt;</code> — Pin a message  
• <code>/unpin</code> — Unpin the last pinned message  
• <code>/adminlist</code> — See all current admins

✨ Tip: Use these commands wisely to keep your group safe!
"""

ANTIFLOOD_TEXT = """
🚫 <b>AntiFlood System</b>

Tired of spammers flooding your group?  
MaxBot automatically detects flooders and takes action:

• <code>/flood</code> — Show current flood settings  
• <code>/setflood &lt;number/off&gt;</code> — Set messages needed to trigger antiflood  
• <code>/setfloodtimer &lt;count&gt; &lt;duration&gt;</code> — Timed antiflood (messages in X seconds)  
• <code>/floodmode &lt;action&gt;</code> — Action for flooders: ban / mute / kick / tban / tmute  
• <code>/clearflood &lt;yes/no&gt;</code> — Delete flood messages automatically

💡 Example:  
• <code>/setflood 7</code> → Triggers antiflood after 7 messages  
• <code>/setfloodtimer 10 30s</code> → 10 messages in 30 seconds triggers antiflood

Keep your group peaceful and spam-free with just a few commands!
"""

ABOUT_TEXT = """
ℹ️ <b>About MaxBot</b>

👤 Developer: <a href="tg://user?id=123456789">Max</a>  
💖 Built with love in India to help manage groups  
🚀 Smart, fast, and reliable — made for every admin!  

Feel free to explore all commands and customize your group the way you like.
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
