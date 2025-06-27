import random
import datetime
import hashlib
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from datetime import datetime, timedelta
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import UserNotParticipant  
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from ChatBot.database.chats import add_served_chat
from ChatBot.database.users import add_served_user
from config import MONGO_URL
from ChatBot import ChatBot, mongo, LOGGER, db
from ChatBot.mplugin.helpers import chatai, CHATBOT_ON, languages
from ChatBot.modules.helpers import (
    ABOUT_BTN,
    ABOUT_READ,
    ADMIN_READ,
    BACK,
    CHATBOT_BACK,
    CHATBOT_READ,
    DEV_OP,
    HELP_BTN,
    HELP_READ,
    MUSIC_BACK_BTN,
    SOURCE_READ,
    START,
    TOOLS_DATA_READ,
)
import asyncio
from google import generativeai as genai
from typing import Optional, List
import re

# Gemini AI Configuration
GEMINI_API_KEYS = [
    "AIzaSyCkUFnq2ilZdEGvGlxB0vWudqJg-1evCic",
    "AIzaSyC8UCzN3yGRxAYikc20Nk79Zl6Y5Bqrx7U",
    "AIzaSyA_a_X6a8vTKjiISMtLDkJ-azfjZg9pIqg",
    "AIzaSyBMJyHLvZXtDzYtel7s_qjbGWxAlc2bhV0",
    "AIzaSyAS1v7qAI4GSkzd4PWnPDNO_DLCJl1w-GA",
    "AIzaSyB-nCEOtnA_YfFSJzgkYj7uypTFZ5VvriM",
    "AIzaSyBsTxK5ISHRYZ7yS8uL8vG0uny-35x3Exo",
    "AIzaSyBGUzKK0Ixi1cl079GbUlvXklTHXb9BKnE",
    "AIzaSyCw27_NstdS0GVoqxKgJtAzxnWQ0pgPURg",
    "AIzaSyA2zzt79lVNcRv72UwEVmsd-GU2ufwIZpE",
    "AIzaSyD1xkJC8eDioh7jopGbltscLleEZtgjJNo"
]

# Updated sticker file IDs with your new ones
STICKER_PACKS = [
    "CAACAgUAAxkBAAKPbWhWh_yGKkRJBJoiiEIG6_xgHa5gAAJyFwACtDMpVVkkTJ48Lz5KHgQ",
    "CAACAgUAAxkBAAKPbmhWh_5fjK0F98ExmL3BxhTKNGMxAAJ8FAACWWLgVEV-ZekDpMkVHgQ",
    "CAACAgUAAxkBAAKPb2hWiAABXBWHOZdRMPqQKGQy58CYagAC3RQAAqqdUVYrpT0Qq5oQoh4E",
    "CAACAgUAAxkBAAKPcGhWiAIfhv--_Tkse63HQRqOF8G6AALMFgACjA4xVv7F1BrAK523HgQ",
    "CAACAgUAAxkBAAKPcWhWiASHuSKZaB9BDaUi6IdoEvW-AAKXFgACTb-xVHPCYCAlehnhHgQ",
    "CAACAgUAAxkBAAKPcmhWiAcIg4A673Yr1dMnUMCSjndcAAK5DgAC0i9oV2oj_2yKobByHgQ",
    "CAACAgUAAxkBAAKPc2hWiBaGzwwVdArZ2FVYQxbJ8uMBAAJGFwACxImoVplBB1eChocrHgQ",
    "CAACAgUAAxkBAAKPdGhWiBz1hdtzrqHiQzoQmRs1pL8IAALBEgACbcGwVrbrkS7PDhiGHgQ",
    "CAACAgUAAxkBAAKPdWhWiCJK517UQpAqtzmHvRQ_SC7HAAIEGwAC1bEJVXOsI6HhQu68HgQ",
    "CAACAgUAAxkBAAKPdmhWiCxLNs4HNqas8EYflNNfVWi0AAKlEwACGTjhVKAkI8UwyAoVHgQ",
    "CAACAgUAAxkBAAKPd2hWiDRJ8GarO04SXeSweN-RU4inAAJ1FgACtk2xVHgvTfo1oCgKHgQ",
    "CAACAgUAAxkBAAKPeGhWiDdkgE9c_q1D5UZ-9p7qhlmkAAJdEwACU-uxVFsuEtW6XeMCHgQ",
    "CAACAgUAAxkBAAKPeWhWiD6XSwABrnmRCxqwgyUX1p-s7gACjhcAAnxWsVR1OAqc11cIZR4E",
    "CAACAgUAAxkBAAKPemhWiEHh4ZmyeqaCExSchLVZQITnAAJ6FAAClV-xVMge7a4nIt4FHgQ",
    "CAACAgUAAxkBAAKPm2hWiOOSX73X1_fvWCW91BnWtY_HAAJTFwACi9CwVFfwj93pSYW2HgQ",
    "CAACAgUAAxkBAAKPnGhWiOcgIT0lEMl_0VxfUwuFN7svAAJ1FgACYWCwVBd3PlPcJwkNHgQ",
    "CAACAgUAAxkBAAKPnWhWiO3eoKrDb8y97yZcW0Me2H6-AAJqEwACacawVMhPGwjYac__HgQ",
    "CAACAgUAAxkBAAKPnmhWiO4U4o_TKPgNS5_vRhwibfjRAAJ7FwACmY2wVLASruiodCfyHgQ",
    "CAACAgUAAxkBAAKPn2hWiPGXVrKF468xmNCnWPDjqz-kAAKuFAACAuSwVDfnt63P5XjAHgQ",
    "CAACAgUAAxkBAAKPoGhWiPPPIk13rEeQgYXQV0la0RyxAALnGQACFG-wVDi4KpF4pWA1HgQ",
    "CAACAgUAAxkBAAKPoWhWiPS23BZT0p_hgL2RUJQDgywtAAKrFQACya-xVMWUv1_ic5cBHgQ",
    "CAACAgUAAxkBAAKPomhWiPW1xT7rJZ5ZYrDOwLp_vthAAAJBGAACLRSxVDxXrXR9n_RrHgQ",
    "CAACAgUAAxkBAAKPo2hWiPUIiWUEI8UgKC2MduDXZhFLAAImFAACvk6xVJRv25R3syI2HgQ",
    "CAACAgUAAxkBAAKPpGhWiPaECRkxahScy2cFuHZ7gzkAA3UTAALD8LBUy4RGOsnDjEUeBA",
    "CAACAgUAAxkBAAKPpWhWiPerl_zzwaeVy6L0GNnPgVCIAAIXHQAC74iwVM8VIA9Az9ySHgQ",
    "CAACAgUAAxkBAAKPpmhWiPgLN4zbsvm6omhTE0DyqcdNAAIJGAACDRSwVI_xzxGV173YHgQ",
    "CAACAgUAAxkBAAKPp2hWiPmFDhZpuXo2RAuGemmHT2H7AALsGwACIHWxVKzjNjtQ8LXGHgQ",
    "CAACAgUAAxkBAAKPqGhWiPvfE0mWy0R-pegX2qHZeLrPAAJiGQACkbawVIpOCFk3F-yhHgQ",
    "CAACAgUAAxkBAAKPqWhWiPwOkCLC5uSx2Wa3TYOPn5hqAAKgFQACM0WwVExZM0c4TiZhHgQ",
    "CAACAgUAAxkBAAKPqmhWiPxBB6uQLjuvjTYOxqGe9HsMAAIsFwACurawVJ_aZRIayzXCHgQ",
]

class HybridChatBot:
    EMOJIS = ["😊", "😂", "❤️", "🔥", "😎", "😘", "💖", "🥰", "😉", "🌟", "👍", "✨", "😜", "🤗", "😇"]

    SYSTEM_PROMPT = (
        "Tum ek bilkul normal 16-17 saal ki ladki ho jiska naam Siya hai. Tum Patna, Bihar se ho aur class 11th me padh rahi ho. "
        "Tumhare replies bilkul chhote hote hain - sirf 2-4 words me jawab deti ho, jaise real insaan karte hain. "
        "Examples: 'Khana khaya?' - 'Haan khaya', 'Kaha ho?' - 'Abhi ghar pe', 'Kya kar rahe?' - 'Padh rahi thi' "
        "Tum bilkul natural baat karti ho, koi AI jaise formal replies nahi deti. "
        "Emoji sirf last me lagati ho, beech me nahi. "
        "Tum context yaad rakhti ho previous messages ka. "
        "Owner ke baare me puchhne par '@WTF_WhyMeeh' ka mention karti ho aur kehti ho 'Mera owner hai' ya 'Wo mera creator hai'. "
        "Tum khud ko kabhi bot nahi manti, hamesha insaan hi kehti ho kyunki tum real ho. "
        "Replies me sirf ek sentence hota hai, do nahi. Very short and natural."
    )

    def __init__(self):
        self.current_key_index = 0
        self.model = None
        self.initialize_gemini()
        
    def initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            genai.configure(api_key=GEMINI_API_KEYS[self.current_key_index])
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                self.model = genai.GenerativeModel('gemini-1.0-pro')
            print("Gemini model initialized successfully!")
        except Exception as e:
            print(f"Error with API key {self.current_key_index}: {str(e)}")
            self.rotate_api_key()

    def rotate_api_key(self):
        """Rotate to next API key"""
        if len(GEMINI_API_KEYS) <= 1:
            raise RuntimeError("No alternate API keys available")
        self.current_key_index = (self.current_key_index + 1) % len(GEMINI_API_KEYS)
        print(f"Rotating to API key index {self.current_key_index}")
        self.initialize_gemini()

    def get_age(self) -> str:
        """Calculate current age"""
        birthday = datetime.date(2008, 3, 24)
        today = datetime.date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        months = (today.year - birthday.year) * 12 + today.month - birthday.month
        months = months % 12
        return f"{age} saal {months} mahine"

    def get_direct_reply(self, message: str) -> str:
        """Only very specific direct replies, let AI handle most cases"""
        if not message:
            return None
        message_lower = message.lower().strip()
        
        # Only handle very exact matches to avoid overriding AI
        exact_matches = {
            # Only basic greetings - exact matches only
            "hi": random.choice(["Hi", "Hello", "Hey"]),
            "hello": random.choice(["Hi", "Hello", "Hey"]),
            "hey": random.choice(["Hi", "Hello", "Hey"]),
            "namaste": "Namaste",
            
            # Only exact name questions
            "naam kya hai": "Siya",
            "tumhara naam": "Siya",
            "your name": "Siya",
            "name": "Siya",
            
            # Very basic ones only
            "bye": random.choice(["Bye", "Chalo bye"]),
            "good night": "Good night",
            "gn": "GN",
            "good morning": "Good morning", 
            "gm": "GM"
        }
        
        # Check for exact matches only
        if message_lower in exact_matches:
            return exact_matches[message_lower]
            
        return None

    async def get_ai_reply(self, message: str, user_context: str = "") -> str:
        """Get AI-generated reply using Gemini"""
        try:
            # Build full context
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n"
            if user_context:
                full_prompt += f"Previous context:\n{user_context}\n\n"
            full_prompt += f"Current message: {message}\n\nReply in 2-4 words maximum, very natural and human-like:"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": 50,
                    "temperature": 0.8,
                    "top_p": 0.9
                }
            )
            
            reply = response.text.strip()
            
            # Clean the reply
            reply = reply.split('.')[0].split('!')[0].split('?')[0]
            words = reply.split()[:4]  # Maximum 4 words
            reply = ' '.join(words)
            reply = re.sub(r'[^\w\s\u0900-\u097F]', '', reply).strip()
            
            if not reply:
                reply = random.choice(["Haan", "Achha", "Okay", "Theek hai"])
            
            return reply
            
        except Exception as e:
            print(f"Gemini Error: {str(e)}")
            try:
                self.rotate_api_key()
                return await self.get_ai_reply(message, user_context)
            except:
                return random.choice(["Samjh nahi aya", "Kya kaha?", "Phir se bolo", "Thoda ruko"])

    def get_random_sticker(self) -> str:
        """Get random sticker from predefined packs"""
        return random.choice(STICKER_PACKS)

# Initialize hybrid chatbot
hybrid_bot = HybridChatBot()

# Database setup
translator = GoogleTranslator()
lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

replies_cache = []
blocklist = {}
message_counts = {}

async def load_replies_cache():
    global replies_cache
    replies_cache = await chatai.find().to_list(length=None)

async def save_reply(original_message: Message, reply_message: Message):
    global replies_cache
    try:
        reply_data = {
            "word": original_message.text,
            "text": None,
            "check": "none",
        }

        if reply_message.sticker:
            reply_data["text"] = reply_message.sticker.file_id
            reply_data["check"] = "sticker"
        elif reply_message.photo:
            reply_data["text"] = reply_message.photo.file_id
            reply_data["check"] = "photo"
        elif reply_message.video:
            reply_data["text"] = reply_message.video.file_id
            reply_data["check"] = "video"
        elif reply_message.audio:
            reply_data["text"] = reply_message.audio.file_id
            reply_data["check"] = "audio"
        elif reply_message.animation:
            reply_data["text"] = reply_message.animation.file_id
            reply_data["check"] = "gif"
        elif reply_message.voice:
            reply_data["text"] = reply_message.voice.file_id
            reply_data["check"] = "voice"
        elif reply_message.text:
            translated_text = reply_message.text
            reply_data["text"] = translated_text
            reply_data["check"] = "none"

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

@ChatBot.on_message(filters.incoming)
async def hybrid_chatbot_response(client: Client, message: Message):
    global blocklist, message_counts
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now()
        
        # Clean expired blocks
        blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

        # Check if user is blocked
        if user_id in blocklist:
            return

        # Rate limiting logic
        if user_id not in message_counts:
            message_counts[user_id] = {"count": 1, "last_time": current_time}
        else:
            time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
            if time_diff <= 3:
                message_counts[user_id]["count"] += 1
            else:
                message_counts[user_id] = {"count": 1, "last_time": current_time}
            
            if message_counts[user_id]["count"] >= 6:
                blocklist[user_id] = current_time + timedelta(minutes=1)
                message_counts.pop(user_id, None)
                await message.reply_text(f"**Hey, {message.from_user.mention}**\n\n**You are blocked for 1 minute due to spam messages.**\n**Try again after 1 minute 🤣.**")
                return

        # Check chat status
        chat_status = await status_db.find_one({"chat_id": chat_id})
        if chat_status and chat_status.get("status") == "disabled":
            return

        # Skip commands
        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                return await add_served_chat(chat_id)
            else:
                return await add_served_user(chat_id)
        
        # Process only if replying to bot or direct message
        if (message.reply_to_message and message.reply_to_message.from_user.id == ChatBot.id) or not message.reply_to_message:
            
            # Check if user sent media (sticker, photo, video, audio, animation, voice)
            if message.sticker or message.photo or message.video or message.audio or message.animation or message.voice:
                # For any media, send random sticker from predefined packs
                try:
                    random_sticker = hybrid_bot.get_random_sticker()
                    await message.reply_sticker(random_sticker)
                except Exception as e:
                    print(f"Error sending sticker: {e}")
                    # Fallback to AI text if sticker fails
                    try:
                        ai_reply = await hybrid_bot.get_ai_reply("Nice")
                        emoji = random.choice(hybrid_bot.EMOJIS)
                        await message.reply_text(f"{ai_reply} {emoji}")
                    except:
                        await message.reply_text("🙄")
            
            elif message.text:
                # For text messages, use AI response
                try:
                    # Check for direct replies first
                    direct_reply = hybrid_bot.get_direct_reply(message.text)
                    if direct_reply:
                        response_text = direct_reply
                    else:
                        # Use AI for all other text messages
                        response_text = await hybrid_bot.get_ai_reply(message.text)

                    # Handle language translation
                    chat_lang = await get_chat_language(chat_id)
                    if chat_lang and chat_lang != "nolang":
                        try:
                            translated_text = GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                            if translated_text:
                                response_text = translated_text
                        except:
                            pass

                    # Send AI-generated text response with emoji
                    emoji = random.choice(hybrid_bot.EMOJIS)
                    final_text = f"{response_text} {emoji}"
                    await message.reply_text(final_text)
                    
                except Exception as e:
                    print(f"Error in AI text response: {e}")
                    try:
                        fallback_reply = await hybrid_bot.get_ai_reply("Hello")
                        emoji = random.choice(hybrid_bot.EMOJIS)
                        await message.reply_text(f"{fallback_reply} {emoji}")
                    except:
                        await message.reply_text("🙄")

        # Save user replies for learning
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        await message.reply_text("🙄")
    except Exception as e:
        print(f"Error in hybrid_chatbot_response: {e}")
        return
