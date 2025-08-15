#!/usr/bin/env python3
"""
🔥 Adult 18+ NSFW Telegram Bot 🔞💦😏
- Seductive welcome text
- Public & private channel verification
- Sends stored adult videos/images after verification
- Animated emoji loading/progress bar
- Admin commands: /add, /store, /status
- Fully NSFW text and emojis
"""

import json
import logging
import io
import random
from pathlib import Path
from typing import Dict
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import Forbidden, BadRequest
from PIL import Image, ImageDraw, ImageFont
import asyncio

# ---------------------------
# CONFIG
# ---------------------------
BOT_TOKEN = "8414761321:AAHPQOi-Q6qfKmmbdpmFZD3HZWWhctef1_U"
ADMIN_ID = 8156053366
DATA_FILE = Path("bot_config.json")
WELCOME_FONT_PATH = None

CHANNEL_IDS = [
    -1002703857153,
    -1002655982430,
    -1002308219804,
    -1002801896143,
    -1002476169118,
    -1002723937230,
    -1002553532761
]

# ---------------------------
# Logging
# ---------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------------------
# Persistent config
# ---------------------------
DEFAULTS = {
    "admin_id": ADMIN_ID,
    "custom_message": "💦 Aahhh… finally here 😈🔥 Ready for naughty 18+ content? 🍑💋😏",
    "videos": [],
}

def load_data() -> Dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to load config, using defaults.")
    d = DEFAULTS.copy()
    save_data(d)
    return d

def save_data(data: Dict):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------
# Welcome image
# ---------------------------
def make_welcome_image(username: str, title: str = "Aahhh... 😈💦") -> io.BytesIO:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#1a0f1a")
    draw = ImageDraw.Draw(img)

    card_w, card_h = 760, 520
    card_x, card_y = 40, 55
    draw.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=24, fill="#330033")

    try:
        if WELCOME_FONT_PATH:
            title_font = ImageFont.truetype(WELCOME_FONT_PATH, 56)
            name_font = ImageFont.truetype(WELCOME_FONT_PATH, 40)
            small_font = ImageFont.truetype(WELCOME_FONT_PATH, 22)
        else:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
            name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except Exception:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    draw.text((card_x + 36, card_y + 36), title, font=title_font, fill="#ff69b4")
    draw.text((card_x + 36, card_y + 120), f"@{username}" if username else "Guest 😈", font=name_font, fill="#ffb6c1")
    txt = "💋 Tap the channels below to unlock your naughty videos 🔞🔥\nAahhh… get ready for pleasure 😏💦"
    draw.multiline_text((card_x + 36, card_y + 200), txt, font=small_font, fill="#ff99cc", spacing=6)

    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out

# ---------------------------
# NSFW Emoji progress bar
# ---------------------------
def create_emoji_progress(progress: int, total: int = 20) -> str:
    filled = int(progress / total * total)
    bar = "🍑" * filled + "🌚" * (total - filled)
    percent = int(progress / total * 100)
    return f"{bar} {percent}%"

# ---------------------------
# /start with NSFW progress
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    username = user.username or user.first_name or "Guest 😈"

    welcome_image = make_welcome_image(username=username)
    caption = f"{data.get('custom_message')}"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(welcome_image, filename="welcome.png"), caption=caption)

    # Loading progress animation
    progress_msg = await update.message.reply_text("💦 Aahhh… preparing your naughty content 🔥:\n" + create_emoji_progress(0))
    steps = 20
    for i in range(1, steps + 1):
        await asyncio.sleep(0.5)
        await progress_msg.edit_text("💦 Aahhh… preparing your naughty content 🔥:\n" + create_emoji_progress(i, steps))

    await progress_msg.edit_text("😈💦 Ready! Join channels & press ✅ I've Joined")

    # Channels keyboard
    keyboard = []
    for chat_id in CHANNEL_IDS:
        try:
            chat_obj = await context.bot.get_chat(chat_id)
            invite_link = getattr(chat_obj, "invite_link", None)
            if not invite_link:
                invite_link = await context.bot.export_chat_invite_link(chat_id)
            keyboard.append([InlineKeyboardButton(f"🔞 {chat_obj.title}", url=invite_link)])
        except Exception:
            keyboard.append([InlineKeyboardButton("🔞 Join Chat", url="https://t.me/")])

    keyboard.append([InlineKeyboardButton("✅ I've Joined", callback_data="check")])
    await update.message.reply_text("Join all channels then press ✅ I've Joined", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------------
# Verification & send NSFW videos
# ---------------------------
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    not_joined = []
    for chat_id in CHANNEL_IDS:
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ("member", "administrator", "creator"):
                chat_obj = await context.bot.get_chat(chat_id)
                not_joined.append(f"❌ {chat_obj.title}")
        except Forbidden:
            not_joined.append(f"⚠️ Cannot check {chat_id} (bot not admin)")
        except BadRequest:
            not_joined.append(f"⚠️ Invalid chat ID: {chat_id}")
        except Exception as e:
            not_joined.append(f"⚠️ Error in {chat_id}: {e}")

    if not_joined:
        await query.edit_message_text(
            "❌ **You haven’t joined all required chats:**\n\n" +
            "\n".join(not_joined) +
            "\n\nCome back and join all naughty rooms 😈💦",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("💦😈 **All joined! Sending your naughty content 🔞🔥**", parse_mode="Markdown")
        # Send stored NSFW videos
        data = load_data()
        videos = data.get("videos", [])
        if not videos:
            await context.bot.send_message(chat_id=query.message.chat_id, text="No adult videos stored yet 🔞💦")
            return
        await context.bot.send_message(chat_id=query.message.chat_id, text="💋 Sending your 18+ naughty content… 🔞🍑💦")
        for fid in videos:
            try:
                await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.UPLOAD_VIDEO)
                await context.bot.send_video(chat_id=query.message.chat_id, video=fid, caption="💦 Hot content just for you 😈🔥")
            except Exception as e:
                logger.exception("Failed to send video %s: %s", fid, e)
        await context.bot.send_message(chat_id=query.message.chat_id, text="😈💦 All naughty videos sent! Enjoy 🔥🍑")

# ---------------------------
# Admin commands
# ---------------------------
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if update.effective_user.id != data.get("admin_id"):
        return await update.message.reply_text("Only admin can use this command 🔞")
    if not context.args:
        return await update.message.reply_text("Usage: /add <custom message text>")
    data["custom_message"] = " ".join(context.args)
    save_data(data)
    await update.message.reply_text("Custom adult message updated 🔞💦")

async def store_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if update.effective_user.id != data.get("admin_id"):
        return await update.message.reply_text("Only admin can store media 🔞💦")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a video message with /store 🔞")
    msg = update.message.reply_to_message
    file_id = msg.video.file_id if msg.video else (msg.document.file_id if msg.document and "video" in (msg.document.mime_type or "") else None)
    if not file_id:
        return await update.message.reply_text("Replied message is not a video 🔞💦")
    if file_id not in data["videos"]:
        data["videos"].append(file_id)
        save_data(data)
    await update.message.reply_text("Adult video stored 🔞💦😈")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"Stored adult videos: {len(data.get('videos', []))} 🔞💦")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Admin: /add /store /status. User: /start 🔞😏")

# ---------------------------
# Main
# ---------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_membership, pattern="check"))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("store", store_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.run_polling()

if __name__ == "__main__":
    main()
