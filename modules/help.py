# modules/help.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# ---------- Text blocks (HTML-safe) ----------
HOME_TEXT = (
    "🤖 <b>Max — Group Manager</b>\n"
    "Built with ❤️ in India • Fast • Reliable • Modular\n\n"
    "Select a category below to explore commands:"
)

ADMIN_TEXT = (
    "👮 <b>Admin Module</b>\n"
    "Manage your group like a pro. Reply to a user when required.\n\n"
    "<b>Commands</b>\n"
    "• <code>/promote</code> — Promote a user (reply to their message)\n"
    "• <code>/demote</code> — Demote/remove admin rights (reply)\n"
    "• <code>/adminlist</code> — Show all admins in this chat\n"
    "• <code>/pin</code> — Pin the replied message\n"
    "• <code>/unpin</code> — Unpin the currently pinned message\n"
    "• <code>/invitelink</code> — Get the group invite link\n\n"
    "ℹ️ <i>Bot must be admin with the right permissions for these actions.</i>"
)

ABOUT_TEXT = (
    "ℹ️ <b>About Max</b>\n"
    "Max is a modular Telegram bot for group management, utilities and fun.\n"
    "• Dynamic modules\n"
    "• Clean command design\n"
    "• Inline help with navigation\n"
)

UTILS_TEXT = (
    "🛠 <b>Utilities</b>\n"
    "Handy tools (more coming soon):\n"
    "• <code>/id</code> — Show your/user/chat ID\n"
    "• <code>/alive</code> — Bot health check\n"
)

# ---------- Keyboards ----------
def home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👮 Admin", callback_data="help:admin"),
         InlineKeyboardButton("🛠 Utilities", callback_data="help:utils")],
        [InlineKeyboardButton("ℹ️ About", callback_data="help:about"),
         InlineKeyboardButton("✖️ Close", callback_data="help:close")],
    ])

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="help:home"),
         InlineKeyboardButton("🏠 Home", callback_data="help:home"),
         InlineKeyboardButton("✖️ Close", callback_data="help:close")],
    ])

# ---------- Handlers ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # works in PM or groups
    if update.message:
        await update.message.reply_text(HOME_TEXT, parse_mode="HTML", reply_markup=home_kb())
    else:
        # if triggered from a callback "Back → Home"
        await update.callback_query.edit_message_text(HOME_TEXT, parse_mode="HTML", reply_markup=home_kb())

async def help_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()  # acknowledge tap so the spinner stops

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
            # If the bot can't delete (no rights), just replace content
            await q.edit_message_text("Closed. Open again with /help", parse_mode="HTML")

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    # Use a clear pattern so buttons always match
    app.add_handler(CallbackQueryHandler(help_callbacks, pattern=r"^help:"))        await help_command(update, context)

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
