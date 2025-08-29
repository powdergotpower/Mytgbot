import importlib
import os
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram import Update
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Optional: global owner (always allowed everywhere)
OWNER_ID = 123456789  # replace with your Telegram ID if you want

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, require: str = None) -> bool:
    """
    Check if user is admin with specific rights.
    require: string, e.g. "can_promote_members", "can_restrict_members"
    """
    user_id = update.effective_user.id

    # Global owner always allowed
    if user_id == OWNER_ID:
        return True

    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            chat_admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            for admin in chat_admins:
                if admin.user.id == user_id:
                    if admin.status == "creator":
                        return True  # group creator always allowed
                    if require:
                        rights = getattr(admin, require, False)
                        return rights is True
                    return True  # if no specific right required, any admin is fine
        except Exception:
            return False

    return False

def protect_admins(require: str = None):
    """
    Decorator to restrict commands to admins/owner with specific rights.
    Example: @protect_admins("can_promote_members")
    """
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await is_admin(update, context, require=require):
                await update.message.reply_text("❌ You don’t have permission to use this command.")
                return
            return await func(update, context)
        return wrapper
    return decorator

def load_modules(app):
    modules_folder = "modules"
    for filename in os.listdir(modules_folder):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"{modules_folder}.{module_name}")
            if hasattr(module, "setup"):
                module.setup(app, protect_admins)  # pass decorator to modules

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    load_modules(app)
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
