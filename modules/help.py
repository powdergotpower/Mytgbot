from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from modules import admin  # import admin for __help__

# Main help menu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👮 Admin", callback_data="help_admin")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📜 **Max Bot Commands:**\n\n"
        "• /start — Welcome message\n"
        "• /alive — Check if I am alive\n"
        "• /help — Show this help message\n\n"
        "🔽 Select a category below:"
    )

    if update.message:
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)

# Handle button clicks
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help_admin":
        text = f"👮 **Admin Commands:**\n{admin.__help__}\n"

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="help_main")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "help_main":
        await help_command(update, context)

def setup(app):
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
