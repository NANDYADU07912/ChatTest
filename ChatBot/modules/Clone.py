import logging
import os
import sys
import shutil
import asyncio
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import config
from config import API_HASH, API_ID, OWNER_ID
from ChatBot import CLONE_OWNERS
from ChatBot import ChatBot as app, save_clonebot_owner
from ChatBot import db as mongodb

CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb
bot_settings_db = mongodb.bot_settings

# Default support links
DEFAULT_SUPPORT_CHANNEL = "https://t.me/ShrutiBots"
DEFAULT_SUPPORT_GROUP = "https://t.me/ShrutiBotsSupport"

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
    
@app.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        bot_token = message.text.split("/clone", 1)[1].strip()
        mi = await message.reply_text("⏳ **Please wait while I check the bot token...**")
        try:
            ai = Client(bot_token, API_ID, API_HASH, bot_token=bot_token, plugins=dict(root="ChatBot/mplugin"))
            await ai.start()
            bot = await ai.get_me()
            bot_id = bot.id
            user_id = message.from_user.id
            await save_clonebot_owner(bot_id, user_id)
            await ai.set_bot_commands([
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get the help menu"),
                    BotCommand("clone", "Make your own chatbot"),
                    BotCommand("ping", "Check if the bot is alive or dead"),
                    BotCommand("lang", "Select bot reply language"),
                    BotCommand("chatlang", "Get current using lang for chat"),
                    BotCommand("resetlang", "Reset to default bot reply lang"),
                    BotCommand("id", "Get users user_id"),
                    BotCommand("stats", "Check bot stats"),
                    BotCommand("gcast", "Broadcast any message to groups/users"),
                    BotCommand("chatbot", "Enable or disable chatbot"),
                    BotCommand("status", "Check chatbot enable or disable in chat"),
                    BotCommand("shayri", "Get random shayri for love"),
                    BotCommand("ask", "Ask anything from chatgpt"),
                    BotCommand("repo", "Get chatbot source code"),
                    BotCommand("mybots", "Manage your cloned bots"),
                    BotCommand("setsupportgroup", "Set custom support group"),
                    BotCommand("setsupportchannel", "Set custom support channel"),
                ])
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("❌ **Invalid bot token. Please provide a valid one.**")
            return
        except Exception as e:
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("🤖 **Your bot is already cloned ✅**")
                return

        await mi.edit_text("🔄 **Cloning process started. Please wait for the bot to start...**")
        try:
            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
            }
            cloned_bots = clonebotdb.find()
            cloned_bots_list = await cloned_bots.to_list(length=None)
            total_clones = len(cloned_bots_list)
            
            # Initialize bot settings with default values
            await get_bot_settings(bot.id)
            
            await app.send_message(
                int(OWNER_ID), f"**#New_Clone**\n\n**Bot:- @{bot.username}**\n**Owner:- {message.from_user.mention}**\n\n**Details:-**\n{details}\n\n**Total Cloned:-** {total_clones + 1}"
            )

            await clonebotdb.insert_one(details)
            
            CLONES.add(bot.id)

            buttons = [
                [InlineKeyboardButton("🛠 Modify Your Bot", callback_data=f"modify_bot_{bot.id}")],
                [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")]
            ]

            await mi.edit_text(
                f"✅ **Bot @{bot.username} has been successfully cloned and started!**\n\n"
                f"🎉 **Congratulations! Your bot is now live and ready to use.**\n\n"
                f"🛠 **Want to customize your bot?** Click the button below to modify settings!\n\n"
                f"📋 **View all your bots:** Use /mybots command\n"
                f"❌ **Remove clone:** Use /delclone command",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ **Error occurred while cloning:**\n\n`{str(e)[:1000]}`\n\n**Forward this message to @ShrutiBotSupport for assistance**"
            )
    else:
        await message.reply_text(
            "🤖 **Clone Your Own ChatBot!**\n\n"
            "**📝 How to get bot token:**\n"
            "1. Go to @BotFather\n"
            "2. Create a new bot with /newbot\n"
            "3. Copy the bot token\n"
            "4. Use: `/clone YOUR_BOT_TOKEN`\n\n"
            "**Example:** `/clone 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`"
        )

@app.on_message(filters.command("cloned") & filters.user(int(OWNER_ID)))
async def list_cloned_bots(client, message):
    try:
        cloned_bots = clonebotdb.find()
        cloned_bots_list = await cloned_bots.to_list(length=None)
        if not cloned_bots_list:
            await message.reply_text("📭 **No bots have been cloned yet.**")
            return
        total_clones = len(cloned_bots_list)
        text = f"🤖 **Total Cloned Bots:** `{total_clones}`\n\n"
        for i, bot in enumerate(cloned_bots_list, 1):
            try:
                owner = await app.get_users(bot['user_id'])
                owner_mention = owner.mention
            except:
                owner_mention = f"User ID: {bot['user_id']}"
            
            text += f"**{i}.** **@{bot['username']}**\n"
            text += f"   ├ **Bot ID:** `{bot['bot_id']}`\n"
            text += f"   ├ **Owner:** {owner_mention}\n"
            text += f"   └ **Name:** {bot['name']}\n\n"
        
        if len(text) > 4000:
            with open("cloned_bots.txt", "w") as f:
                f.write(text)
            await message.reply_document("cloned_bots.txt", caption=f"📊 **Total Cloned Bots:** `{total_clones}`")
            os.remove("cloned_bots.txt")
        else:
            await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("❌ **An error occurred while listing cloned bots.**")

@app.on_message(filters.command("mybots"))
async def my_bots(client, message):
    try:
        user_id = message.from_user.id
        user_bots = clonebotdb.find({"user_id": user_id})
        user_bots_list = await user_bots.to_list(length=None)
        
        if not user_bots_list:
            await message.reply_text(
                "🤖 **You haven't cloned any bots yet!**\n\n"
                "**Want to create your own bot?**\n"
                "Use: `/clone YOUR_BOT_TOKEN`\n\n"
                "**Need help?** @ShrutiBotsSupport"
            )
            return
        
        buttons = []
        text = f"🤖 **Your Cloned Bots ({len(user_bots_list)}):**\n\n"
        
        for i, bot in enumerate(user_bots_list, 1):
            text += f"**{i}.** @{bot['username']} (`{bot['bot_id']}`)\n"
            buttons.append([InlineKeyboardButton(f"🛠 Modify @{bot['username']}", callback_data=f"modify_bot_{bot['bot_id']}")])
        
        buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="my_bots")])
        buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logging.exception(e)
        await message.reply_text("❌ **An error occurred while fetching your bots.**")

@app.on_callback_query(filters.regex("my_bots"))
async def my_bots_callback(client, callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        user_bots = clonebotdb.find({"user_id": user_id})
        user_bots_list = await user_bots.to_list(length=None)
        
        if not user_bots_list:
            await callback_query.edit_message_text(
                "🤖 **You haven't cloned any bots yet!**\n\n"
                "**Want to create your own bot?**\n"
                "Use: `/clone YOUR_BOT_TOKEN`\n\n"
                "**Need help?** @ShrutiBotsSupport"
            )
            return
        
        buttons = []
        text = f"🤖 **Your Cloned Bots ({len(user_bots_list)}):**\n\n"
        
        for i, bot in enumerate(user_bots_list, 1):
            text += f"**{i}.** @{bot['username']} (`{bot['bot_id']}`)\n"
            buttons.append([InlineKeyboardButton(f"🛠 Modify @{bot['username']}", callback_data=f"modify_bot_{bot['bot_id']}")])
        
        buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="my_bots")])
        buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
        
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logging.exception(e)
        await callback_query.answer("❌ An error occurred!", show_alert=True)

@app.on_callback_query(filters.regex("modify_bot_"))
async def modify_bot_callback(client, callback_query: CallbackQuery):
    try:
        bot_id = int(callback_query.data.split("_")[-1])
        user_id = callback_query.from_user.id
        
        # Check if user owns this bot
        bot_data = await clonebotdb.find_one({"bot_id": bot_id, "user_id": user_id})
        if not bot_data:
            await callback_query.answer("❌ You don't own this bot!", show_alert=True)
            return
        
        settings = await get_bot_settings(bot_id)
        
        text = f"🛠 **Modify Bot: @{bot_data['username']}**\n\n"
        text += "**🎨 Customize Your Bot Settings:**\n\n"
        text += f"**📢 Support Channel:** `{settings['support_channel']}`\n"
        text += f"**👥 Support Group:** `{settings['support_group']}`\n\n"
        text += "**🔧 Available Commands:**\n"
        text += f"• `/setsupportchannel <url>` - Set support channel\n"
        text += f"• `/setsupportgroup <url>` - Set support group\n\n"
        text += "**💡 How to customize:**\n"
        text += "1. Go to your bot @{}\n".format(bot_data['username'])
        text += "2. Use the commands above to set custom links\n"
        text += "3. If you don't set custom links, default @ShrutiBots links will be used\n\n"
        text += "**📌 Note:** Changes will be applied immediately to your bot's start message!"
        
        buttons = [
            [InlineKeyboardButton("🔙 Back to My Bots", callback_data="my_bots")],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ]
        
        await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logging.exception(e)
        await callback_query.answer("❌ An error occurred!", show_alert=True)

@app.on_callback_query(filters.regex("close_menu"))
async def close_menu_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

@app.on_message(
    filters.command(["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"])
)
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("⚠️ **Please provide the bot token after the command.**\n\n**Example:** `/delclone YOUR_BOT_TOKEN`")
            return

        bot_token = " ".join(message.command[1:])
        ok = await message.reply_text("🔍 **Checking the bot token...**")

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            # Check if user owns this bot or is the main owner
            if cloned_bot["user_id"] != message.from_user.id and message.from_user.id != int(OWNER_ID):
                await ok.edit_text("❌ **You can only delete your own cloned bots!**")
                return
            
            await clonebotdb.delete_one({"token": bot_token})
            await bot_settings_db.delete_one({"bot_id": cloned_bot["bot_id"]})
            
            if cloned_bot["bot_id"] in CLONES:
                CLONES.remove(cloned_bot["bot_id"])

            await ok.edit_text(
                f"✅ **Bot @{cloned_bot['username']} has been removed successfully!**\n\n"
                f"⚠️ **Important:** Please revoke your bot token from @BotFather to completely stop the bot.\n\n"
                f"**🔄 How to revoke token:**\n"
                f"1. Go to @BotFather\n"
                f"2. Send /mybots\n"
                f"3. Select your bot\n"
                f"4. Click 'API Token'\n"
                f"5. Click 'Revoke current token'"
            )
        else:
            await ok.edit_text(
                "❌ **Bot not found in database!**\n\n"
                "**Make sure you're using the correct bot token.**\n"
                "**Example:** `/delclone YOUR_BOT_TOKEN`"
            )
    except Exception as e:
        await message.reply_text(f"❌ **An error occurred while deleting the bot:** `{str(e)[:500]}`")
        logging.exception(e)

async def restart_bots():
    global CLONES
    try:
        logging.info("🔄 Restarting all cloned bots...")
        bots = [bot async for bot in clonebotdb.find()]
        
        async def restart_bot(bot):
            bot_token = bot["token"]
            ai = Client(bot_token, API_ID, API_HASH, bot_token=bot_token, plugins=dict(root="ChatBot/mplugin"))
            try:
                await ai.start()
                bot_info = await ai.get_me()
                await ai.set_bot_commands([
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get the help menu"),
                    BotCommand("clone", "Make your own chatbot"),
                    BotCommand("ping", "Check if the bot is alive or dead"),
                    BotCommand("lang", "Select bot reply language"),
                    BotCommand("chatlang", "Get current using lang for chat"),
                    BotCommand("resetlang", "Reset to default bot reply lang"),
                    BotCommand("id", "Get users user_id"),
                    BotCommand("stats", "Check bot stats"),
                    BotCommand("gcast", "Broadcast any message to groups/users"),
                    BotCommand("chatbot", "Enable or disable chatbot"),
                    BotCommand("status", "Check chatbot enable or disable in chat"),
                    BotCommand("shayri", "Get random shayri for love"),
                    BotCommand("ask", "Ask anything from chatgpt"),
                    BotCommand("repo", "Get chatbot source code"),
                    BotCommand("mybots", "Manage your cloned bots"),
                    BotCommand("setsupportgroup", "Set custom support group"),
                    BotCommand("setsupportchannel", "Set custom support channel"),
                ])

                if bot_info.id not in CLONES:
                    CLONES.add(bot_info.id)
                    logging.info(f"✅ Restarted bot: @{bot_info.username}")
                    
            except (AccessTokenExpired, AccessTokenInvalid):
                await clonebotdb.delete_one({"token": bot_token})
                await bot_settings_db.delete_one({"bot_id": bot["bot_id"]})
                logging.info(f"🗑 Removed expired token for bot ID: {bot['bot_id']}")
            except Exception as e:
                logging.exception(f"❌ Error restarting bot {bot['bot_id']}: {e}")
            
        await asyncio.gather(*(restart_bot(bot) for bot in bots), return_exceptions=True)
        logging.info(f"🎉 Successfully restarted {len(CLONES)} bots")
        
    except Exception as e:
        logging.exception("❌ Error while restarting bots.")

@app.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("🗑 **Deleting all cloned bots...**")
        
        # Get count before deletion
        total_bots = len(await clonebotdb.find().to_list(length=None))
        
        # Delete all cloned bots and their settings
        await clonebotdb.delete_many({})
        await bot_settings_db.delete_many({})
        CLONES.clear()
        
        await a.edit_text(f"✅ **Successfully deleted {total_bots} cloned bots!**\n\n🔄 **Restarting system...**")
        os.system(f"kill -9 {os.getpid()} && bash start")
    except Exception as e:
        await a.edit_text(f"❌ **Error occurred:** `{str(e)[:500]}`")
        logging.exception(e)
