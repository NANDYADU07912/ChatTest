import logging
import os
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config
from ChatBot.mplugin.helpers import is_owner
from config import API_HASH, API_ID, OWNER_ID
from ChatBot import CLONE_OWNERS
from ChatBot import ChatBot as app, save_clonebot_owner
from ChatBot import db as mongodb, ChatBot

CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb


@Client.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        bot_token = message.text.split("/clone", 1)[1].strip()
        mi = await message.reply_text("🔍 <b>Checking the provided bot token...</b>", parse_mode=ParseMode.HTML)
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
                BotCommand("idclone", "Make your id-chatbot"),
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
                BotCommand("repo", "Get chatbot source code"),
            ])
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("❌ <b>Invalid bot token!</b>\nPlease provide a valid one from @BotFather.", parse_mode=ParseMode.HTML)
            return
        except Exception as e:
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("✅ <b>This bot is already cloned!</b>\nNo need to clone again.", parse_mode=ParseMode.HTML)
                return

        await mi.edit_text("⚙️ <b>Cloning process started…</b>\nPlease wait a moment while I set up your bot.", parse_mode=ParseMode.HTML)
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

            await app.send_message(
                int(OWNER_ID),
                f"🚀 <b>#New_Clone</b>\n\n🤖 <b>Bot:</b> @{bot.username}\n\n🗂️ <b>Details:</b>\n<code>{details}</code>\n\n📊 <b>Total Cloned:</b> {total_clones}",
                parse_mode=ParseMode.HTML
            )

            await clonebotdb.insert_one(details)
            CLONES.add(bot.id)

            await mi.edit_text(
                f"✅ <b>Your bot</b> @{bot.username} <b>has been successfully cloned & deployed!</b>\n\n"
                "🗑️ <b>To delete:</b> <code>/delidclone</code>\n"
                "📋 <b>Check list:</b> <code>/idcloned</code>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🤖 Open Your Bot", url=f"https://t.me/{bot.username}")]]
                ),
                parse_mode=ParseMode.HTML
            )
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ <b>Error occurred:</b>\n<code>{e}</code>\n\n💬 <b>Contact:</b> @ShrutiBotSupport for help.",
                parse_mode=ParseMode.HTML
            )
    else:
        await message.reply_text(
            "⚠️ <b>Please provide the bot token after the command.</b>\n\n"
            "📌 <b>Example:</b>\n<code>/clone 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>",
            parse_mode=ParseMode.HTML
        )


@Client.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    try:
        cloned_bots = clonebotdb.find()
        cloned_bots_list = await cloned_bots.to_list(length=None)
        if not cloned_bots_list:
            await message.reply_text("📭 <b>No cloned bots found!</b>", parse_mode=ParseMode.HTML)
            return

        total_clones = len(cloned_bots_list)
        text = f"📋 <b>Total Cloned Bots:</b> <code>{total_clones}</code>\n\n"
        for bot in cloned_bots_list:
            text += (
                f"🤖 <b>Bot:</b> @{bot['username']}\n"
                f"🆔 <b>ID:</b> <code>{bot['bot_id']}</code>\n"
                f"📛 <b>Name:</b> {bot['name']}\n\n"
            )
        await message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("❌ <b>An error occurred while fetching cloned bots.</b>", parse_mode=ParseMode.HTML)


@Client.on_message(filters.command(["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"]))
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "⚠️ <b>Please provide the bot token to delete a cloned bot.</b>\n\n"
                "📌 <b>Example:</b> <code>/delclone 123456:ABC-XYZ</code>",
                parse_mode=ParseMode.HTML
            )
            return

        bot_token = " ".join(message.command[1:])
        ok = await message.reply_text("🔍 <b>Checking token in database...</b>", parse_mode=ParseMode.HTML)

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token})

            await ok.edit_text(
                f"🗑️ <b>Bot @{cloned_bot['username']} has been removed from database.</b>\n\n"
                "⚠️ <i>Don’t forget to revoke the token from @BotFather.</i>",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text("❌ <b>No bot found with the given token.</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ <b>Error occurred:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        logging.exception(e)


@Client.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("🧹 <b>Cleaning all cloned bots…</b>", parse_mode=ParseMode.HTML)
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text("✅ <b>All cloned bots deleted successfully!</b>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await a.edit_text(f"❌ <b>Error occurred while cleaning bots:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        logging.exception(e)
