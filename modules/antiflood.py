# modules/antiflood.py
import os
import json
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, Any, Optional, List

from telegram import Update, ChatPermissions
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackContext,
    ContextTypes,
    filters,
)

# ---------- storage ----------
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "antiflood.json")

DEFAULT_CFG = {"limit": 0, "timer": None, "mode": "mute", "clear": False, "temp_default": None}
# timer stored as {"count": int, "duration": seconds}

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

_settings = load_settings()  # keyed by str(chat_id)

def get_cfg(chat_id: int) -> Dict[str, Any]:
    return _settings.get(str(chat_id), DEFAULT_CFG.copy())

def set_cfg(chat_id: int, cfg: Dict[str, Any]):
    _settings[str(chat_id)] = cfg
    save_settings(_settings)

# ---------- runtime state ----------
# per chat runtime counters
# consecutive: last_user, count, msg_ids
# timed: user_id -> deque[timestamps]
runtime_state: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
    "last_user": None,
    "count": 0,
    "msg_ids": [],
    "timestamps": defaultdict(lambda: deque()),  # user_id -> deque[timestamps]
})

# helper: parse durations like '30s', '5m', '2h', '3d' or plain seconds
def parse_duration(text: str) -> Optional[int]:
    if not text:
        return None
    txt = text.strip().lower()
    if txt in ("off", "no", "none"):
        return None
    try:
        unit = txt[-1]
        num = int(txt[:-1])
        if unit == "s":
            return num
        if unit == "m":
            return num * 60
        if unit == "h":
            return num * 3600
        if unit == "d":
            return num * 86400
    except Exception:
        # try plain integer seconds
        try:
            return int(txt)
        except Exception:
            return None
    return None

# ---------- punishment helpers ----------
async def _apply_action(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int,
                        mode: str, duration_seconds: Optional[int], msg_ids: Optional[List[int]]):
    bot = context.bot

    # delete messages if provided
    if msg_ids:
        for mid in msg_ids:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=mid)
            except Exception:
                pass

    until_date = None
    if duration_seconds:
        until_date = datetime.utcnow() + timedelta(seconds=duration_seconds)

    try:
        if mode == "ban":
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        elif mode == "kick":
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
            perms = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=perms)
    except Exception as e:
        return e

    # schedule undo for temporary actions (won't survive reboot)
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
        asyncio.create_task(_undo())

    return None

# ---------- core message handler ----------
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # skip admins
    try:
        member = await bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            # reset counters for this user
            state = runtime_state[chat.id]
            if user.id in state["timestamps"]:
                state["timestamps"][user.id].clear()
            if state["last_user"] == user.id:
                state["last_user"] = None
                state["count"] = 0
                state["msg_ids"] = []
            return
    except Exception:
        pass

    cfg = get_cfg(chat.id)
    limit = cfg.get("limit", 0)
    timer_cfg = cfg.get("timer")  # dict or None
    mode = cfg.get("mode", "mute")
    clear = cfg.get("clear", False)

    # nothing enabled
    if (not limit or limit <= 0) and (not timer_cfg):
        return

    state = runtime_state[chat.id]

    # consecutive check
    if state["last_user"] == user.id:
        state["count"] += 1
        state["msg_ids"].append(message.message_id)
    else:
        state["last_user"] = user.id
        state["count"] = 1
        state["msg_ids"] = [message.message_id]

    # trigger consecutive
    if limit and limit > 0 and state["count"] >= limit:
        msg_ids = state["msg_ids"][:] if clear else None
        # if mode is temporary and default temp duration provided, use it; else None for permanent
        duration = None
        if mode in ("tban", "tmute"):
            duration = cfg.get("temp_default")
        err = await _apply_action(context, chat.id, user.id, mode, duration, msg_ids)
        if err:
            try:
                await message.reply_text(f"❌ Antiflood action failed: {err}")
            except Exception:
                pass
        else:
            try:
                await message.reply_text(f"⚠️ {user.mention_html()} triggered antiflood ({limit} msgs). Action: {mode}", parse_mode="HTML")
            except Exception:
                pass
        # reset counters
        state["last_user"] = None
        state["count"] = 0
        state["msg_ids"] = []
        if user.id in state["timestamps"]:
            state["timestamps"][user.id].clear()
        return

    # timed flood logic
    if timer_cfg:
        count_needed = timer_cfg.get("count")
        dur = timer_cfg.get("duration")
        dq: Deque = state["timestamps"][user.id]
        now_ts = datetime.utcnow().timestamp()
        dq.append(now_ts)
        # pop older than dur
        while dq and (now_ts - dq[0]) > dur:
            dq.popleft()
        if len(dq) >= count_needed:
            msg_ids = state["msg_ids"][:] if clear else None
            duration = None
            if mode in ("tban", "tmute"):
                duration = cfg.get("temp_default")
            err = await _apply_action(context, chat.id, user.id, mode, duration, msg_ids)
            if err:
                try:
                    await message.reply_text(f"❌ Antiflood action failed: {err}")
                except Exception:
                    pass
            else:
                try:
                    await message.reply_text(f"⚠️ {user.mention_html()} triggered timed antiflood ({count_needed} in {dur}s). Action: {mode}", parse_mode="HTML")
                except Exception:
                    pass
            dq.clear()
            state["last_user"] = None
            state["count"] = 0
            state["msg_ids"] = []
            return

# ---------- admin checks (decorator-like) ----------
def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        user = update.effective_user
        bot = context.bot
        if chat is None or chat.type not in ("group", "supergroup"):
            await update.effective_message.reply_text("This command works only in groups.")
            return
        try:
            mem = await bot.get_chat_member(chat.id, user.id)
            if mem.status not in ("administrator", "creator"):
                await update.effective_message.reply_text("You must be an admin to use this command.")
                return
        except Exception:
            await update.effective_message.reply_text("Could not verify admin status.")
            return
        return await func(update, context)
    return wrapper

# ---------- admin commands ----------
@admin_only
async def cmd_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    cfg = get_cfg(chat.id)
    text = "🛡️ <b>Antiflood settings</b>\n\n"
    text += f"• Consecutive limit: <b>{cfg.get('limit', 0)}</b>\n"
    timer = cfg.get("timer")
    if timer:
        text += f"• Timed: <b>{timer.get('count')}</b> msgs in <b>{timer.get('duration')}s</b>\n"
    else:
        text += "• Timed: <b>disabled</b>\n"
    text += f"• Action: <b>{cfg.get('mode')}</b>\n"
    text += f"• Clear triggering messages: <b>{'yes' if cfg.get('clear') else 'no'}</b>\n"
    td = cfg.get("temp_default")
    if td:
        text += f"\n• Default temp duration (for tban/tmute): <b>{td}s</b>"
    await update.effective_message.reply_text(text, parse_mode="HTML")

@admin_only
async def cmd_setflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    msg = update.effective_message
    chat = update.effective_chat
    if not args:
        await msg.reply_text("Usage: /setflood <number/off>")
        return
    val = args[0].lower()
    cfg = get_cfg(chat.id)
    if val in ("off", "no", "0"):
        cfg["limit"] = 0
        set_cfg(chat.id, cfg)
        await msg.reply_text("✅ Consecutive antiflood disabled.")
        return
    if not val.isdigit():
        await msg.reply_text("Please provide a number (e.g. /setflood 7) or 'off'.")
        return
    n = int(val)
    if n < 2:
        await msg.reply_text("Minimum is 2 messages for consecutive flood (or use 'off').")
        return
    cfg["limit"] = n
    set_cfg(chat.id, cfg)
    await msg.reply_text(f"✅ Set consecutive antiflood limit to {n}.")

@admin_only
async def cmd_setfloodtimer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    msg = update.effective_message
    chat = update.effective_chat
    if not args:
        await msg.reply_text("Usage: /setfloodtimer <count> <duration/off>\nExample: /setfloodtimer 10 30s")
        return
    if args[0].lower() in ("off", "no"):
        cfg = get_cfg(chat.id)
        cfg["timer"] = None
        set_cfg(chat.id, cfg)
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
        await msg.reply_text("Couldn't parse duration. Use examples: 30s, 5m, 1h, 2d")
        return
    cfg = get_cfg(chat.id)
    cfg["timer"] = {"count": count_needed, "duration": dur}
    set_cfg(chat.id, cfg)
    await msg.reply_text(f"✅ Timed antiflood set: {count_needed} messages in {dur}s.")

@admin_only
async def cmd_floodmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    msg = update.effective_message
    chat = update.effective_chat
    if not args:
        await msg.reply_text("Usage: /floodmode <ban/mute/kick/tban/tmute> [default-duration]")
        return
    mode = args[0].lower()
    if mode not in ("ban", "mute", "kick", "tban", "tmute"):
        await msg.reply_text("Invalid mode. Choose: ban / mute / kick / tban / tmute")
        return
    cfg = get_cfg(chat.id)
    cfg["mode"] = mode
    if mode in ("tban", "tmute") and len(args) >= 2:
        dur = parse_duration(args[1])
        if dur is None:
            await msg.reply_text("Couldn't parse default duration. Example: 3d, 12h.")
        else:
            cfg["temp_default"] = dur
    else:
        cfg.pop("temp_default", None)
    set_cfg(chat.id, cfg)
    await msg.reply_text(f"✅ Antiflood action set to: {mode}")

@admin_only
async def cmd_clearflood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    msg = update.effective_message
    chat = update.effective_chat
    if not args:
        await msg.reply_text("Usage: /clearflood <on/off>")
        return
    val = args[0].lower()
    cfg = get_cfg(chat.id)
    if val in ("on", "yes"):
        cfg["clear"] = True
        set_cfg(chat.id, cfg)
        await msg.reply_text("✅ I will delete triggering messages when antiflood acts.")
    else:
        cfg["clear"] = False
        set_cfg(chat.id, cfg)
        await msg.reply_text("✅ I will NOT delete triggering messages.")

# ---------- help text integration ----------
__help__ = """
Antiflood — auto-action on users who spam.

Commands:
 - /flood : Show antiflood settings.
 - /setflood <n/off> : Trigger after n consecutive messages.
 - /setfloodtimer <count> <duration/off> : Timed antiflood (example: /setfloodtimer 10 30s).
 - /floodmode <ban/mute/kick/tban/tmute> : Set action to take.
 - /clearflood <on/off> : Whether to delete the messages that triggered the flood.
"""

# ---------- register handlers ----------
def setup(app):
    # message handler: high priority (lower index runs earlier)
    app.add_handler(MessageHandler(filters.ALL & ~filters.StatusUpdate.ALL & filters.ChatType.GROUPS, check_flood), 2)

    app.add_handler(CommandHandler("flood", cmd_flood))
    app.add_handler(CommandHandler("setflood", cmd_setflood))
    app.add_handler(CommandHandler("setfloodtimer", cmd_setfloodtimer))
    app.add_handler(CommandHandler("floodmode", cmd_floodmode))
    app.add_handler(CommandHandler("clearflood", cmd_clearflood))
