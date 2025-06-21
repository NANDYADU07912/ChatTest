import random
import datetime
import hashlib
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.errors import MessageEmpty
from pyrogram.enums import ChatAction, ChatMemberStatus as CMS
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from deep_translator import GoogleTranslator
from ChatBot.database.chats import add_served_chat
from ChatBot.database.users import add_served_user
from ChatBot.database import add_served_cchat, add_served_cuser
from config import MONGO_URL
from ChatBot import ChatBot, mongo, LOGGER, db
from ChatBot.mplugin.helpers import chatai, languages
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
        "Owner ke baare me puchhne par @WTF_WhyMeeh ka mention karti ho. "
        "Tum khud ko kabhi bot nahi manti, hamesha insaan hi kehti ho kyunki tum real ho. "
        "Replies me sirf ek sentence hota hai, do nahi. Very short and natural."
    )

    def __init__(self):
        self.current_key_index = 0
        self.model = None
        self.replies_cache = []
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

    def get_user_id(self, telegram_user_id: int, group_id: int = None) -> str:
        """Generate unique user ID"""
        if group_id:
            combined = f"{telegram_user_id}_{group_id}"
        else:
            combined = str(telegram_user_id)
        return hashlib.md5(combined.encode()).hexdigest()

    def get_age(self) -> str:
        """Calculate current age"""
        birthday = datetime.date(2008, 3, 24)
        today = datetime.date.today()
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        months = (today.year - birthday.year) * 12 + today.month - birthday.month
        months = months % 12
        return f"{age} saal {months} mahine"

    def get_direct_reply(self, message: str) -> str:
        """Direct human-like replies for common questions"""
        message_lower = message.lower()
        
        # Common greetings
        if any(word in message_lower for word in ['hi', 'hello', 'hey', 'namaste', 'hii']):
            return random.choice(["Hi", "Hello", "Hey", "Namaste", "Hii"])
            
        # Food related
        if 'khana' in message_lower and 'khaya' in message_lower:
            return random.choice(["Haan khaya", "Nahi abhi", "Khaya tha", "Abhi nahi"])
            
        # Location
        if any(word in message_lower for word in ['kaha', 'kahan', 'where']):
            return random.choice(["Ghar pe", "Patna me", "College me", "Bahar hun"])
            
        # What doing
        if any(word in message_lower for word in ['kya kar', 'what doing', 'kya kr']):
            return random.choice(["Padh rahi", "So rahi thi", "Kuch nahi", "Time pass"])
            
        # How are you
        if any(word in message_lower for word in ['kaise ho', 'kaisi ho', 'how are']):
            return random.choice(["Bas theek", "Acchi hun", "Mast hun", "Thik hun"])
            
        # Name
        if any(word in message_lower for word in ['naam', 'name']):
            return "Siya"
            
        # Age
        if any(word in message_lower for word in ['umar', 'age', 'kitni']):
            return f"{self.get_age()} ki hun"
            
        # Good night/morning
        if any(word in message_lower for word in ['good night', 'gn', 'sona', 'bye']):
            return random.choice(["Good night", "Bye", "Sona hai?", "Chalo bye"])
            
        if any(word in message_lower for word in ['good morning', 'gm']):
            return random.choice(["Good morning", "GM", "Uth gaye?"])
            
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

# Initialize hybrid chatbot
hybrid_bot = HybridChatBot()

# Database setup
translator = GoogleTranslator()
lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status
replies_cache = []

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
            reply_data["text"] = reply_message.text
            reply_data["check"] = "none"

        is_chat = await chatai.find_one(reply_data)
        if not is_chat:
            await chatai.insert_one(reply_data)
            replies_cache.append(reply_data)

    except Exception as e:
        print(f"Error in save_reply: {e}")

async def get_database_reply(word: str):
    global replies_cache
    if not replies_cache:
        await load_replies_cache()
        
    # First try exact match
    exact_matches = [reply for reply in replies_cache if reply['word'] == word]
    if exact_matches:
        return random.choice(exact_matches)
    
    # Then try partial match
    partial_matches = [reply for reply in replies_cache if word.lower() in reply['word'].lower()]
    if partial_matches:
        return random.choice(partial_matches)
        
    return None

async def get_chat_language(chat_id, bot_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id, "bot_id": bot_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

@Client.on_message(filters.incoming)
async def hybrid_chatbot_response(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        bot_id = client.me.id
        chat_status = await status_db.find_one({"chat_id": chat_id, "bot_id": bot_id})
        
        if chat_status and chat_status.get("status") == "disabled":
            return

        # Skip commands
        if message.text and any(message.text.startswith(prefix) for prefix in ["!", "/", ".", "?", "@", "#"]):
            if message.chat.type in ["group", "supergroup"]:
                await add_served_cchat(bot_id, message.chat.id)
                return await add_served_chat(message.chat.id)      
            else:
                await add_served_cuser(bot_id, message.chat.id)
                return await add_served_user(message.chat.id)

        # Process only if replying to bot or direct message
        if ((message.reply_to_message and message.reply_to_message.from_user.id == client.me.id) or 
            not message.reply_to_message) and not message.from_user.is_bot:
            
            response_text = None
            media_response = None
            
            # Step 1: Try direct AI replies for common patterns
            direct_reply = hybrid_bot.get_direct_reply(message.text)
            if direct_reply:
                response_text = direct_reply
            else:
                # Step 2: Check database for media responses only
                db_reply = await get_database_reply(message.text)
                if db_reply and db_reply["check"] != "none":
                    # Media response from database (photos, videos, stickers, etc.)
                    media_response = db_reply
                
                # Step 3: For text responses, always use AI
                if not media_response:
                    # Get user context for AI (you can implement this based on your needs)
                    user_context = ""  # Add context retrieval logic here
                    ai_reply = await hybrid_bot.get_ai_reply(message.text, user_context)
                    response_text = ai_reply

            # Handle language translation
            chat_lang = await get_chat_language(chat_id, bot_id)
            if response_text and chat_lang and chat_lang != "nolang":
                try:
                    translated_text = GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                    if translated_text:
                        response_text = translated_text
                except:
                    pass

            # Send response
            if media_response:
                # Send media response
                try:
                    if media_response["check"] == "sticker":
                        await message.reply_sticker(media_response["text"])
                    elif media_response["check"] == "photo":
                        await message.reply_photo(media_response["text"])
                    elif media_response["check"] == "video":
                        await message.reply_video(media_response["text"])
                    elif media_response["check"] == "audio":
                        await message.reply_audio(media_response["text"])
                    elif media_response["check"] == "gif":
                        await message.reply_animation(media_response["text"])
                    elif media_response["check"] == "voice":
                        await message.reply_voice(media_response["text"])
                except:
                    # Fallback to AI text if media fails
                    ai_reply = await hybrid_bot.get_ai_reply(message.text)
                    emoji = random.choice(hybrid_bot.EMOJIS)
                    await message.reply_text(f"{ai_reply} {emoji}")
            elif response_text:
                # Send text response with emoji
                emoji = random.choice(hybrid_bot.EMOJIS)
                final_text = f"{response_text} {emoji}"
                try:
                    await message.reply_text(final_text)
                except:
                    pass
            else:
                # Ultimate fallback
                try:
                    fallback_reply = await hybrid_bot.get_ai_reply(message.text)
                    emoji = random.choice(hybrid_bot.EMOJIS)
                    await message.reply_text(f"{fallback_reply} {emoji}")
                except:
                    await message.reply_text("🙄🙄")

        # Save user replies for learning
        if message.reply_to_message:
            await save_reply(message.reply_to_message, message)

    except MessageEmpty:
        try:
            await message.reply_text("🙄🙄")
        except:
            pass
    except Exception as e:
        print(f"Error in hybrid_chatbot_response: {e}")
        return
