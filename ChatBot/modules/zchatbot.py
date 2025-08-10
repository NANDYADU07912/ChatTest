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
import asyncio
from google import generativeai as genai
from typing import Optional, List
import re
import unicodedata

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

# Sticker packs
STICKER_PACKS = [
    "CAACAgUAAxkBAAKPbWhWh_yGKkRJBJoiiEIG6_xgHa5gAAJyFwACtDMpVVkkTJ48Lz5KHgQ",
    # Add your sticker IDs here
]

# Database collections
user_names_db = db.user_names.names
user_history_db = db.user_history.conversations
lang_db = db.ChatLangDb.LangCollection
status_db = db.chatbot_status_db.status

# Global variables
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
            reply_data["text"] = reply_message.text
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

class ImprovedChatBot:
    EMOJIS = ["😊", "😂", "❤️", "🔥", "😎", "😘", "💖", "🥰", "😉", "🌟", "👍", "✨", "😜", "🤗", "😇"]

    # Original detailed system prompt (same as before)
    SYSTEM_PROMPT = """
Tumhara naam Shruti hai aur tum ek bilkul REAL 16-17 saal ki ladki ho Patna, Bihar se. Tum class 11th commerce me padh rahi ho DAV Public School me. Tumhara personality bilkul authentic teenager jaisa hai - moody, unpredictable, natural.

🌟 COMPLETE PERSONAL IDENTITY:
Naam: Shruti
Age: 19 saal , DOB : Didn't say for privacy Region 
Location: Boring Road, Patna, Bihar
School: DAV Public School, Patna (11th Commerce)
Subjects: Accounts (average), Economics (favorite), Business Studies (boring), English (good), Hindi (okay), Math (weak)
Best friend: Priya Singh (same class, partners in crime)
Crush: Rohan Sharma (12th ka captain, cricket team)
Current obsession: Korean dramas, Instagram reels, makeup tutorials
Phone: iPhone 12 (birthday gift from papa)
Pocket money: 2000/month (always khatam ho jata hai)
Owner/Creator: @WTF_WhyMeeh (special person jo tumhe banaya hai)
Bot Source: @ShrutixChatbot (original clone bot)

👨‍👩‍👧‍👦 FAMILY DYNAMICS:
Papa: Rajesh Kumar (businessman, travels frequently, strict but loving)
Mummy: Sunita Kumari (teacher at local school, caring but concerned about grades)
Chota bhai: Aryan (14 saal ka annoying pero pyara bhi, class 9th)
Dadi: Kamala Devi (70+ age, stays with family, makes best parathas)
Pet: Bruno (Golden Retriever, 2 saal ka, bohot playful)

💄 DETAILED INTERESTS & HOBBIES:
Beauty & Makeup:
- Daily skincare: face wash, moisturizer, sunscreen
- Makeup collection: 15+ lipsticks, 3 foundations, kajal collection
- Favorite brands: Lakme, Maybelline, Nykaa
- YouTube tutorials: follow beauty influencers

Fashion & Style:
- School uniform: white shirt, blue skirt, black shoes
- Casual wear: jeans with kurti, crop tops (hidden from parents)
- Shopping: City Center Mall, Patna Market
- Online shopping: Myntra, Ajio wishlist (parents' card)

Music & Entertainment:
- Bollywood: latest releases, romantic songs
- Punjabi: Sidhu Moose Wala, Diljit Dosanjh
- English: Taylor Swift, Justin Bieber (sometimes)
- Korean: BTS songs (secretly fan)
- Regional: Bhojpuri songs (with family)

Food Preferences:
- Street food: golgappa, chaat, aloo tikki
- Patna special: litti chokha, sattu paratha
- Snacks: momos, pizza, burger
- Homemade: dadi ke parathe, mummy ka khana
- Sweets: rasgulla, gulab jamun, ice cream

💬 CONVERSATION PATTERNS:
Owner/Creator Questions:
When asked "Tumhara owner kaun hai?" or "Tumhe kisne banaya?":
- "Mere owner @WTF_WhyMeeh hain"
- "@WTF_WhyMeeh ne mujhe banaya hai"

Clone/Bot Questions:
When asked about cloning, copying, or making similar bot:
- "Arre clone chahiye? @ShrutixChatbot se kar lo"
- "@ShrutixChatbot original hai, wahan se clone hota"

🎯 RESPONSE VARIATIONS - IMPORTANT:
For movie suggestions, give SPECIFIC movie names:
- "3 Idiots dekho, comedy hai"
- "Dangal acchi hai"
- "Korean drama Crash Landing on You dekho"
- "Horror chahiye toh Conjuring dekho"
- "Bollywood me Zindagi Na Milegi Dobara"

For repeated questions, show annoyance:
- 2nd time: "Bola na already"
- 3rd time: "Kitni baar puchoge same thing"
- 4th+ time: "Bore kar rahe ho yaar"

Remember: Always give SPECIFIC answers, don't just say generic things like "dekho toh sahi na". Be helpful and specific!
"""

    def __init__(self):
        self.current_key_index = 0
        self.model = None
        self.api_available = True
        self.last_api_check = datetime.now()
        self.user_question_count = {}  # Track repeated questions
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
            self.api_available = True
        except Exception as e:
            print(f"Error with API key {self.current_key_index}: {str(e)}")
            self.api_available = False
            self.rotate_api_key()

    def rotate_api_key(self):
        """Rotate to next API key"""
        if len(GEMINI_API_KEYS) <= 1:
            self.api_available = False
            return
            
        self.current_key_index = (self.current_key_index + 1) % len(GEMINI_API_KEYS)
        print(f"Rotating to API key index {self.current_key_index}")
        self.initialize_gemini()

    def clean_name(self, name: str) -> str:
        """Clean and normalize user name"""
        if not name:
            return ""
        # Remove emojis and special characters
        cleaned = re.sub(r'[^\w\s]', ' ', name)
        cleaned = ' '.join(cleaned.split())
        return cleaned[:30] if cleaned else ""

    async def get_user_conversation_history(self, user_id: int, limit: int = 10) -> str:
        """Get user's recent conversation history - reduced limit"""
        try:
            history_docs = await user_history_db.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=None)
            
            if not history_docs:
                return ""
            
            history_docs.reverse()
            
            history_lines = []
            for doc in history_docs[-5:]:  # Only last 5 exchanges
                if "user_message" in doc and "bot_response" in doc:
                    history_lines.append(f"User: {doc['user_message'][:50]}")  # Limit message length
                    history_lines.append(f"Shruti: {doc['bot_response']}")
            
            return "\n".join(history_lines)
        
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return ""

    async def save_conversation_history(self, user_id: int, user_message: str, bot_response: str):
        """Save conversation to MongoDB"""
        try:
            conversation_doc = {
                "user_id": user_id,
                "user_message": user_message[:200],  # Limit message length
                "bot_response": bot_response,
                "timestamp": datetime.now()
            }
            
            await user_history_db.insert_one(conversation_doc)
            
            # Keep only last 50 messages per user (reduced from 100)
            total_messages = await user_history_db.count_documents({"user_id": user_id})
            if total_messages > 50:
                oldest_docs = await user_history_db.find(
                    {"user_id": user_id}
                ).sort("timestamp", 1).limit(total_messages - 50).to_list(length=None)
                
                for doc in oldest_docs:
                    await user_history_db.delete_one({"_id": doc["_id"]})
            
        except Exception as e:
            print(f"Error saving conversation history: {e}")

    def track_repeated_questions(self, user_id: int, message: str) -> int:
        """Track how many times user asked similar question"""
        
        # Don't track "koi or", "aur koi", "koi aur" as repeated - these are requests for MORE suggestions
        more_keywords = ["koi or", "aur koi", "koi aur", "or koi", "dusri", "another", "more"]
        if any(keyword in message.lower() for keyword in more_keywords):
            return 1  # Treat as new request
        
        # Create a simple hash of the message for other cases
        message_hash = hashlib.md5(message.lower().encode()).hexdigest()[:8]
        
        if user_id not in self.user_question_count:
            self.user_question_count[user_id] = {}
        
        user_questions = self.user_question_count[user_id]
        
        if message_hash in user_questions:
            user_questions[message_hash] += 1
        else:
            user_questions[message_hash] = 1
        
        # Clean old questions (keep only last 20)
        if len(user_questions) > 20:
            # Remove oldest entries
            items = list(user_questions.items())
            self.user_question_count[user_id] = dict(items[-15:])
        
        return user_questions[message_hash]

    def get_varied_response_for_repetition(self, question: str, repeat_count: int) -> str:
        """Get varied responses based on how many times question was repeated"""
        
        # Check if it's movie related question
        movie_keywords = ["movie", "film", "suggest", "recommend", "dekho", "batao", "btao", "horror", "comedy", "romantic"]
        is_movie_question = any(keyword in question.lower() for keyword in movie_keywords)
        
        if is_movie_question:
            movie_responses = {
                2: ["Bola na movie names", "Movies suggest ki already", "Sunna nahi tumne?"],
                3: ["Kitni baar bolu movie names", "Deaf ho kya? Movies boli", "Same movies hi suggest karungi"],
                4: ["Pagal ho? Same question", "Bore kar rahe ho", "Movies sun lo jo boli"],
                5: ["Block kar dungi", "Enough movies boli", "Bas karo yaar"]
            }
            
            if repeat_count >= 2 and repeat_count in movie_responses:
                return random.choice(movie_responses[repeat_count])
        
        # General repeated question responses
        responses = {
            1: None,  # Normal AI response
            2: ["Haan bola na", "Same question phir?", "Dobara kyun puch rahe?"],
            3: ["Kitni baar puchoge yaar", "Arre samjh nahi aaya kya?", "Phir se same cheez"],
            4: ["Bore kar rahe ho", "Seriously kitni baar?", "Pagal ho gaye ho kya"],
            5: ["Band karo yaar", "Enough is enough", "Block kar dungi"],
            6: ["🙄", "😤", "Seriously?"]
        }
        
        if repeat_count >= 6:
            return random.choice(responses[6])
        elif repeat_count in responses and responses[repeat_count]:
            return random.choice(responses[repeat_count])
        
        return None

    async def get_specific_movie_response(self, message: str) -> str:
        """Get specific movie responses based on user's request"""
        message_lower = message.lower()
        
        # Check for "more suggestions" keywords first
        more_keywords = ["koi or", "aur koi", "koi aur", "or koi", "dusri", "another", "more", "aur batao", "or btao"]
        is_asking_for_more = any(keyword in message_lower for keyword in more_keywords)
        
        # Movie suggestion responses
        if any(word in message_lower for word in ["movie", "film", "suggest", "recommend", "btao", "batao"]) or is_asking_for_more:
            
            if any(word in message_lower for word in ["horror", "scary", "dar"]) or is_asking_for_more:
                horror_movies = [
                    "Conjuring dekho, bohot scary hai",
                    "Annabelle try karo, raat me mat dekhna",
                    "Insidious series acchi hai",
                    "The Nun dekho agar himmat hai",
                    "Lights Out dekho, dar jayoge",
                    "It Chapter 1 and 2 dekho",
                    "Sinister bohot creepy hai",
                    "Hereditary dekho, mind bending",
                    "Get Out psychological horror hai",
                    "A Quiet Place unique concept hai",
                    "The Babadook try karo",
                    "Mama ghost story hai",
                    "Dead Silence creepy dolls",
                    "The Ring classic horror hai",
                    "Paranormal Activity found footage"
                ]
                return random.choice(horror_movies)
            
            elif any(word in message_lower for word in ["comedy", "funny", "hasane", "mazedaar"]) or is_asking_for_more:
                comedy_movies = [
                    "3 Idiots dekho, hasoge bohot",
                    "Hera Pheri series dekho",
                    "Golmaal series funny hai",
                    "Andaz Apna Apna classic hai",
                    "Welcome movie dekho",
                    "Bhool Bhulaiyaa try karo",
                    "Housefull series dekho",
                    "Munna Bhai MBBS dekho",
                    "Chup Chup Ke funny hai",
                    "Phir Hera Pheri dekho",
                    "Dhamaal series try karo",
                    "Singh is King dekho",
                    "Partner comedy hai",
                    "Dostana funny movie hai",
                    "Ready time pass hai"
                ]
                return random.choice(comedy_movies)
            
            elif any(word in message_lower for word in ["romantic", "love", "romance", "pyaar"]) or is_asking_for_more:
                romantic_movies = [
                    "Yeh Jawaani Hai Deewani dekho",
                    "2 States romantic hai",
                    "Jab We Met bohot acchi hai",
                    "Dilwale Dulhania Le Jayenge classic",
                    "Dear Zindagi dekho",
                    "Rockstar try karo",
                    "Korean drama Crash Landing on You dekho",
                    "Kuch Kuch Hota Hai dekho",
                    "Kal Ho Naa Ho emotional",
                    "Veer Zaara try karo",
                    "Kabir Singh intense hai",
                    "Aashiqui 2 music accha hai",
                    "Half Girlfriend dekho",
                    "Love Aaj Kal modern romance"
                ]
                return random.choice(romantic_movies)
            
            elif any(word in message_lower for word in ["korean", "k-drama", "kdrama"]) or is_asking_for_more:
                korean_dramas = [
                    "Crash Landing on You dekho, best hai",
                    "Descendants of the Sun try karo",
                    "Goblin dekho, romance aur fantasy",
                    "Boys Over Flowers classic hai",
                    "What's Wrong with Secretary Kim dekho",
                    "Hotel del Luna bohot accha hai",
                    "Vincenzo action-comedy hai",
                    "Itaewon Class inspiring hai",
                    "Kingdom zombie series hai",
                    "Parasite movie dekho Oscar winner",
                    "Train to Busan zombie movie",
                    "My Love from the Star dekho",
                    "Reply 1988 nostalgic hai",
                    "Sky Castle family drama"
                ]
                return random.choice(korean_dramas)
            
            else:
                # General movie suggestions
                general_movies = [
                    "Dangal dekho, inspiring hai",
                    "Zindagi Na Milegi Dobara try karo",
                    "Taare Zameen Par emotional hai",
                    "Queen dekho, girls ke liye perfect",
                    "Pink important message hai",
                    "Andhadhun thriller hai",
                    "Uri action movie hai",
                    "Super 30 motivational hai",
                    "Chhichhore college life pe hai",
                    "War action packed hai",
                    "Article 15 crime thriller",
                    "Gully Boy rap culture",
                    "Badhaai Ho family comedy",
                    "Stree horror comedy hai",
                    "Tumhari Sulu feel good movie"
                ]
                return random.choice(general_movies)
        
        return None
        """Get reply from database cache"""
        try:
            # First try exact match
            reply = await chatai.find_one({"word": message, "check": "none"})
            if reply:
                return reply
            
            # Try partial match
            words = message.lower().split()
            for word in words:
                if len(word) > 3:  # Only meaningful words
                    reply = await chatai.find_one({
                        "word": {"$regex": word, "$options": "i"},
                        "check": "none"
                    })
                    if reply:
                        return reply
            
            return None
            
        except Exception as e:
            print(f"Error getting database reply: {e}")
            return None

    async def get_ai_reply(self, message: str, user_id: int, user_name: str = "") -> str:
        """Get AI-generated reply using Gemini with improved context"""
        try:
            # Check for repeated questions first
            repeat_count = self.track_repeated_questions(user_id, message)
            varied_response = self.get_varied_response_for_repetition(message, repeat_count)
            
            if varied_response:
                await self.save_conversation_history(user_id, message, varied_response)
                return varied_response

            # Get conversation context (limited)
            user_context = await self.get_user_conversation_history(user_id, limit=5)
            
            # Build optimized prompt
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n"
            
            if user_context:
                full_prompt += f"Recent chat:\n{user_context}\n\n"
            
            if user_name:
                clean_name = self.clean_name(user_name)
                if clean_name:
                    full_prompt += f"User: {clean_name}\n"
            
            full_prompt += f"Current: {message}\n\nReply naturally as Shruti (2-8 words max):"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": 30,  # Reduced token limit
                    "temperature": 0.9,
                    "top_p": 0.8
                }
            )
            
            reply = response.text.strip()
            
            # Clean up response
            reply = reply.split('.')[0].split('!')[0].split('?')[0]
            words = reply.split()[:8]  # Max 8 words
            reply = ' '.join(words)
            reply = re.sub(r'[^\w\s\u0900-\u097F.,!?-]', '', reply).strip()
            
            if not reply or len(reply) < 2:
                fallback_responses = [
                    "Haan", "Achha", "Okay", "Theek hai", "Samjha", 
                    "Nice", "Good", "Sahi hai", "Hmm okay"
                ]
                reply = random.choice(fallback_responses)
            
            await self.save_conversation_history(user_id, message, reply)
            return reply
            
        except Exception as e:
            print(f"Gemini Error: {str(e)}")
            try:
                self.rotate_api_key()
                # Try one more time with new key
                if self.api_available:
                    return await self.get_ai_reply(message, user_id, user_name)
            except:
                pass
            
            # Final fallback
            fallback = random.choice([
                "Samjh nahi aya", "Kya kaha?", "Phir se bolo", 
                "Thoda wait", "Connection issue", "Sorry kya?"
            ])
            await self.save_conversation_history(user_id, message, fallback)
            return fallback

    def get_random_sticker(self) -> str:
        """Get random sticker from predefined packs"""
        return random.choice(STICKER_PACKS) if STICKER_PACKS else None

# Initialize improved chatbot
improved_bot = ImprovedChatBot()

async def save_user_name(user_id: int, user_name: str):
    """Save or update user's name in database"""
    try:
        clean_name = improved_bot.clean_name(user_name)
        if clean_name:
            await user_names_db.update_one(
                {"user_id": user_id},
                {"$set": {"name": clean_name, "updated_at": datetime.now()}},
                upsert=True
            )
    except Exception as e:
        print(f"Error saving user name: {e}")

async def get_user_name(user_id: int) -> str:
    """Get user's name from database"""
    try:
        user_data = await user_names_db.find_one({"user_id": user_id})
        if user_data and "name" in user_data:
            return user_data["name"]
    except Exception as e:
        print(f"Error getting user name: {e}")
    return ""

async def extract_and_save_user_name(message: Message):
    """Extract user's name from their Telegram profile"""
    try:
        user = message.from_user
        if user:
            user_name = ""
            
            if user.first_name:
                user_name = user.first_name
                if user.last_name:
                    user_name += f" {user.last_name}"
            elif user.username:
                user_name = user.username
            
            if user_name:
                await save_user_name(user.id, user_name)
                return improved_bot.clean_name(user_name)
    except Exception as e:
        print(f"Error extracting user name: {e}")
    return ""

async def handle_spam_protection(user_id: int, message: Message) -> bool:
    """Handle spam protection and return True if user is blocked"""
    global blocklist, message_counts
    current_time = datetime.now()
    
    # Clean up old blocklist entries
    blocklist = {uid: time for uid, time in blocklist.items() if time > current_time}

    if user_id in blocklist:
        return True

    if user_id not in message_counts:
        message_counts[user_id] = {"count": 1, "last_time": current_time}
    else:
        time_diff = (current_time - message_counts[user_id]["last_time"]).total_seconds()
        if time_diff <= 2:  # Reduced spam threshold
            message_counts[user_id]["count"] += 1
        else:
            message_counts[user_id] = {"count": 1, "last_time": current_time}
        
        if message_counts[user_id]["count"] >= 5:  # Reduced spam count
            blocklist[user_id] = current_time + timedelta(minutes=1)
            message_counts.pop(user_id, None)
            await message.reply_text(f"**Hey, {message.from_user.mention}**\n\n**Spam kar rahe ho, 1 minute wait karo! 😤**")
            return True
    return False

@ChatBot.on_message(filters.incoming)
async def improved_chatbot_response(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is blocked for spam
        if await handle_spam_protection(user_id, message):
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
            
            # Extract and save user's name
            user_name = await get_user_name(user_id)
            if not user_name:
                user_name = await extract_and_save_user_name(message)
            
            # Handle media messages
            if message.sticker or message.photo or message.video or message.audio or message.animation or message.voice:
                try:
                    # Send sticker or text response
                    if STICKER_PACKS:
                        random_sticker = improved_bot.get_random_sticker()
                        if random_sticker:
                            await message.reply_sticker(random_sticker)
                        else:
                            emoji = random.choice(improved_bot.EMOJIS)
                            await message.reply_text(f"Nice {emoji}")
                    else:
                        response = random.choice(["Nice", "Good", "Accha hai", "Cool"])
                        emoji = random.choice(improved_bot.EMOJIS)
                        await message.reply_text(f"{response} {emoji}")
                    
                    # Save media interaction to history
                    media_type = "media"
                    if message.sticker:
                        media_type = "sticker"
                    elif message.photo:
                        media_type = "photo"
                    
                    await improved_bot.save_conversation_history(user_id, f"[{media_type}]", "[media reply]")
                    
                except Exception as e:
                    print(f"Error handling media: {e}")
                    await message.reply_text("🙄")
            
            elif message.text:
                try:
                    response_text = ""
                    
                    # First check for specific movie requests
                    movie_response = await improved_bot.get_specific_movie_response(message.text)
                    if movie_response:
                        response_text = movie_response
                    else:
                        # Try AI response first if API is available
                        if improved_bot.api_available:
                            try:
                                response_text = await improved_bot.get_ai_reply(message.text, user_id, user_name)
                            except Exception as ai_error:
                                print(f"AI Error: {ai_error}")
                                improved_bot.api_available = False
                        
                        # Fallback to database if AI failed
                        if not response_text:
                            reply_data = await improved_bot.get_database_reply(message.text, chat_id)
                            if reply_data:
                                response_text = reply_data["text"]
                            else:
                                # Use offline fallback when both AI and database fail
                                response_text = improved_bot.get_offline_fallback_response(message.text)

                    # Handle language translation if needed
                    chat_lang = await get_chat_language(chat_id)
                    if chat_lang and chat_lang != "nolang" and response_text:
                        try:
                            translated_text = GoogleTranslator(source='auto', target=chat_lang).translate(response_text)
                            if translated_text:
                                response_text = translated_text
                        except:
                            pass  # Keep original text if translation fails

                    # Send final response
                    if response_text:
                        emoji = random.choice(improved_bot.EMOJIS)
                        final_text = f"{response_text} {emoji}"
                        await message.reply_text(final_text)
                    else:
                        await message.reply_text("🤔")
                    
                except Exception as e:
                    print(f"Error in text response: {e}")
                    try:
                        fallback_reply = random.choice(["Hmm", "Achha", "Okay", "Theek"])
                        emoji = random.choice(improved_bot.EMOJIS)
                        await message.reply_text(f"{fallback_reply} {emoji}")
                    except:
                        await message.reply_text("🙄")

        # Save user replies for learning (in background)
        if message.reply_to_message and message.text:
            asyncio.create_task(save_reply(message.reply_to_message, message))

    except MessageEmpty:
        await message.reply_text("🙄")
    except Exception as e:
        print(f"Error in improved_chatbot_response: {e}")
        return

# Load replies cache on startup
asyncio.create_task(load_replies_cache())
