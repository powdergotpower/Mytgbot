import importlib
import os
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def load_modules(app):
    modules_folder = "modules"
    for filename in os.listdir(modules_folder):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"{modules_folder}.{module_name}")
            if hasattr(module, "setup"):
                module.setup(app)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    load_modules(app)  # load all modules
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
