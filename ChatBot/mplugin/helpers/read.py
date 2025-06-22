from config import OWNER_USERNAME, SUPPORT_GRP
from ChatBot import ChatBot
from pyrogram import Client, filters

START = """**
🤖 **ɪ'ᴍ** ᴛʜᴇ **sᴜᴘᴇʀғᴀsᴛ ᴄʜᴀᴛʙᴏᴛ** 🚀

✨ **ғᴇᴀᴛᴜʀᴇs:**
🎯 sᴜᴘᴘᴏʀᴛs ᴛᴇxᴛ, sᴛɪᴄᴋᴇʀ, ᴘʜᴏᴛᴏ, ᴠɪᴅᴇᴏ
🌐 ᴍᴜʟᴛɪ-ʟᴀɴɢᴜᴀɢᴇ sᴜᴘᴘᴏʀᴛ
⚡ ᴄʜᴀᴛʙᴏᴛ ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ
🛠️ ᴍᴀᴋᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʜᴀᴛʙᴏᴛ ғʀᴏᴍ [@Shruticlone](https://t.me/Shruticlone)
👤 ɪᴅ-ᴄʜᴀᴛʙᴏᴛ sᴜᴘᴘᴏʀᴛ

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

HELP_READ = f"""**
📋 **ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ**

❓ **ɪғ ʏᴏᴜ'ʀᴇ ғᴀᴄɪɴɢ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ,** ᴀsᴋ ɪɴ [**sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ**](https://t.me/ShrutiBotSupport)

⚡ **ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ:** **/**

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

TOOLS_DATA_READ = f"""**
🛠️ **ʜᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ᴛᴏᴏʟs:**

🎯 **/start** - ᴡᴀᴋᴇ ᴜᴘ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ʀᴇᴄᴇɪᴠᴇ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ

📋 **/help** - ɢᴇᴛ ᴅᴇᴛᴀɪʟs ᴀʙᴏᴜᴛ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ғᴇᴀᴛᴜʀᴇs

🏓 **/ping** - ᴄʜᴇᴄᴋ ᴛʜᴇ ʀᴇsᴘᴏɴsᴇ ᴛɪᴍᴇ ᴏғ ᴛʜᴇ ʙᴏᴛ

🆔 **/id** - ɢᴇᴛ ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ, ᴄʜᴀᴛ ɪᴅ, ᴀɴᴅ ᴍᴇssᴀɢᴇ ɪᴅ

📢 **/broadcast** - ғᴏʀᴡᴀʀᴅ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴄʜᴀᴛs
**ᴇxᴀᴍᴘʟᴇ:** `/broadcast -user -pin ʜᴇʟʟᴏ ғʀɪᴇɴᴅs`

💕 **/shayri** - ɢᴇᴛ ʀᴀɴᴅᴏᴍ sʜᴀʏʀɪ ғᴏʀ ʏᴏᴜʀ ʟᴏᴠᴇ

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

CHATBOT_READ = f"""**
🤖 **ʜᴇʀᴇ ᴀʀᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅs ғᴏʀ ᴄʜᴀᴛʙᴏᴛ:**

⚡ **/chatbot** - ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ᴛʜᴇ ᴄʜᴀᴛʙᴏᴛ

🌐 **/lang, /language, /setlang** - sᴇʟᴇᴄᴛ ᴄʜᴀᴛ ʟᴀɴɢᴜᴀɢᴇ

🔄 **/resetlang, /nolang** - ʀᴇsᴇᴛ ʟᴀɴɢᴜᴀɢᴇ ᴛᴏ ᴍɪxᴇᴅ

🗣️ **/chatlang** - ɢᴇᴛ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ ʟᴀɴɢᴜᴀɢᴇ

📊 **/status** - ᴄʜᴇᴄᴋ ᴄʜᴀᴛʙᴏᴛ ᴀᴄᴛɪᴠᴇ ᴏʀ ɴᴏᴛ

📈 **/stats** - ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs

🤖 **/clone [ʙᴏᴛ ᴛᴏᴋᴇɴ]** - ᴄʟᴏɴᴇ ʏᴏᴜʀ ʙᴏᴛ

👤 **/idclone [ᴘʏʀᴏɢʀᴀᴍ sᴛʀɪɴɢ sᴇssɪᴏɴ]** - ᴍᴀᴋᴇ ɪᴅ-ᴄʜᴀᴛʙᴏᴛ

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

SOURCE_READ = f"""**
🎉 **ʜᴇʏ, ᴛʜᴇ** [{ChatBot.name}](https://t.me/{ChatBot.username}) **ɪs ɴᴇᴡ ᴘᴏᴡᴇʀғᴜʟ ᴄʜᴀᴛʙᴏᴛ**

💰 **ᴘʟᴇᴀsᴇ ᴅᴏɴᴀᴛᴇ ᴛʜᴇ ᴅᴇᴠᴇʟᴏᴘᴇʀ ᴛᴏ ᴍᴀɪɴᴛᴀɪɴ ᴛʜᴇ ᴘʀᴏᴊᴇᴄᴛs**

🎁 **ʜᴇʀᴇ ɪs ᴛʜᴇ** [**ᴅᴏɴᴀᴛᴇ ʟɪɴᴋ**](https://t.me/creativeydv/3)

🆘 **ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍ ᴄᴏɴᴛᴀᴄᴛ** [**sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ**](https://t.me/{SUPPORT_GRP})

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

ADMIN_READ = f"""**
⚡ **ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ** - **sᴏᴏɴ**

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""

ABOUT_READ = f"""**
🤖 **[{ChatBot.name}](https://t.me/{ChatBot.username}) ɪs ᴀɴ ᴀɪ ʙᴀsᴇᴅ ᴄʜᴀᴛ-ʙᴏᴛ**

💬 **[{ChatBot.name}](https://t.me/{ChatBot.username}) ʀᴇᴘʟɪᴇs ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴛᴏ ᴜsᴇʀs**  

🎯 **ʜᴇʟᴘs ʏᴏᴜ ɪɴ ᴀᴄᴛɪᴠᴀᴛɪɴɢ ʏᴏᴜʀ ɢʀᴏᴜᴘs**

🐍 **ᴡʀɪᴛᴛᴇɴ ɪɴ** [**ᴘʏᴛʜᴏɴ**](https://www.python.org) **ᴡɪᴛʜ** [**ᴍᴏɴɢᴏ-ᴅʙ**](https://www.mongodb.com) **ᴀs ᴅᴀᴛᴀʙᴀsᴇ**

📋 **ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ ғᴏʀ ɢᴇᴛᴛɪɴɢ ʙᴀsɪᴄ ʜᴇʟᴘ ᴀɴᴅ ɪɴғᴏ ᴀʙᴏᴜᴛ** [{ChatBot.name}](https://t.me/{ChatBot.username})

💝 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ** [𝐒ʜʀᴜᴛɪ ʙᴏᴛs](https://t.me/ShrutiBots)
**"""
