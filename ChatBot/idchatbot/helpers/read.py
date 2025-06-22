from config import OWNER_USERNAME, SUPPORT_GRP
from ChatBot import ChatBot
from pyrogram import Client, filters

# Start Message
START = """
<b>🌟 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ᴀɪ ᴄʜᴀᴛʙᴏᴛ 🌟</b>

ʜɪ! ɪ'ᴍ ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ ᴀɪ ʙᴏᴛ ᴄᴀᴘᴀʙʟᴇ ᴏғ ᴜɴᴅᴇʀsᴛᴀɴᴅɪɴɢ ᴀɴʏ ᴛʏᴘᴇ ᴏғ ᴄᴏɴᴛᴇɴᴛ ⚡

<b>✨ ғᴇᴀᴛᴜʀᴇs:</b>
🎯 ᴀᴜᴛᴏ ʀᴇᴘʟʏ ᴛᴏ ᴛᴇxᴛ, ᴠᴏɪᴄᴇ, ᴘʜᴏᴛᴏ, ᴠɪᴅᴇᴏ & sᴛɪᴄᴋᴇʀs  
🌐 ᴍᴜʟᴛɪ-ʟᴀɴɢᴜᴀɢᴇ sᴜᴘᴘᴏʀᴛ → /setlang  
🔘 ᴏɴ/ᴏғғ ᴀɪ ᴍᴏᴅᴇ → /chatbot on | off  

<b>🛠 ᴄʟᴏɴᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ ғʀᴏᴍ:</b> @ShrutiClone
"""

# Help Message
HELP_READ = """
<b>🆘 ʜᴇʟᴘ ᴍᴇɴᴜ</b>

🔹 <b>/chatbot [on/off]</b> – ᴛᴜʀɴ ᴀɪ ʀᴇᴘʟʏ ᴏɴ ᴏʀ ᴏғғ  
🔹 <b>/setlang</b> – sᴇᴛ ʙᴏᴛ ʟᴀɴɢᴜᴀɢᴇ  
🔹 <b>/resetlang</b> – ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛ  
🔹 <b>/chatlang</b> – sʜᴏᴡ ᴄᴜʀʀᴇɴᴛ ʟᴀɴɢᴜᴀɢᴇ  
🔹 <b>/status</b> – ᴄʜᴇᴄᴋ ʙᴏᴛ ᴀɪ sᴛᴀᴛᴜs  
🔹 <b>/id</b> – ɢᴇᴛ ᴜsᴇʀ/ᴄʜᴀᴛ/message ɪᴅ  
🔹 <b>/ping</b> – ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ
"""

# Tools Message
TOOLS_DATA_READ = """
<b>🧰 ᴜsᴇғᴜʟ ᴛᴏᴏʟs</b>

💠 <b>/start</b> – ʀᴇsᴛᴀʀᴛ ʙᴏᴛ  
💠 <b>/help</b> – ɢᴇᴛ ᴛʜɪs ʜᴇʟᴘ ᴍᴇɴᴜ  
💠 <b>/id</b> – sʜᴏᴡ ɪᴅs  
💠 <b>/ping</b> – ʙᴏᴛ ᴘɪɴɢ  
💠 <b>.broadcast</b> – sᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
💠 <b>/shayri</b> – ʀᴀɴᴅᴏᴍ ʟᴏᴠᴇ sʜᴀʏʀɪ
"""

# Chatbot Commands
CHATBOT_READ = """
<b>🤖 ᴀɪ ᴄʜᴀᴛʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs</b>

🔸 <b>/chatbot on | off</b> – ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ᴀɪ ʀᴇᴘʟʏ  
🔸 <b>/setlang</b> – ᴄʜᴏᴏsᴇ ʏᴏᴜʀ ʟᴀɴɢᴜᴀɢᴇ  
🔸 <b>/resetlang</b> – ʀᴇsᴇᴛ ʟᴀɴɢᴜᴀɢᴇ  
🔸 <b>/chatlang</b> – ᴄᴜʀʀᴇɴᴛ ʟᴀɴɢᴜᴀɢᴇ  
🔸 <b>/status</b> – ᴀɪ ᴄʜᴀᴛʙᴏᴛ sᴛᴀᴛᴜs  
🔸 <b>/stats</b> – ʙᴏᴛ ᴜsᴀɢᴇ sᴛᴀᴛs  
🔸 <b>.idclone</b> – ɢᴇɴᴇʀᴀᴛᴇ ɪᴅ ғʀᴏᴍ sᴛʀɪɴɢ
"""

# Source Message
SOURCE_READ = f"""
<b>💡 ᴘᴏᴡᴇʀᴇᴅ ʙʏ sʜʀᴜᴛɪ ᴀɪ ᴇɴɢɪɴᴇ</b>

ᴅᴇsɪɢɴᴇᴅ ғᴏʀ sᴜᴘᴇʀғᴀsᴛ, ᴍᴜʟᴛɪ-ʟᴀɴɢᴜᴀʟ ʀᴇᴘʟɪᴇs ᴀɴᴅ ᴀɪ sᴇɴsᴇ sᴜᴘᴘᴏʀᴛ 💬

👑 ᴏᴡɴᴇʀ: <a href="https://t.me/{OWNER_USERNAME}">{OWNER_USERNAME}</a>  
📢 sᴜᴘᴘᴏʀᴛ: <a href="https://t.me/{SUPPORT_GRP}">ᴄʟɪᴄᴋ ʜᴇʀᴇ</a>
"""
