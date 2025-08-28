# modules/antiflood.py
import os
import json
import asyncio
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Deque, Dict, Any, Optional

from telegram import Update, ChatPermissions
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackContext,
    ContextTypes,
    filters,
)

# ---------- Config / storage ----------
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "antiflood.json")

# Structure saved to JSON:
# {
#   "<chat_id>": {
#       "limit": int,
#       "timer": {"count": int, "duration": seconds} or None,
#       "mode": "ban"|"kick"|"mute"|"tban"|"tmute",
#       "clear": True|False
#   },
#   ...
# }

DEFAULTS = {"limit": 0, "timer": None, "mode": "mute", "clear": False}

# runtime state (not persisted)
# per chat: track last speaker and consecutive messages + msg ids
flood_state: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
    "last_user": None,
    "count": 0,
    "msg_ids": [],  # list of message ids for the consecutive messages
    "timestamps": defaultdict(lambda: deque()),  # for timed flood: user_id -> deque[timestamp]
})

# load/save helpers
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_settings() -> Dict[str, Any]:
    ensure_data_dir()
    if not os.path.isfile(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data: Dict[str, Any]):
    ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

settings = load_settings()  # in-memory cache of settings


# ---------- utilities ----------
def parse_duration(text: str) -> Optional[int]:
    """
    parse durations like '30s', '10m', '2h', '3d' -> seconds
    returns None if couldn't parse
    """
    text = text.strip().lower()
    if text in ("off", "no", "none"):
        return None
    try:
        unit = text[-1]
        num = int(text[:-1])
        if unit == "s":
            return num
        if unit == "m":
            return num * 60
        if unit == "h":
            return num * 3600
        if unit == "d":
            return num * 86400
    except Exception:
        try:
            # plain seconds?
            return int(text)
        except Exception:
            return None
    return None

async def is_user_admin(chat, user_id, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat.id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

def get_chat_settings(chat_id: int) -> Dict[str, Any]:
    return settings.get(str(chat_id), DEFAULTS.copy())

def set_chat_settings(chat_id: int, cfg: Dict[str, Any]):
    settings[str(chat_id)] = cfg
    save_settings(settings)

# ---------- punishment helpers ----------
async def punish_user(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_id: int,
    mode: str,
    duration_seconds: Optional[int],
    msg_ids_to_delete: Optional[list],
):
    bot = context.bot
    # delete messages if requested
    if msg_ids_to_delete:
        for mid in msg_ids_to_delete:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass

    # Immediate actions
    until_date = None
    if duration_seconds:
        until_date = datetime.utcnow() + timedelta(seconds=duration_seconds)

    try:
        if mode == "ban":
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        elif mode == "kick":
            # kick = ban then unban immediately to allow rejoin? We can use ban + unban
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await asyncio.sleep(1)
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        elif mode == "tban":
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id, until_date=until_date)
        elif mode == "mute":
            perms = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=perms)
        elif mode == "tmute":
            perms = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=perms, until_date=until_date)
        else:
            # unknown mode: mute as fallback
            perms = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=perms)
    except Exception as e:
        # return the exception object for reporting
        return e

    # schedule unban/unmute if temporary mode
    if mode in ("tban", "tmute") and duration_seconds:
        async def _undo():
            await asyncio.sleep(duration_seconds + 2)
            try:
                if mode == "tban":
                    await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
                elif mode == "tmute":
                    perms = ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                            can_send_polls=True, can_send_other_messages=True,
                                            can_add_web_page_previews=True, can_change_info=False,
                                            can_invite_users=True, can_pin_messages=False)
                    await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=perms)
            except Exception:
                pass
        # fire and forget
        asyncio.create_task(_undo())

    return None


# ---------- message handler (core flood detection) ----------
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler counts consecutive messages by same user AND timed floods.
    It uses chat settings (limit, timer, mode, clear).
    """
    message = update.effective_message
    if message is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type not in ("group", "supergroup"):
        return

    user = update.effective_user
    if user is None:
        return

    bot = context.bot

    # admins exempt
    try:
        bot_member = await bot.get_chat_member(chat.id, bot.id)
    except Exception:
        bot_member = None

    admin_flag = False
    try:
        mem = await bot.get_chat_member(chat.id, user.id)
        admin_flag = mem.status in ("administrator", "creator")
    except Exception:
        admin_flag = False

    if admin_flag:
        # reset counters for admins
        state = flood_state[chat.id]
        state["last_user"] = None
        state["count"] = 0
        state["msg_ids"] = []
        # also clear timestamp queue
        if user.id in state["timestamps"]:
            state["timestamps"][user.id].clear()
        return

    cfg = get_chat_settings(chat.id)
    limit = cfg.get("limit", 0)
    timer_cfg = cfg.get("timer")  # either None or {"count": int, "duration": seconds}
    mode = cfg.get("mode", "mute")
    clear = cfg.get("clear", False)

    # if antiflood disabled
    if (not limit or limit <= 0) and (not timer_cfg):
        return

    state = flood_state[chat.id]

    # --- consecutive-count logic ---
    if state["last_user"] == user.id:
        state["count"] += 1
        state["msg_ids"].append(message.message_id)
    else:
        state["last_user"] = user.id
        state["count"] = 1
        state["msg_ids"] = [message.message_id]

    # if consecutive limit triggered
    if limit and limit > 0 and state["count"] >= limit:
        # perform action
        msg_ids = state["msg_ids"][:] if clear else None
        err = await punish_user(context, chat.id, user.id, mode, None, msg_ids)
        if err:
            try:
                await message.reply_text(f"❌ Antiflood action failed: {err}")
            except Exception:
                pass
        else:
            try:
                await message.reply_text(f"⚠️ {user.mention_html()} triggered antiflood ({limit} messages). Action: {mode}", parse_mode="HTML")
            except Exception:
                pass
        # reset count for that chat
        state["last_user"] = None
        state["count"] = 0
        state["msg_ids"] = []
        # clear timestamp queue as well
        if user.id in state["timestamps"]:
            state["timestamps"][user.id].clear()
        return

    # --- timed flood logic ---
    if timer_cfg:
        count_needed = timer_cfg.get("count")
        dur = timer_cfg.get("duration")
        dq: Deque = state["timestamps"][user.id]
        now_ts = datetime.utcnow().timestamp()
        dq.append(now_ts)
        # pop old timestamps outside window
        while dq and (now_ts - dq[0]) > dur:
            dq.popleft()
        if len(dq) >= count_needed:
            # triggered
            # collect msg ids to delete if clear: we only have consecutive msg ids; timed could delete recent N messages if available
            msg_ids = state["msg_ids"][:] if clear else None
            err = await punish_user(context, chat.id, user.id, mode, None, msg_ids)
            if err:
                try:
                    await message.reply_text(f"❌ Antiflood action failed: {err}")
                except Exception:
                    pass
            else:
                try:
                    await message.reply_text(f"⚠️ {user.mention_html()} triggered timed antiflood ({count_needed} msgs in {dur}s). Action: {mode}", parse_mode="HTML")
                except Exception:
                    pass
            # reset
            dq.clear()
            state["last_user"] = None
            state["count"] = 0
            state["msg_ids"] = []
            return


# ---------- admin commands ----------
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        bot = context.bot
        # require group context
        if chat is None or chat.type not in ("group", "supergroup"):
            await update.effective_message.reply_text("This command works only in groups.")
            return
        try:
            member = await bot.get_chat_member(chat.id, user.id)
            if member.status not in ("administrator", "creator"):
                await update.effective_message.reply_text("You must be an admin to use this command.")
                return
        except Exception:
            await update.effective_message.reply_text("Could not verify admin status.")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def cmd_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    cfg = get_chat_settings(chat.id)
    text = "🛡️ <b>Antiflood settings</b>\n\n"
    text += f"• Consecutive limit: <b>{cfg.get('limit', 0)}</b>\n"
    timer = cfg.get("timer")
    if timer:
        text += f"• Timed limit: <b>{timer.get('count')}</b> messages in <b>{timer.get('duration')}s</b>\n"
    else:
        text += "• Timed limit: <b>disabled</b>\n"
    text += f"• Action: <b>{cfg.get('mode')}</b>\n"
    text += f"• Clear triggering messages: <b>{'yes' if cfg.get('clear') else 'no'}</b>\n"
    await update.effective_message.reply_text(text, parse_mode="HTML")


@admin_only
async def cmd_setflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    args = context.args or []
    if not args:
        await msg.reply_text("Usage: /setflood <number/off>")
        return
    val = args[0].lower()
    cfg = get_chat_settings(chat.id)
    if val in ("off", "no", "0"):
        cfg["limit"] = 0
        set_chat_settings(chat.id, cfg)
        await msg.reply_text("✅ Consecutive antiflood disabled.")
        return
    if not val.isdigit():
        await msg.reply_text("Please give a number (e.g. /setflood 7) or 'off'.")
        return
    n = int(val)
    if n < 3:
        await msg.reply_text("Antiflood consecutive limit must be 3 or higher, or use 'off'.")
        return
    cfg["limit"] = n
    set_chat_settings(chat.id, cfg)
    await msg.reply_text(f"✅ Set consecutive antiflood limit to {n}.")


@admin_only
async def cmd_setfloodtimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    args = context.args or []
    if not args:
        await msg.reply_text("Usage: /setfloodtimer <count> <duration|off>\nExample: /setfloodtimer 10 30s")
        return
    val = args[0].lower()
    if val in ("off", "no"):
        cfg = get_chat_settings(chat.id)
        cfg["timer"] = None
        set_chat_settings(chat.id, cfg)
        await msg.reply_text("✅ Timed antiflood disabled.")
        return
    if len(args) < 2:
        await msg.reply_text("Please provide both count and duration (e.g. 10 30s).")
        return
    try:
        count_needed = int(args[0])
    except Exception:
        await msg.reply_text("First argument must be a number.")
        return
    dur = parse_duration(args[1])
    if dur is None:
        await msg.reply_text("Couldn't parse duration. Examples: 30s, 5m, 1h, 2d")
        return
    cfg = get_chat_settings(chat.id)
    cfg["timer"] = {"count": count_needed, "duration": dur}
    set_chat_settings(chat.id, cfg)
    await msg.reply_text(f"✅ Timed antiflood: {count_needed} messages in {dur} seconds.")


@admin_only
async def cmd_floodmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    args = context.args or []
    if not args:
        await msg.reply_text("Usage: /floodmode <ban/mute/kick/tban/tmute>")
        return
    mode = args[0].lower()
    if mode not in ("ban", "mute", "kick", "tban", "tmute"):
        await msg.reply_text("Invalid mode. Choose: ban / mute / kick / tban / tmute")
        return
    cfg = get_chat_settings(chat.id)
    cfg["mode"] = mode
    # if temporary mode with parameter (like tban 3d) user can pass second arg for duration
    if mode in ("tban", "tmute") and len(args) >= 2:
        dur = parse_duration(args[1])
        if dur is None:
            await msg.reply_text("Couldn't parse duration (example: 3d, 12h). Continue without default duration.")
        else:
            # we store preferred default duration in timer field? We'll store under "temp_default"
            cfg["temp_default"] = dur
    else:
        cfg.pop("temp_default", None)
    set_chat_settings(chat.id, cfg)
    await msg.reply_text(f"✅ Antiflood action set to: {mode}")


@admin_only
async def cmd_clearflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    args = context.args or []
    if not args:
        await msg.reply_text("Usage: /clearflood <on/off>")
        return
    val = args[0].lower()
    cfg = get_chat_settings(chat.id)
    if val in ("on", "yes"):
        cfg["clear"] = True
        set_chat_settings(chat.id, cfg)
        await msg.reply_text("✅ I will delete messages that triggered antiflood.")
    else:
        cfg["clear"] = False
        set_chat_settings(chat.id, cfg)
        await msg.reply_text("✅ I will NOT delete triggering messages.")


# ---------- help text for integration ----------
__help__ = """
Antiflood — prevent spammy users by auto-acting when they send too many messages.

Commands:
 - /flood : Show antiflood settings for the chat.
 - /setflood <n/off> : Trigger after n consecutive messages (set 0/off to disable).
 - /setfloodtimer <count> <duration/off> : Timed antiflood example: /setfloodtimer 10 30s
 - /floodmode <ban/mute/kick/tban/tmute> : Action to take on flooding user.
 - /clearflood <on/off> : Whether to delete the messages that triggered the flood.
"""

# ---------- register handlers ----------
def setup(app):
    # message handler should be early priority (use group index 2 or so)
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & filters.ChatType.GROUPS, check_flood), 2)
    app.add_handler(CommandHandler("flood", cmd_flood))
    app.add_handler(CommandHandler("setflood", cmd_setflood))
    app.add_handler(CommandHandler("setfloodtimer", cmd_setfloodtimer))
    app.add_handler(CommandHandler("floodmode", cmd_floodmode))
    app.add_handler(CommandHandler("clearflood", cmd_clearflood))
