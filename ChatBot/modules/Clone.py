# UI Enhanced Version 🌟
# Note: Functional logic untouched – only added styled messages and inline formatting.

import logging
import os
import sys
import shutil
import asyncio
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config
from pyrogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from config import API_HASH, API_ID, OWNER_ID
from ChatBot import CLONE_OWNERS
from ChatBot import ChatBot as app, save_clonebot_owner
from ChatBot import db as mongodb

CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb


@app.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        bot_token = message.text.split("/clone", 1)[1].strip()
        mi = await message.reply_text("🔍 <b>Checking the Bot Token, Please wait...</b>")
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
            ])
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("❌ <b>Invalid bot token. Please provide a valid one.</b>")
            return
        except Exception:
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("✅ <b>Your bot is already cloned.</b>")
                return

        await mi.edit_text("⚙️ <b>Cloning process started... Please wait for the bot to be up!</b>")
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
                f"🆕 <b>#New_Clone</b>\n\n🤖 <b>Bot:</b> @{bot.username}\n\n<b>Details:</b>\n<code>{details}</code>\n\n<b>Total Cloned:</b> {total_clones}"
            )

            await clonebotdb.insert_one(details)
            CLONES.add(bot.id)

            await mi.edit_text(
                f"✅ <b>Bot</b> @{bot.username} <b>has been successfully cloned and started.</b>\n\n🗑️ To delete: <code>/delclone {bot_token}</code>\n📜 View list: <code>/cloned</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.username}")]])
            )
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ <b>Error:</b>\n<code>{e}</code>\n\n📩 <b>Contact:</b> @ShrutiBotSupport"
            )
    else:
        await message.reply_text(
            "⚠️ <b>Please provide the Bot Token after the /clone command.</b>\n\n<b>Example:</b>\n<code>/clone 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>"
        )


@app.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    try:
        cloned_bots = clonebotdb.find()
        cloned_bots_list = await cloned_bots.to_list(length=None)
        if not cloned_bots_list:
            await message.reply_text("🤖 <b>No bots have been cloned yet.</b>")
            return
        total_clones = len(cloned_bots_list)
        text = f"🤖 <b>Total Cloned Bots:</b> <code>{total_clones}</code>\n\n"
        for bot in cloned_bots_list:
            text += (
                f"🔹 <b>Name:</b> {bot['name']}\n"
                f"🔸 <b>Username:</b> @{bot['username']}\n"
                f"🆔 <b>ID:</b> <code>{bot['bot_id']}</code>\n\n"
            )
        await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("❌ <b>An error occurred while listing cloned bots.</b>")


@app.on_message(
    filters.command(["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"])
)
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("⚠️ <b>Please provide the Bot Token after the command.</b>")
            return

        bot_token = " ".join(message.command[1:])
        ok = await message.reply_text("🔍 <b>Verifying token...</b>")

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token})
            CLONES.remove(cloned_bot["bot_id"])
            await ok.edit_text(
                f"🗑️ <b>Bot @{cloned_bot['username']} has been removed from the database.</b>\n\n⚠️ <b>Don't forget to revoke the token from @BotFather!</b>"
            )
        else:
            await message.reply_text("❌ <b>Bot token not found in the database.</b>")
    except Exception as e:
        await message.reply_text(f"❌ <b>Error:</b> <code>{e}</code>")
        logging.exception(e)


async def restart_bots():
    global CLONES
    try:
        logging.info("Restarting all cloned bots...")
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
                ])
                if bot_info.id not in CLONES:
                    CLONES.add(bot_info.id)
            except (AccessTokenExpired, AccessTokenInvalid):
                await clonebotdb.delete_one({"token": bot_token})
                logging.info(f"🗑️ Removed invalid token: {bot['bot_id']}")
            except Exception as e:
                logging.exception(f"Error while restarting bot {bot_token}: {e}")

        await asyncio.gather(*(restart_bot(bot) for bot in bots))

    except Exception as e:
        logging.exception("Error while restarting bots.")


@app.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("🗑️ <b>Deleting all cloned bots...</b>")
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text("✅ <b>All cloned bots removed successfully!</b>\n🔄 <i>Restarting main bot...</i>")
        os.system(f"kill -9 {os.getpid()} && bash start")
    except Exception as e:
        await a.edit_text(f"❌ <b>Error:</b> <code>{e}</code>")
        logging.exception(e)
