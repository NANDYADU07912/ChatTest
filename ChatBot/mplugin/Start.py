import asyncio
import logging
import random
import time
import psutil
import config
import os
import io
from ChatBot import _boot_
from ChatBot import get_readable_time
from ChatBot.mplugin.helpers import is_owner
from ChatBot import mongo
from datetime import datetime
from pymongo import MongoClient
from pyrogram.enums import ChatType
from pyrogram import Client, filters
from ChatBot import CLONE_OWNERS, db
from config import OWNER_ID, MONGO_URL, OWNER_USERNAME
from pyrogram.errors import FloodWait, ChatAdminRequired
from ChatBot.database.chats import get_served_chats, add_served_chat
from ChatBot.database.users import get_served_users, add_served_user
from ChatBot.database.clonestats import get_served_cchats, get_served_cusers, add_served_cuser, add_served_cchat
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from ChatBot.mplugin.helpers import (
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

# Enhanced Messages with Emojis and Formatting
GSTART = """**✨ ʜᴇʏ {0}, ɪ'ᴍ {1} ✨**\n\n**📌 ʏᴏᴜʀ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ᴄʜᴀᴛʙᴏᴛ**\n\n**• /chatbot** - ᴛᴏɢɢʟᴇ ᴄʜᴀᴛʙᴏᴛ\n**• /lang** - sᴇᴛ ʟᴀɴɢᴜᴀɢᴇ\n**• /ping** - ʙᴏᴛ sᴛᴀᴛᴜs\n**• /broadcast** - ʙʀᴏᴀᴅᴄᴀsᴛ ᴍsɢ\n**• /id** - ɢᴇᴛ ɪᴅs\n**• /stats** - ʙᴏᴛ sᴛᴀᴛs\n\n**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"""

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
cloneownerdb = db.clone_owners
bot_settings_db = db.bot_settings

# Default support links
DEFAULT_SUPPORT_CHANNEL = "https://t.me/ShrutiBots"
DEFAULT_SUPPORT_GROUP = "https://t.me/ShrutiBotsSupport"

async def get_clone_owner(bot_id):
    data = await cloneownerdb.find_one({"bot_id": bot_id})
    if data:
        return data["user_id"]
    return None

async def get_bot_settings(bot_id):
    """Get bot settings from database"""
    settings = await bot_settings_db.find_one({"bot_id": bot_id})
    if not settings:
        settings = {
            "bot_id": bot_id,
            "support_channel": DEFAULT_SUPPORT_CHANNEL,
            "support_group": DEFAULT_SUPPORT_GROUP,
            "custom_start_msg": None
        }
        await bot_settings_db.insert_one(settings)
    return settings

async def update_bot_settings(bot_id, key, value):
    """Update bot settings in database"""
    await bot_settings_db.update_one(
        {"bot_id": bot_id},
        {"$set": {key: value}},
        upsert=True
    )

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

async def set_default_status(chat_id):
    try:
        if not await status_db.find_one({"chat_id": chat_id}):
            await status_db.insert_one({"chat_id": chat_id, "status": "enabled"})
    except Exception as e:
        print(f"Error setting status: {e}")

@Client.on_message(filters.new_chat_members)
async def welcome_new_chat(client, message: Message):
    chat = message.chat
    bot_id = client.me.id
    await add_served_cchat(bot_id, chat.id)
    await add_served_chat(chat.id)
    await set_default_status(chat.id)
    
    # Get bot settings for support links
    settings = await get_bot_settings(bot_id)
    
    for member in message.new_chat_members:
        if member.id == client.me.id:
            try:
                # Welcome Message with Buttons including support links
                buttons = [
                    [InlineKeyboardButton("🌍 sᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ", callback_data="choose_lang")],
                    [InlineKeyboardButton("🛠 ʜᴇʟᴘ", url=f"https://t.me/{client.username}?start=help")],
                    [
                        InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                        InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
                    ]
                ]
                await message.reply_text(
                    text="**🎉 ᴛʜᴀɴᴋs ғᴏʀ ᴀᴅᴅɪɴɢ ᴍᴇ!**\n\n**📌 ɪ'ᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ᴄʜᴀᴛʙᴏᴛ**\n\n**🌟 ᴜsᴇ /lang ᴛᴏ sᴇᴛ ʏᴏᴜʀ ᴄʜᴀᴛ ʟᴀɴɢᴜᴀɢᴇ**\n**💬 sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ ᴡɪᴛʜ ᴍᴇ!**",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                
                # Get Chat Info for Logs
                try:
                    invitelink = await client.export_chat_invite_link(chat.id)
                    link = f"📎 [ɢʀᴏᴜᴘ ʟɪɴᴋ]({invitelink})"
                except:
                    link = "🔒 ɴᴏ ʟɪɴᴋ"
                
                chat_photo = await client.download_media(chat.photo.big_file_id) if chat.photo else BOT_PIC
                
                # Enhanced Log Message
                log_msg = (
                    f"**📌 ɴᴇᴡ ɢʀᴏᴜᴘ**\n\n"
                    f"**• ɴᴀᴍᴇ:** {chat.title}\n"
                    f"**• ɪᴅ:** `{chat.id}`\n"
                    f"**• ᴜsᴇʀɴᴀᴍᴇ:** @{chat.username if chat.username else 'ᴘʀɪᴠᴀᴛᴇ'}\n"
                    f"**• ʟɪɴᴋ:** {link}\n"
                    f"**• ᴍᴇᴍʙᴇʀs:** {await client.get_chat_members_count(chat.id)}\n"
                    f"**• ᴀᴅᴅᴇᴅ ʙʏ:** {message.from_user.mention}\n\n"
                    f"**🔥 ᴛᴏᴛᴀʟ ᴄʜᴀᴛs:** {len(await get_served_cchats(bot_id))}"
                )
                
                # Send to Owner
                owner_id = await get_clone_owner(bot_id)
                if owner_id:
                    await client.send_photo(
                        owner_id,
                        photo=chat_photo,
                        caption=log_msg,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                            f"{message.from_user.first_name}",
                            user_id=message.from_user.id
                        )]])
                    )
                
            except Exception as e:
                print(f"Welcome error: {e}")

@Client.on_message(filters.command(["setsupportchannel"]))
async def set_support_channel(client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    # Check if user owns this bot
    if not await is_owner(bot_id, user_id):
        return await message.reply("❌ **You don't have permission to modify this bot!**")
    
    if len(message.command) < 2:
        return await message.reply(
            "⚠️ **Please provide the support channel URL**\n\n"
            "**Usage:** `/setsupportchannel https://t.me/YourChannel`\n\n"
            "**Example:** `/setsupportchannel https://t.me/ShrutiBots`"
        )
    
    channel_url = message.text.split(None, 1)[1]
    
    # Basic URL validation
    if not (channel_url.startswith("https://t.me/") or channel_url.startswith("http://t.me/")):
        return await message.reply("❌ **Please provide a valid Telegram channel URL!**\n\n**Example:** `https://t.me/YourChannel`")
    
    try:
        await update_bot_settings(bot_id, "support_channel", channel_url)
        await message.reply(
            f"✅ **Support channel updated successfully!**\n\n"
            f"**📢 New Channel:** {channel_url}\n\n"
            f"**📌 Note:** This will now appear in your bot's start message buttons!"
        )
    except Exception as e:
        await message.reply(f"❌ **Error updating support channel:** `{str(e)[:200]}`")

@Client.on_message(filters.command(["setsupportgroup"]))
async def set_support_group(client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    # Check if user owns this bot
    if not await is_owner(bot_id, user_id):
        return await message.reply("❌ **You don't have permission to modify this bot!**")
    
    if len(message.command) < 2:
        return await message.reply(
            "⚠️ **Please provide the support group URL**\n\n"
            "**Usage:** `/setsupportgroup https://t.me/YourGroup`\n\n"
            "**Example:** `/setsupportgroup https://t.me/ShrutiBotsSupport`"
        )
    
    group_url = message.text.split(None, 1)[1]
    
    # Basic URL validation
    if not (group_url.startswith("https://t.me/") or group_url.startswith("http://t.me/")):
        return await message.reply("❌ **Please provide a valid Telegram group URL!**\n\n**Example:** `https://t.me/YourGroup`")
    
    try:
        await update_bot_settings(bot_id, "support_group", group_url)
        await message.reply(
            f"✅ **Support group updated successfully!**\n\n"
            f"**👥 New Group:** {group_url}\n\n"
            f"**📌 Note:** This will now appear in your bot's start message buttons!"
        )
    except Exception as e:
        await message.reply(f"❌ **Error updating support group:** `{str(e)[:200]}`")

@Client.on_message(filters.command(["start", "aistart"]))
async def start_command(client, message: Message):
    bot_id = client.me.id
    users = len(await get_served_cusers(bot_id))
    chats = len(await get_served_cchats(bot_id))
    
    # Get bot settings for support links
    settings = await get_bot_settings(bot_id)
    
    if message.chat.type == ChatType.PRIVATE:
        # Cool Loading Animation
        loading = await message.reply_text(random.choice(EMOJIOS))
        steps = [
            "🤍",
            "💛",
            "💙",
            "🖤",
        ]
        for step in steps:
            await loading.edit(step)
            await asyncio.sleep(0.2)  # Faster animation
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
        
        # Enhanced Start Message with support buttons
        start_buttons = [
            [
                InlineKeyboardButton("🔥 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", url=f"https://t.me/{client.username}?startgroup=true"),
            ],
            [
                InlineKeyboardButton("🛠 ʜᴇʟᴘ", callback_data="help_menu"),
                InlineKeyboardButton("🎛 ᴄᴏᴍᴍᴀɴᴅs", callback_data="commands_menu")
            ],
            [
                InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
            ],
            [
                InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")
            ]
        ]
        
        enhanced_start_msg = (
            f"**✨ ʜᴇʟʟᴏ {message.from_user.mention}!**\n\n"
            f"**🤖 ɪ'ᴍ {client.me.first_name} - ʏᴏᴜʀ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ᴄʜᴀᴛʙᴏᴛ!**\n\n"
            f"**📊 ʙᴏᴛ sᴛᴀᴛs:**\n"
            f"**├ 👥 ᴜsᴇʀs:** `{users}`\n"
            f"**├ 💬 ᴄʜᴀᴛs:** `{chats}`\n"
            f"**├ ⏰ ᴜᴘᴛɪᴍᴇ:** `{UP}`\n"
            f"**└ 🖥 ᴄᴘᴜ:** `{CPU}`\n\n"
            f"**🌟 ғᴇᴀᴛᴜʀᴇs:**\n"
            f"**• 💬 sᴍᴀʀᴛ ᴄʜᴀᴛʙᴏᴛ**\n"
            f"**• 🌍 ᴍᴜʟᴛɪ-ʟᴀɴɢᴜᴀɢᴇ sᴜᴘᴘᴏʀᴛ**\n"
            f"**• ⚡ ғᴀsᴛ ʀᴇsᴘᴏɴsᴇs**\n"
            f"**• 🛠 ᴄᴜsᴛᴏᴍɪᴢᴀʙʟᴇ**\n\n"
            f"**🔥 ʀᴇᴀᴅʏ ᴛᴏ ᴄʜᴀᴛ? ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀ ᴍᴇssᴀɢᴇ!**"
        )
        
        await message.reply_photo(
            photo=chat_photo,
            caption=enhanced_start_msg,
            reply_markup=InlineKeyboardMarkup(start_buttons)
        )
        await add_served_cuser(bot_id, message.chat.id)
        await add_served_user(message.chat.id)
        
        # Notify Owner with enhanced message
        owner_msg = (
            f"**🚀 ɴᴇᴡ ᴜsᴇʀ sᴛᴀʀᴛᴇᴅ ʙᴏᴛ**\n\n"
            f"**• ɴᴀᴍᴇ:** {message.chat.first_name}\n"
            f"**• ᴜsᴇʀɴᴀᴍᴇ:** @{message.chat.username or 'ɴ/ᴀ'}\n"
            f"**• ɪᴅ:** `{message.chat.id}`\n"
            f"**• ʟᴀɴɢ:** {message.chat.language_code or 'ᴜɴᴋɴᴏᴡɴ'}\n\n"
            f"**📊 ᴛᴏᴛᴀʟ ᴜsᴇʀs:** `{users + 1}`"
        )
        owner_id = await get_clone_owner(bot_id)
        if owner_id:
            await client.send_photo(
                owner_id,
                photo=chat_photo,
                caption=owner_msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                    f"{message.chat.first_name}",
                    user_id=message.chat.id
                )]])
            )
    else:
        # Group Start Message with support buttons
        group_buttons = [
            [
                InlineKeyboardButton("🛠 ʜᴇʟᴘ", url=f"https://t.me/{client.username}?start=help"),
                InlineKeyboardButton("🎛 ᴄᴏᴍᴍᴀɴᴅs", url=f"https://t.me/{client.username}?start=commands")
            ],
            [
                InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
            ]
        ]
        
        enhanced_group_start = (
            f"**✨ ʜᴇʏ {message.from_user.mention}, ɪ'ᴍ {client.me.first_name}! ✨**\n\n"
            f"**🤖 ʏᴏᴜʀ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ᴄʜᴀᴛʙᴏᴛ ᴡɪᴛʜ sᴍᴀʀᴛ ᴄᴏɴᴠᴇʀsᴀᴛɪᴏɴs!**\n\n"
            f"**🌟 ᴋᴇʏ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            f"**• /chatbot** - ᴛᴏɢɢʟᴇ ᴄʜᴀᴛʙᴏᴛ ᴏɴ/ᴏғғ\n"
            f"**• /lang** - sᴇᴛ ʏᴏᴜʀ ʟᴀɴɢᴜᴀɢᴇ\n"
            f"**• /ping** - ᴄʜᴇᴄᴋ ʙᴏᴛ sᴛᴀᴛᴜs\n"
            f"**• /stats** - ᴠɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
            f"**• /id** - ɢᴇᴛ ᴄʜᴀᴛ/ᴜsᴇʀ ɪᴅs\n\n"
            f"**💬 ᴊᴜsᴛ sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ!**"
        )
        
        await message.reply_photo(
            photo=random.choice(IMG),
            caption=help_text,
            reply_markup=InlineKeyboardMarkup(help_buttons),
        )
    else:
        group_help_buttons = [
            [
                InlineKeyboardButton("🛠 ʜᴇʟᴘ", url=f"https://t.me/{client.username}?start=help"),
                InlineKeyboardButton("🎛 ᴄᴏᴍᴍᴀɴᴅs", url=f"https://t.me/{client.username}?start=commands")
            ],
            [
                InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
            ]
        ]
        
        await message.reply_photo(
            photo=random.choice(IMG),
            caption="**💡 ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ғᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ʜᴇʟᴘ**\n\n**🤖 ᴏʀ ᴊᴜsᴛ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ ᴡɪᴛʜ ᴍᴇ!**",
            reply_markup=InlineKeyboardMarkup(group_help_buttons),
        )
        await add_served_cchat(bot_id, message.chat.id)
        await add_served_chat(message.chat.id)

@Client.on_message(filters.command("repo"))
async def repo_command(client, message: Message):
    settings = await get_bot_settings(client.me.id)
    
    repo_buttons = [
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ],
        [InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")]
    ]
    
    await message.reply_text(
        text=SOURCE_READ,
        reply_markup=InlineKeyboardMarkup(repo_buttons),
        disable_web_page_preview=True,
    )

@Client.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    bot_id = client.me.id
    start = datetime.now()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    settings = await get_bot_settings(bot_id)
    
    ping_msg = await message.reply_photo(
        photo=random.choice(IMG),
        caption="**📡 ᴘɪɴɢɪɴɢ...**",
    )

    ms = (datetime.now() - start).microseconds / 1000
    
    ping_buttons = [
        [
            InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ", callback_data="refresh_ping"),
            InlineKeyboardButton("📊 ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛs", callback_data="detailed_stats")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ]
    ]
    
    await ping_msg.edit_text(
        text=(
            f"**⚡ {client.me.first_name} sᴛᴀᴛs ⚡**\n\n"
            f"**📊 sʏsᴛᴇᴍ ᴘᴇʀғᴏʀᴍᴀɴᴄᴇ:**\n"
            f"**├ 📡 ᴘɪɴɢ:** `{ms:.2f}` ms\n"
            f"**├ 🖥 ᴄᴘᴜ:** `{CPU}`\n"
            f"**├ 💾 ʀᴀᴍ:** `{RAM}`\n"
            f"**├ 💿 ᴅɪsᴋ:** `{DISK}`\n"
            f"**└ ⏰ ᴜᴘᴛɪᴍᴇ:** `{UP}`\n\n"
            f"**🚀 sᴛᴀᴛᴜs:** {'🟢 ᴏɴʟɪɴᴇ' if ms < 100 else '🟡 sʟᴏᴡ' if ms < 200 else '🔴 ʟᴀɢɢɪɴɢ'}\n\n"
            f"**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"
        ),
        reply_markup=InlineKeyboardMarkup(ping_buttons)
    )

@Client.on_callback_query(filters.regex("refresh_stats"))
async def refresh_stats_callback(client, callback_query: CallbackQuery):
    bot_id = client.me.id
    users = len(await get_served_cusers(bot_id))
    chats = len(await get_served_cchats(bot_id))
    settings = await get_bot_settings(bot_id)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    
    stats_buttons = [
        [
            InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ", callback_data="refresh_stats"),
            InlineKeyboardButton("📈 ɢʀᴏᴡᴛʜ", callback_data="growth_stats")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ]
    ]
    
    stats_text = (
        f"**📊 {client.me.first_name} sᴛᴀᴛɪsᴛɪᴄs**\n\n"
        f"**👥 ᴜsᴇʀ sᴛᴀᴛs:**\n"
        f"**├ 👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs:** `{users:,}`\n"
        f"**└ 💬 ᴛᴏᴛᴀʟ ᴄʜᴀᴛs:** `{chats:,}`\n\n"
        f"**⚡ sʏsᴛᴇᴍ sᴛᴀᴛs:**\n"
        f"**├ ⏰ ᴜᴘᴛɪᴍᴇ:** `{UP}`\n"
        f"**├ 🖥 ᴄᴘᴜ:** `{CPU}`\n"
        f"**├ 💾 ʀᴀᴍ:** `{RAM}`\n"
        f"**└ 💿 ᴅɪsᴋ:** `{DISK}`\n\n"
        f"**🌟 ᴛᴏᴛᴀʟ ɪɴᴛᴇʀᴀᴄᴛɪᴏɴs:** `{users + chats:,}`\n\n"
        f"**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"
    )
    
    await callback_query.edit_message_text(
        text=stats_text,
        reply_markup=InlineKeyboardMarkup(stats_buttons)
    )

# Additional Callback Handlers for enhanced functionality
@Client.on_callback_query(filters.regex("help_menu"))
async def help_menu_callback(client, callback_query: CallbackQuery):
    settings = await get_bot_settings(client.me.id)
    
    help_buttons = [
        [
            InlineKeyboardButton("🤖 ᴄʜᴀᴛʙᴏᴛ", callback_data="help_chatbot"),
            InlineKeyboardButton("🌍 ʟᴀɴɢᴜᴀɢᴇ", callback_data="help_language")
        ],
        [
            InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="help_stats"),
            InlineKeyboardButton("🛠 ᴀᴅᴍɪɴ", callback_data="help_admin")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ],
        [InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")]
    ]
    
    help_text = (
        f"**🛠 ʜᴇʟᴘ ᴍᴇɴᴜ - {client.me.first_name}**\n\n"
        f"**🤖 ᴄʜᴀᴛʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/chatbot` - ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ\n"
        f"• `/status` - ᴄʜᴇᴄᴋ ᴄʜᴀᴛʙᴏᴛ sᴛᴀᴛᴜs\n\n"
        f"**🌍 ʟᴀɴɢᴜᴀɢᴇ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/lang` - sᴇᴛ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ\n"
        f"• `/chatlang` - ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ʟᴀɴɢᴜᴀɢᴇ\n"
        f"• `/resetlang` - ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ\n\n"
        f"**📊 ɪɴғᴏ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/ping` - ᴄʜᴇᴄᴋ ʙᴏᴛ sᴛᴀᴛᴜs\n"
        f"• `/stats` - ᴠɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
        f"• `/id` - ɢᴇᴛ ᴄʜᴀᴛ/ᴜsᴇʀ ɪᴅs\n\n"
        f"**💬 ᴊᴜsᴛ sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ!**"
    )
    
    await callback_query.edit_message_text(
        text=help_text,
        reply_markup=InlineKeyboardMarkup(help_buttons)
    )

@Client.on_callback_query(filters.regex("commands_menu"))
async def commands_menu_callback(client, callback_query: CallbackQuery):
    settings = await get_bot_settings(client.me.id)
    
    commands_buttons = [
        [
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="help_menu"),
            InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ]
    ]
    
    commands_text = (
        f"**🎛 ᴄᴏᴍᴍᴀɴᴅ ʟɪsᴛ - {client.me.first_name}**\n\n"
        f"**🔰 ʙᴀsɪᴄ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/start` - sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n"
        f"• `/help` - sʜᴏᴡ ʜᴇʟᴘ ᴍᴇɴᴜ\n"
        f"• `/ping` - ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ\n"
        f"• `/stats` - ᴠɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
        f"• `/id` - ɢᴇᴛ ᴄʜᴀᴛ/ᴜsᴇʀ ɪᴅs\n\n"
        f"**🤖 ᴄʜᴀᴛʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/chatbot` - ᴛᴏɢɢʟᴇ ᴄʜᴀᴛʙᴏᴛ\n"
        f"• `/status` - ᴄʜᴇᴄᴋ ᴄʜᴀᴛʙᴏᴛ sᴛᴀᴛᴜs\n"
        f"• `/ask <ǫᴜᴇsᴛɪᴏɴ>` - ᴀsᴋ ᴀɪ\n\n"
        f"**🌍 ʟᴀɴɢᴜᴀɢᴇ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/lang` - sᴇᴛ ʟᴀɴɢᴜᴀɢᴇ\n"
        f"• `/chatlang` - ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ʟᴀɴɢ\n"
        f"• `/resetlang` - ʀᴇsᴇᴛ ʟᴀɴɢᴜᴀɢᴇ\n\n"
        f"**🛠 ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs:**\n"
        f"• `/broadcast` - ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ\n"
        f"• `/setsupportchannel` - sᴇᴛ sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ\n"
        f"• `/setsupportgroup` - sᴇᴛ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ\n\n"
        f"**💬 ᴊᴜsᴛ ᴛʏᴘᴇ ᴀɴʏᴛʜɪɴɢ ᴛᴏ ᴄʜᴀᴛ ᴡɪᴛʜ ᴍᴇ!**"
    )
    
    await callback_query.edit_message_text(
        text=commands_text,
        reply_markup=InlineKeyboardMarkup(commands_buttons)
    )

# Utility Function
def humanbytes(size: int) -> str:
    """Convert bytes to human readable format"""
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    units = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"

# Enhanced error handling
async def handle_error(client, message, error):
    """Enhanced error handler"""
    error_msg = (
        f"**❌ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ**\n\n"
        f"**• ᴇʀʀᴏʀ:** `{str(error)[:200]}`\n"
        f"**• ᴄʜᴀᴛ:** `{message.chat.id}`\n"
        f"**• ᴜsᴇʀ:** `{message.from_user.id}`\n\n"
        f"**🔧 ɪғ ᴛʜɪs ᴘᴇʀsɪsᴛs, ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ**"
    )
    
    try:
        settings = await get_bot_settings(client.me.id)
        error_buttons = [
            [
                InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
            ]
        ]
        await message.reply(error_msg, reply_markup=InlineKeyboardMarkup(error_buttons))
    except:
        await message.reply(error_msg[:1000])

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Success message
logger.info("🎉 Start.py loaded successfully with enhanced features! ʙʏ: @ShrutiBots**")
    
    if message.chat.type == ChatType.PRIVATE:
        await add_served_cuser(bot_id, message.from_user.id)
        await add_served_user(message.from_user.id)
    else:
        await add_served_cchat(bot_id, message.chat.id)
        await add_served_chat(message.chat.id)

@Client.on_message(filters.command("stats"))
async def stats_command(client, message: Message):
    bot_id = client.me.id
    users = len(await get_served_cusers(bot_id))
    chats = len(await get_served_cchats(bot_id))
    settings = await get_bot_settings(bot_id)
    UP, CPU, RAM, DISK = await bot_sys_stats()
    
    stats_buttons = [
        [
            InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ", callback_data="refresh_stats"),
            InlineKeyboardButton("📈 ɢʀᴏᴡᴛʜ", callback_data="growth_stats")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ]
    ]
    
    stats_text = (
        f"**📊 {client.me.first_name} sᴛᴀᴛɪsᴛɪᴄs**\n\n"
        f"**👥 ᴜsᴇʀ sᴛᴀᴛs:**\n"
        f"**├ 👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs:** `{users:,}`\n"
        f"**└ 💬 ᴛᴏᴛᴀʟ ᴄʜᴀᴛs:** `{chats:,}`\n\n"
        f"**⚡ sʏsᴛᴇᴍ sᴛᴀᴛs:**\n"
        f"**├ ⏰ ᴜᴘᴛɪᴍᴇ:** `{UP}`\n"
        f"**├ 🖥 ᴄᴘᴜ:** `{CPU}`\n"
        f"**├ 💾 ʀᴀᴍ:** `{RAM}`\n"
        f"**└ 💿 ᴅɪsᴋ:** `{DISK}`\n\n"
        f"**🌟 ᴛᴏᴛᴀʟ ɪɴᴛᴇʀᴀᴄᴛɪᴏɴs:** `{users + chats:,}`\n\n"
        f"**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"
    )
    
    await message.reply_photo(
        photo=random.choice(IMG),
        caption=stats_text,
        reply_markup=InlineKeyboardMarkup(stats_buttons)
    )

@Client.on_message(filters.command("id"))
async def get_id(client, message: Message):
    chat = message.chat
    user_id = message.from_user.id
    msg_id = message.id
    reply = message.reply_to_message

    text = f"**📌 ɪᴅ ɪɴғᴏʀᴍᴀᴛɪᴏɴ**\n\n"
    text += f"**🆔 ʙᴀsɪᴄ ɪᴅs:**\n"
    text += f"**├ 💬 ᴍᴇssᴀɢᴇ ɪᴅ:** `{msg_id}`\n"
    text += f"**├ 👤 ʏᴏᴜʀ ɪᴅ:** `{user_id}`\n"
    text += f"**└ 🏠 ᴄʜᴀᴛ ɪᴅ:** `{chat.id}`\n\n"

    if len(message.command) == 2:
        try:
            user = message.text.split(None, 1)[1].strip()
            user_info = await client.get_users(user)
            text += f"**🔍 ʟᴏᴏᴋᴇᴅ ᴜᴘ ᴜsᴇʀ:**\n"
            text += f"**├ 👤 ɴᴀᴍᴇ:** {user_info.first_name}\n"
            text += f"**├ 🆔 ᴜsᴇʀ ɪᴅ:** `{user_info.id}`\n"
            text += f"**└ 📛 ᴜsᴇʀɴᴀᴍᴇ:** @{user_info.username or 'ɴ/ᴀ'}\n\n"
        except:
            text += "**⚠️ ᴜsᴇʀ ɴᴏᴛ ғᴏᴜɴᴅ**\n\n"

    if reply:
        text += f"**↩️ ʀᴇᴘʟɪᴇᴅ ᴍᴇssᴀɢᴇ ɪɴғᴏ:**\n"
        text += f"**├ 💬 ᴍsɢ ɪᴅ:** `{reply.id}`\n"
        if reply.from_user:
            text += f"**├ 👤 ᴜsᴇʀ ɪᴅ:** `{reply.from_user.id}`\n"
            text += f"**└ 📛 ᴜsᴇʀɴᴀᴍᴇ:** @{reply.from_user.username or 'ɴ/ᴀ'}\n"
        if reply.forward_from_chat:
            text += f"**└ 📤 ғᴏʀᴡᴀʀᴅᴇᴅ ғʀᴏᴍ:** `{reply.forward_from_chat.id}`\n"
        if reply.sender_chat:
            text += f"**└ 📢 sᴇɴᴅᴇʀ ᴄʜᴀᴛ:** `{reply.sender_chat.id}`"

    await message.reply_text(text, disable_web_page_preview=True)

# Broadcast Command (Optimized)
@Client.on_message(filters.command(["broadcast", "gcast"]))
async def broadcast_command(client, message: Message):
    bot_id = client.me.id
    user_id = message.from_user.id
    
    if not await is_owner(bot_id, user_id):
        return await message.reply("⚠️ **ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ**")
        
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply(
            "**📢 ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅ ᴜsᴀɢᴇ:**\n\n"
            "**1.** ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ `/broadcast`\n"
            "**2.** ᴏʀ ᴜsᴇ `/broadcast <ʏᴏᴜʀ ᴍᴇssᴀɢᴇ>`\n\n"
            "**🎛 ᴀᴠᴀɪʟᴀʙʟᴇ ғʟᴀɢs:**\n"
            "• `-pin` - ᴘɪɴ ᴍᴇssᴀɢᴇ sɪʟᴇɴᴛʟʏ\n"
            "• `-pinloud` - ᴘɪɴ ᴡɪᴛʜ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ\n"
            "• `-user` - sᴇɴᴅ ᴛᴏ ᴜsᴇʀs ᴏɴʟʏ\n"
            "• `-nogroup` - sᴋɪᴘ ɢʀᴏᴜᴘs"
        )

    query = message.text.split(None, 1)[1] if len(message.command) > 1 else ""
    flags = {
        "-pin": "-pin" in query,
        "-pinloud": "-pinloud" in query,
        "-nogroup": "-nogroup" in query,
        "-user": "-user" in query,
    }

    content = message.reply_to_message if message.reply_to_message else query.replace("-pin", "").replace("-pinloud", "").replace("-nogroup", "").replace("-user", "").strip()

    if not content:
        return await message.reply("⚠️ **ɴᴏ ᴄᴏɴᴛᴇɴᴛ ғᴏᴜɴᴅ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ**")

    processing = await message.reply("**📡 ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ...**")

    # Broadcast to Groups
    if not flags.get("-nogroup"):
        sent_groups = 0
        failed_groups = 0
        pinned_groups = 0
        groups = await get_served_cchats(bot_id)
        total_groups = len(groups)
        
        for i, group in enumerate(groups):
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
                        pass
                
                # Update progress every 10 groups
                if (i + 1) % 10 == 0:
                    await processing.edit(f"**📡 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...**\n\n**📊 ᴘʀᴏɢʀᴇss:** `{i + 1}/{total_groups}`\n**✅ sᴜᴄᴄᴇss:** `{sent_groups}`")
                
                await asyncio.sleep(0.1)  # Faster sending
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                failed_groups += 1
                continue

        result_text = f"**✅ ɢʀᴏᴜᴘ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n"
        result_text += f"**📊 ʀᴇsᴜʟᴛs:**\n"
        result_text += f"**├ ✅ sᴇɴᴛ:** `{sent_groups}`\n"
        result_text += f"**├ ❌ ғᴀɪʟᴇᴅ:** `{failed_groups}`\n"
        result_text += f"**└ 📌 ᴘɪɴɴᴇᴅ:** `{pinned_groups}`"
        
        await processing.edit(result_text)

    # Broadcast to Users
    if flags.get("-user"):
        sent_users = 0
        failed_users = 0
        users = await get_served_cusers(bot_id)
        total_users = len(users)
        
        user_processing = await message.reply("**👥 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴛᴏ ᴜsᴇʀs...**")
        
        for i, user in enumerate(users):
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
                
                # Update progress every 20 users
                if (i + 1) % 20 == 0:
                    await user_processing.edit(f"**👥 ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ...**\n\n**📊 ᴘʀᴏɢʀᴇss:** `{i + 1}/{total_users}`\n**✅ sᴜᴄᴄᴇss:** `{sent_users}`")
                
                await asyncio.sleep(0.05)  # Faster for users
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                failed_users += 1
                continue

        user_result = f"**✅ ᴜsᴇʀ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\n"
        user_result += f"**📊 ʀᴇsᴜʟᴛs:**\n"
        user_result += f"**├ ✅ sᴇɴᴛ:** `{sent_users}`\n"
        user_result += f"**└ ❌ ғᴀɪʟᴇᴅ:** `{failed_users}`"
        
        await user_processing.edit(user_result)

# File Manager Commands (Owner Only)
@Client.on_message(filters.command(["ls"]) & filters.user(int(OWNER_ID)))
async def list_files(_, m: Message):
    """List all files and folders."""
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
                elif ext in (".py", ".js", ".html", ".css", ".json"):
                    files.append(f"💻 `{item}`")
                elif ext in (".txt", ".md", ".log"):
                    files.append(f"📝 `{item}`")
                else:
                    files.append(f"📄 `{item}`")
        
        msg += "\n".join(folders + files) if folders or files else "**📂 ᴇᴍᴘᴛʏ ᴅɪʀᴇᴄᴛᴏʀʏ**"
    else:
        size = os.stat(path).st_size
        ext = os.path.splitext(path)[1].lower()
        
        # File type icons
        icon_map = {
            (".mp3", ".flac", ".wav", ".m4a"): "🎵",
            (".opus",): "🎙",
            (".mkv", ".mp4", ".webm", ".avi", ".mov", ".flv"): "🎞",
            (".zip", ".tar", ".tar.gz", ".rar"): "🗜",
            (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico"): "🖼",
            (".py", ".js", ".html", ".css", ".json"): "💻",
            (".txt", ".md", ".log"): "📝"
        }
        
        icon = "📄"  # default
        for extensions, file_icon in icon_map.items():
            if ext in extensions:
                icon = file_icon
                break
        
        msg = (
            f"**📌 ғɪʟᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ**\n\n"
            f"**• ɴᴀᴍᴇ:** `{os.path.basename(path)}`\n"
            f"**• ᴛʏᴘᴇ:** {icon}\n"
            f"**• sɪᴢᴇ:** `{humanbytes(size)}`\n"
            f"**• ᴘᴀᴛʜ:** `{path}`\n"
            f"**• ᴍᴏᴅɪғɪᴇᴅ:** `{time.ctime(os.path.getmtime(path))}`\n"
            f"**• ᴀᴄᴄᴇssᴇᴅ:** `{time.ctime(os.path.getatime(path))}`"
        )

    if len(msg) > 4096:
        with io.BytesIO(str.encode(msg)) as file:
            file.name = "file_list.txt"
            await m.reply_document(file, caption=f"**📂 ᴘᴀᴛʜ:** `{path}`")
    else:
        await m.reply_text(msg)

# Callback Query Handlers
@Client.on_callback_query(filters.regex("close"))
async def close_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

@Client.on_callback_query(filters.regex("refresh_ping"))
async def refresh_ping_callback(client, callback_query: CallbackQuery):
    start = datetime.now()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    ms = (datetime.now() - start).microseconds / 1000
    settings = await get_bot_settings(client.me.id)
    
    ping_buttons = [
        [
            InlineKeyboardButton("🔄 ʀᴇғʀᴇsʜ", callback_data="refresh_ping"),
            InlineKeyboardButton("📊 ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛs", callback_data="detailed_stats")
        ],
        [
            InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
            InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
        ]
    ]
    
    await callback_query.edit_message_text(
        text=(
            f"**⚡ {client.me.first_name} sᴛᴀᴛs ⚡**\n\n"
            f"**📊 sʏsᴛᴇᴍ ᴘᴇʀғᴏʀᴍᴀɴᴄᴇ:**\n"
            f"**├ 📡 ᴘɪɴɢ:** `{ms:.2f}` ms\n"
            f"**├ 🖥 ᴄᴘᴜ:** `{CPU}`\n"
            f"**├ 💾 ʀᴀᴍ:** `{RAM}`\n"
            f"**├ 💿 ᴅɪsᴋ:** `{DISK}`\n"
            f"**└ ⏰ ᴜᴘᴛɪᴍᴇ:** `{UP}`\n\n"
            f"**🚀 sᴛᴀᴛᴜs:** {'🟢 ᴏɴʟɪɴᴇ' if ms < 100 else '🟡 sʟᴏᴡ' if ms < 200 else '🔴 ʟᴀɢɢɪɴɢ'}\n\n"
            f"**🔥 ᴘᴏᴡᴇʀᴇᴅ  ᴊᴜsᴛ ᴛᴀɢ ᴍᴇ ᴏʀ ʀᴇᴘʟʏ ᴛᴏ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ!**\n\n"
            f"**🔥 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @ShrutiBots**"
        )
        
        await message.reply_photo(
            photo=random.choice(IMG),
            caption=enhanced_group_start,
            reply_markup=InlineKeyboardMarkup(group_buttons),
        )
        await add_served_cchat(bot_id, message.chat.id)
        await add_served_chat(message.chat.id)

@Client.on_message(filters.command("help"))
async def help_command(client, message: Message):
    bot_id = client.me.id
    settings = await get_bot_settings(bot_id)
    
    if message.chat.type == ChatType.PRIVATE:
        help_buttons = [
            [
                InlineKeyboardButton("🤖 ᴄʜᴀᴛʙᴏᴛ", callback_data="help_chatbot"),
                InlineKeyboardButton("🌍 ʟᴀɴɢᴜᴀɢᴇ", callback_data="help_language")
            ],
            [
                InlineKeyboardButton("📊 sᴛᴀᴛs", callback_data="help_stats"),
                InlineKeyboardButton("🛠 ᴀᴅᴍɪɴ", callback_data="help_admin")
            ],
            [
                InlineKeyboardButton("📢 sᴜᴘᴘᴏʀᴛ ᴄʜᴀɴɴᴇʟ", url=settings['support_channel']),
                InlineKeyboardButton("👥 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ", url=settings['support_group'])
            ],
            [InlineKeyboardButton("🔒 ᴄʟᴏsᴇ", callback_data="close")]
        ]
        
        help_text = (
            f"**🛠 ʜᴇʟᴘ ᴍᴇɴᴜ - {client.me.first_name}**\n\n"
            f"**🤖 ᴄʜᴀᴛʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            f"• `/chatbot` - ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ\n"
            f"• `/status` - ᴄʜᴇᴄᴋ ᴄʜᴀᴛʙᴏᴛ sᴛᴀᴛᴜs\n\n"
            f"**🌍 ʟᴀɴɢᴜᴀɢᴇ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            f"• `/lang` - sᴇᴛ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ\n"
            f"• `/chatlang` - ᴄʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ ʟᴀɴɢᴜᴀɢᴇ\n"
            f"• `/resetlang` - ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ\n\n"
            f"**📊 ɪɴғᴏ ᴄᴏᴍᴍᴀɴᴅs:**\n"
            f"• `/ping` - ᴄʜᴇᴄᴋ ʙᴏᴛ sᴛᴀᴛᴜs\n"
            f"• `/stats` - ᴠɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
            f"• `/id` - ɢᴇᴛ ᴄʜᴀᴛ/ᴜsᴇʀ ɪᴅs\n\n"
            f"**💬
