import asyncio
import logging
import random
import time
import psutil
import config
from ChatBot import _boot_
from ChatBot import get_readable_time
from ChatBot import ChatBot, mongo
from datetime import datetime
from pymongo import MongoClient
from pyrogram.enums import ChatType
from pyrogram import Client, filters
from config import OWNER_ID, MONGO_URL, OWNER_USERNAME
from pyrogram.errors import FloodWait, ChatAdminRequired
from ChatBot.database.chats import get_served_chats, add_served_chat
from ChatBot.database.users import get_served_users, add_served_user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from ChatBot.modules.helpers import (
    START,
    START_BOT,
    PNG_BTN,
    CLOSE_BTN,
    HELP_BTN,
    HELP_BUTN,
    HELP_READ,
    HELP_START,
    SOURCE_READ,
)

# Enhanced Messages with Emojis
GSTART = """**🌟 ʜᴇʏ {0}, ɪ'ᴍ {1} 🌟**\n\n**📌 ʏᴏᴜʀ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ᴄʜᴀᴛʙᴏᴛ**\n\n• /chatbot - ᴛᴏɢɢʟᴇ ᴄʜᴀᴛʙᴏᴛ\n• /lang - sᴇᴛ ʟᴀɴɢᴜᴀɢᴇ\n• /ping - ʙᴏᴛ sᴛᴀᴛᴜs\n• /broadcast - ʙʀᴏᴀᴅᴄᴀsᴛ ᴍsɢ\n• /id - ɢᴇᴛ ɪᴅs\n• /stats - ʙᴏᴛ sᴛᴀᴛs\n\n**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"""

STICKER = [
    "CAACAgUAAx0CYlaJawABBy4vZaieO6T-Ayg3mD-JP-f0yxJngIkAAv0JAALVS_FWQY7kbQSaI-geBA",
    "CAACAgUAAx0CYlaJawABBy4rZaid77Tf70SV_CfjmbMgdJyVD8sAApwLAALGXCFXmCx8ZC5nlfQeBA",
    "CAACAgUAAx0CYlaJawABBy4jZaidvIXNPYnpAjNnKgzaHmh3cvoAAiwIAAIda2lVNdNI2QABHuVVHgQ",
]

EMOJIOS = ["⚡","🔥","🪄","💫","✨","💥","🎯","🌟","🎩","🦋"]

BOT_PIC = "https://envs.sh/IL_.jpg"
IMG = [
    "https://graph.org/file/210751796ff48991b86a3.jpg",
    "https://graph.org/file/7b4924be4179f70abcf33.jpg",
    "https://graph.org/file/f6d8e64246bddc26b4f66.jpg",
    "https://graph.org/file/63d3ec1ca2c965d6ef210.jpg",
    "https://graph.org/file/9f12dc2a668d40875deb5.jpg",
]

# Database Collections
from ChatBot import db
chatai = db.Word.WordDb
lang_db = db.ChatLangDb.LangCollection
status_db = db.ChatBotStatusDb.StatusCollection

# System Stats
async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    UP = f"{get_readable_time((bot_uptime))}"
    CPU = f"{cpu}%"
    RAM = f"{mem}%"
    DISK = f"{disk}%"
    return UP, CPU, RAM, DISK

# Default Chat Status
async def set_default_status(chat_id):
    try:
        if not await status_db.find_one({"chat_id": chat_id}):
            await status_db.insert_one({"chat_id": chat_id, "status": "enabled"})
    except Exception as e:
        print(f"Error setting status: {e}")

# New Chat Handler
@ChatBot.on_message(filters.new_chat_members)
async def welcome_new_chat(client, message: Message):
    chat = message.chat
    await add_served_chat(chat.id)
    await set_default_status(chat.id)
    
    for member in message.new_chat_members:
        if member.id == ChatBot.id:
            try:
                # Welcome Message with Buttons
                buttons = [
                    [InlineKeyboardButton("🌍 sᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ", callback_data="choose_lang")],
                    [InlineKeyboardButton("🛠 ʜᴇʟᴘ", url=f"https://t.me/{ChatBot.username}?start=help")]
                ]
                await message.reply_text(
                    text="**🎉 ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ!**\n\n**📌 ᴜsᴇ /lang ᴛᴏ sᴇᴛ ʏᴏᴜʀ ᴄʜᴀᴛ ʟᴀɴɢᴜᴀɢᴇ**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                
                # Get Chat Info for Logs
                try:
                    invitelink = await client.export_chat_invite_link(chat.id)
                    link = f"📎 [ɢʀᴏᴜᴘ ʟɪɴᴋ]({invitelink})"
                except:
                    link = "🔒 ɴᴏ ʟɪɴᴋ"
                
                chat_photo = await client.download_media(chat.photo.big_file_id) if chat.photo else BOT_PIC
                
                # Prepare Log Message
                log_msg = (
                    f"**📌 ɴᴇᴡ ɢʀᴏᴜᴘ**\n\n"
                    f"**• ɴᴀᴍᴇ:** {chat.title}\n"
                    f"**• ɪᴅ:** `{chat.id}`\n"
                    f"**• ᴜsᴇʀɴᴀᴍᴇ:** @{chat.username if chat.username else 'ᴘʀɪᴠᴀᴛᴇ'}\n"
                    f"**• ʟɪɴᴋ:** {link}\n"
                    f"**• ᴍᴇᴍʙᴇʀs:** {await client.get_chat_members_count(chat.id)}\n"
                    f"**• ᴀᴅᴅᴇᴅ ʙʏ:** {message.from_user.mention}\n\n"
                    f"**🔥 ᴛᴏᴛᴀʟ ᴄʜᴀᴛs:** {len(await get_served_chats())}"
                )
                
                # Send to Owner
                await client.send_photo(
                    OWNER_ID,
                    photo=chat_photo,
                    caption=log_msg,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        f"{message.from_user.first_name}",
                        user_id=message.from_user.id
                    )]])
                )
                
            except Exception as e:
                print(f"Welcome error: {e}")

# Start Command
@ChatBot.on_cmd(["start", "aistart"])
async def start_command(client, message: Message):
    users = len(await get_served_users())
    chats = len(await get_served_chats())
    
    if message.chat.type == ChatType.PRIVATE:
        # Cool Loading Animation
        loading = await message.reply_text(random.choice(EMOJIOS))
        steps = [
            "🍓",
            "💙",
            "🖤",
            "💛",
            "🤍",
            "❤️"
        ]
        for step in steps:
            await loading.edit(step)
            await asyncio.sleep(0.3)
        await loading.delete()
        
        # Send Sticker
        await message.reply_sticker(random.choice(STICKER))
        
        # Get User Photo or Default
        chat_photo = BOT_PIC
        if message.chat.photo:
            try:
                user_photo = await client.download_media(message.chat.photo.big_file_id)
                chat_photo = user_photo if user_photo else BOT_PIC
            except:
                chat_photo = BOT_PIC
        
        # System Stats
        UP, CPU, RAM, DISK = await bot_sys_stats()
        
        # Enhanced Start Message
        await message.reply_photo(
            photo=chat_photo,
            caption=START.format(ChatBot.mention, users, chats, UP),
            reply_markup=InlineKeyboardMarkup(START_BOT)
        )
        await add_served_user(message.chat.id)
        
        # Notify Owner
        owner_msg = (
            f"**🚀 ɴᴇᴡ ᴜsᴇʀ**\n\n"
            f"**• ɴᴀᴍᴇ:** {message.chat.first_name}\n"
            f"**• ᴜsᴇʀɴᴀᴍᴇ:** @{message.chat.username}\n"
            f"**• ɪᴅ:** {message.chat.id}\n\n"
            f"**🔥 ᴛᴏᴛᴀʟ ᴜsᴇʀs:** {users}"
        )
        await client.send_photo(
            OWNER_ID,
            photo=chat_photo,
            caption=owner_msg,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                f"{message.chat.first_name}",
                user_id=message.chat.id
            )]])
        )
    else:
        # Group Start Message
        await message.reply_photo(
            photo=random.choice(IMG),
            caption=GSTART.format(message.from_user.mention, ChatBot.name),
            reply_markup=InlineKeyboardMarkup(HELP_START),
        )
        await add_served_chat(message.chat.id)

# Help Command
@ChatBot.on_cmd("help")
async def help_command(client, message: Message):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_photo(
            photo=random.choice(IMG),
            caption=HELP_READ,
            reply_markup=InlineKeyboardMarkup(HELP_BTN),
        )
    else:
        await message.reply_photo(
            photo=random.choice(IMG),
            caption="**💡 ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ғᴏʀ ʜᴇʟᴘ**",
            reply_markup=InlineKeyboardMarkup(HELP_BUTN),
        )
        await add_served_chat(message.chat.id)

# Repo Command
@ChatBot.on_cmd("repo")
async def repo_command(_, message: Message):
    await message.reply_text(
        text=SOURCE_READ,
        reply_markup=InlineKeyboardMarkup(CLOSE_BTN),
        disable_web_page_preview=True,
    )

# Ping Command
@ChatBot.on_cmd("ping")
async def ping_command(_, message: Message):
    start = datetime.now()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    
    ping_msg = await message.reply_photo(
        photo=random.choice(IMG),
        caption="**📡 ᴘɪɴɢɪɴɢ...**",
    )

    ms = (datetime.now() - start).microseconds / 1000
    await ping_msg.edit_text(
        text=(
            f"**⚡ {ChatBot.name} sᴛᴀᴛs ⚡**\n\n"
            f"**• ᴘɪɴɢ:** `{ms}` ms\n"
            f"**• ᴄᴘᴜ:** {CPU}\n"
            f"**• ʀᴀᴍ:** {RAM}\n"
            f"**• ᴅɪsᴋ:** {DISK}\n"
            f"**• ᴜᴘᴛɪᴍᴇ:** {UP}\n\n"
            f"**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"
        ),
        reply_markup=InlineKeyboardMarkup(PNG_BTN),
    )
    
    if message.chat.type == ChatType.PRIVATE:
        await add_served_user(message.from_user.id)
    else:
        await add_served_chat(message.chat.id)

# Stats Command
@ChatBot.on_message(filters.command("stats"))
async def stats_command(client, message: Message):
    users = len(await get_served_users())
    chats = len(await get_served_chats())
    await message.reply_text(
        f"""**📊 {ChatBot.name} sᴛᴀᴛs**\n\n**• ᴄʜᴀᴛs:** {chats}\n**• ᴜsᴇʀs:** {users}"""
    )

# ID Command
@ChatBot.on_cmd("id")
async def get_id(client, message: Message):
    chat = message.chat
    user_id = message.from_user.id
    msg_id = message.id
    reply = message.reply_to_message

    text = f"**📌 ɪᴅ ɪɴғᴏ**\n\n"
    text += f"**• ᴍᴇssᴀɢᴇ ɪᴅ:** `{msg_id}`\n"
    text += f"**• ʏᴏᴜʀ ɪᴅ:** `{user_id}`\n"

    if len(message.command) == 2:
        try:
            user = message.text.split(None, 1)[1].strip()
            user_info = await client.get_users(user)
            text += f"**• ᴜsᴇʀ ɪᴅ:** `{user_info.id}`\n"
        except:
            text += "**⚠️ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ**\n"

    text += f"**• ᴄʜᴀᴛ ɪᴅ:** `{chat.id}`\n\n"

    if reply:
        text += f"**• ʀᴇᴘʟɪᴇᴅ ᴍsɢ ɪᴅ:** `{reply.id}`\n"
        if reply.from_user:
            text += f"**• ʀᴇᴘʟɪᴇᴅ ᴜsᴇʀ ɪᴅ:** `{reply.from_user.id}`\n"
        if reply.forward_from_chat:
            text += f"**• ғᴏʀᴡᴀʀᴅᴇᴅ ᴄʜᴀᴛ ɪᴅ:** `{reply.forward_from_chat.id}`\n"
        if reply.sender_chat:
            text += f"**• sᴇɴᴅᴇʀ ᴄʜᴀᴛ ɪᴅ:** `{reply.sender_chat.id}`"

    await message.reply_text(text, disable_web_page_preview=True)

# Broadcast Command (Optimized)
@ChatBot.on_message(filters.command(["broadcast", "gcast"]) & filters.user(OWNER_ID))
async def broadcast_command(client, message: Message):
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply("**⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴏʀ ᴘʀᴏᴠɪᴅᴇ ᴛᴇxᴛ**")

    query = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    flags = {
        "-pin": "-pin" in query,
        "-pinloud": "-pinloud" in query,
        "-nogroup": "-nogroup" in query,
        "-user": "-user" in query,
    }

    content = message.reply_to_message if message.reply_to_message else query.replace("-pin", "").replace("-pinloud", "").replace("-nogroup", "").replace("-user", "").strip()

    if not content:
        return await message.reply("**⚠️ ɴᴏ ᴄᴏɴᴛᴇɴᴛ ғᴏᴜɴᴅ**")

    processing = await message.reply("**📢 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...**")

    # Broadcast to Groups
    if not flags.get("-nogroup"):
        sent_groups = 0
        pinned_groups = 0
        groups = await get_served_chats()
        
        for group in groups:
            try:
                if message.reply_to_message:
                    msg = await client.forward_messages(
                        group["chat_id"],
                        message.chat.id,
                        message.reply_to_message.id
                    )
                else:
                    msg = await client.send_message(
                        group["chat_id"],
                        content
                    )
                sent_groups += 1

                if flags.get("-pin") or flags.get("-pinloud"):
                    try:
                        await msg.pin(disable_notification=flags.get("-pin"))
                        pinned_groups += 1
                    except:
                        continue
                
                await asyncio.sleep(0.2)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                continue

        await processing.edit(f"**✅ sᴇɴᴛ ᴛᴏ {sent_groups} ɢʀᴏᴜᴘs | 📌 ᴘɪɴɴᴇᴅ ɪɴ {pinned_groups}**")

    # Broadcast to Users
    if flags.get("-user"):
        sent_users = 0
        users = await get_served_users()
        
        for user in users:
            try:
                if message.reply_to_message:
                    await client.forward_messages(
                        user["user_id"],
                        message.chat.id,
                        message.reply_to_message.id
                    )
                else:
                    await client.send_message(
                        user["user_id"],
                        content
                    )
                sent_users += 1
                await asyncio.sleep(0.2)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                continue

        await message.reply(f"**✅ sᴇɴᴛ ᴛᴏ {sent_users} ᴜsᴇʀs**")

# File Manager Commands
@ChatBot.on_cmd(["ls"])
async def list_files(_, m: Message):
    "To list all files and folders."
    path = "".join(m.text.split(maxsplit=1)[1:]) if len(m.command) > 1 else os.getcwd()
    
    if not os.path.exists(path):
        return await m.reply_text(f"**⚠️ ᴘᴀᴛʜ ɴᴏᴛ ғᴏᴜɴᴅ:** `{path}`")

    if os.path.isdir(path):
        msg = f"**📂 ᴄᴏɴᴛᴇɴᴛs ᴏғ `{path}`:**\n\n"
        files = []
        folders = []
        
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append(f"📁 `{item}`")
            else:
                ext = os.path.splitext(item)[1].lower()
                if ext in (".mp3", ".flac", ".wav", ".m4a"):
                    files.append(f"🎵 `{item}`")
                elif ext == ".opus":
                    files.append(f"🎙 `{item}`")
                elif ext in (".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv"):
                    files.append(f"🎞 `{item}`")
                elif ext in (".zip", ".tar", ".tar.gz", ".rar"):
                    files.append(f"🗜 `{item}`")
                elif ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico"):
                    files.append(f"🖼 `{item}`")
                else:
                    files.append(f"📄 `{item}`")
        
        msg += "\n".join(folders + files) if folders or files else "**📂 ᴇᴍᴘᴛʏ ᴅɪʀᴇᴄᴛᴏʀʏ**"
    else:
        size = os.stat(path).st_size
        ext = os.path.splitext(path)[1].lower()
        
        if ext in (".mp3", ".flac", ".wav", ".m4a"):
            icon = "🎵"
        elif ext == ".opus":
            icon = "🎙"
        elif ext in (".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv"):
            icon = "🎞"
        elif ext in (".zip", ".tar", ".tar.gz", ".rar"):
            icon = "🗜"
        elif ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico"):
            icon = "🖼"
        else:
            icon = "📄"
        
        msg = (
            f"**📌 ғɪʟᴇ ɪɴғᴏ**\n\n"
            f"**• ɴᴀᴍᴇ:** `{os.path.basename(path)}`\n"
            f"**• ᴛʏᴘᴇ:** {icon}\n"
            f"**• sɪᴢᴇ:** `{humanbytes(size)}`\n"
            f"**• ᴘᴀᴛʜ:** `{path}`\n"
            f"**• ʟᴀsᴛ ᴍᴏᴅɪғɪᴇᴅ:** `{time.ctime(os.path.getmtime(path))}`\n"
            f"**• ʟᴀsᴛ ᴀᴄᴄᴇssᴇᴅ:** `{time.ctime(os.path.getatime(path))}`"
        )

    if len(msg) > 4096:
        with io.BytesIO(str.encode(msg)) as file:
            file.name = "file_list.txt"
            await m.reply_document(file, caption=path)
    else:
        await m.reply_text(msg)

# Utility Function
def humanbytes(size: int) -> str:
    if not size:
        return ""
    power = 2**10
    n = 0
    units = {0: "", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
