#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Media Downloader Bot - النسخة الكاملة والمطورة
بوت احترافي لتحميل الوسائط من 20+ منصة
"""

import logging
import os
import sqlite3
import time
import asyncio
import re
from datetime import datetime
from typing import Dict, Optional
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from telegram.constants import ParseMode

# ==================== الإعدادات الأساسية ====================
BOT_TOKEN = "7370155559:AAF4jH4f7db_8QZYqoay_tWv1-CMXpCNgrY"
ADMIN_ID = 6891530912
DATABASE_NAME = "bot_database.db"
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 ميجابايت

# حالات المحادثة
BROADCAST, BAN, UNBAN = range(3)

# إنشاء مجلد التحميلات
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== النصوص متعددة اللغات ====================
LANG = {
    'ar': {
        # نصوص الترحيب
        'welcome': "❖ <b>أهلاً بك {name}</b> ❖\n\n⚡︎ <b>أقوى بوت تحميل ميديا</b> ⚡︎\n\n➢ يدعم: يوتيوب، تيك توك، انستا، فيسبوك...\n➢ وأكثر من 1000 موقع آخر.\n➢ فقط أرسل الرابط للبدء.\n\n❴ يعمل بقوة yt-dlp ❵",
        'maintenance': "⚠︎ البوت تحت الصيانة حالياً. يرجى المحاولة لاحقاً.",
        'process': "➢ جاري معالجة طلبك ⚡︎...",
        'downloading': "⬇︎ جاري التحميل بأعلى جودة...",
        'uploading': "⬆︎ جاري الرفع إلى تيليجرام...",
        'error_generic': "✕ حدث خطأ: {error}",
        'error_size': "✕ الملف كبير جداً (حد تيليجرام 50 ميجا).",
        'error_unsupported': "✕ الرابط غير مدعوم أو خاص.",
        'send_url': "⚠︎ الرجاء إرسال رابط صالح.",
        'caption': "❖ <b>{title}</b>\n\n➢ تم التحميل بواسطة: @{bot_user}",
        'sites_btn': "⟡ المواقع المدعومة ⟡",
        'settings_btn': "⚙️ الإعدادات",
        'back_btn': "🔙 رجوع",
        'select_lang': "❖ اختر لغتك المفضلة",
        'lang_set': "✅ تم تعيين اللغة العربية",
        
        # نصوص المساعدة الكاملة
        'help_title': "💠┇طرق التحميل من اليوتيوب:\n🏷┇من خلال أرسال لي رابط الأغنية من اليوتيوب،\n🖇┇أو أرسال لي أسم الأغنية للبحث عنها في اليوتيوب.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من الانستكرام:\n🏷┇قم بأرسال لي رابط الفيديو أو الصورة في الانستكرام،\n🖇┇أو يمكنك تحميل ستوريات أي شخص فقط عبر أرسال لي اليوزر الخاص به.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من الفيسبوك:\n🏷┇يمكنك تحميل مقاطع الفيديو العامة من موقع الفيسبوك،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من بينترست:\n🏷┇يمكنك تحميل مقاطع الفيديو العامة من موقع بينترست،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n🖇┇يمكنك تحميل الصور بحث الاسم صوره\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من لايكي:\n🏷┇يمكنك تحميل مقاطع الفيديو العامة من موقع لايكي،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من التويتر:\n🏷┇يمكنك تحميل مقاطع الفيديو العامة من موقع تويتر،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من التيك توك:\n🏷┇يمكنك تحميل مقاطع الفيديو العامة من موقع التيك توك،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من السناب جات:\n🏷┇يمكنك تحميل الستوريات العامة من موقع سناب جات،\n🖇┇عن طريق أرسال رابط الحساب فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من تيليجرام:\n🏷┇يمكنك تحميل الستوريات العامة من موقع تيليجرام،\n🖇┇عن طريق أرسال رابط الستوري فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من ساوند كلاود:\n🏷┇يمكنك تحميل الأغاني العامة من موقع ساوند كلاود،\n🖇┇عن طريق أرسال رابط الأغنية فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من ديلي موشن:\n🏷┇يمكنك تحميل الفيديوات العامة من موقع ديلي موشن،\n🖇┇عن طريق أرسال رابط الفيديو فقط.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠┇طرق التحميل من فيميو:\n🏷┇يمكنك تحميل الفيديوات العامة من موقع فيميو،\n🖇┇عن طريق أرسال رابط الفيديو فقط.",
        
        'make_bot': "🔨 <b>لصنع بوت مشابه</b>\n\nيمكنك التواصل مع المطور:\n@avetaar\nأو زيارة قناة المصدر:\nhttps://t.me/+rawFtlErSFRlZjhk",
        
        # نصوص لوحة التحكم
        'admin_panel': "♛ <b>لوحة التحكم</b> ♛\n\n👥 إجمالي المستخدمين: <code>{total}</code>\n⚙️ حالة البوت: {status}\n📡 البنج: <code>{ping}ms</code>",
        'status_online': "🟢 يعمل",
        'status_maintenance': "🔴 صيانة",
        'broadcast_start': "➢ أرسل الرسالة (نص / صورة / فيديو) للنشر العام:",
        'broadcast_progress': "➢ جاري النشر...",
        'broadcast_done': "✅ تم النشر\n🟢 نجح: {success}\n🔴 فشل: {failed}",
        'ban_prompt': "➢ أرسل معرف المستخدم للحظر:",
        'unban_prompt': "➢ أرسل معرف المستخدم لإلغاء الحظر:",
        'user_banned': "🚫 تم حظر المستخدم {uid}.",
        'user_unbanned': "✅ تم إلغاء حظر المستخدم {uid}.",
        'user_not_banned': "⚠️ المستخدم ليس في قائمة المحظورين.",
        'invalid_id': "⚠️ الرجاء إرسال رقم صالح.",
        'maintenance_on': "🔒 تم تفعيل وضع الصيانة.",
        'maintenance_off': "🔓 تم إلغاء وضع الصيانة.",
        'access_denied': "⛔ غير مصرح لك.",
    },
    
    'en': {
        'welcome': "❖ 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 <b>{name}</b> ❖\n\n⚡︎ 𝐅𝐚𝐬𝐭𝐞𝐬𝐭 𝐌𝐞𝐝𝐢𝐚 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐫 ⚡︎\n\n➢ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭𝐬: 𝐘𝐨𝐮𝐓𝐮𝐛𝐞, 𝐓𝐢𝐤𝐓𝐨𝐤, 𝐈𝐆, 𝐅𝐁...\n➢ 𝐀𝐧𝐝 𝟏𝟎𝟎𝟎+ 𝐨𝐭𝐡𝐞𝐫 𝐬𝐢𝐭𝐞𝐬.\n➢ 𝐉𝐮𝐬𝐭 𝐬𝐞𝐧𝐝 𝐭𝐡𝐞 𝐔𝐑𝐋 𝐭𝐨 𝐬𝐭𝐚𝐫𝐭.\n\n❴ 𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲 𝐲𝐭-𝐝𝐥𝐩 ❵",
        'maintenance': "⚠︎ 𝐓𝐡𝐞 𝐁𝐨𝐭 𝐢𝐬 𝐮𝐧𝐝𝐞𝐫 𝐦𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞 𝐧𝐨𝐰.",
        'process': "➢ 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 𝐘𝐨𝐮𝐫 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 ⚡︎...",
        'downloading': "⬇︎ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐟𝐫𝐨𝐦 𝐒𝐞𝐫𝐯𝐞𝐫...",
        'uploading': "⬆︎ 𝐔𝐩𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐭𝐨 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦...",
        'error_generic': "✕ 𝐄𝐫𝐫𝐨𝐫: {error}",
        'error_size': "✕ 𝐅𝐢𝐥𝐞 𝐢𝐬 𝐭𝐨𝐨 𝐥𝐚𝐫𝐠𝐞 𝐟𝐨𝐫 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦 (𝐋𝐢𝐦𝐢𝐭 𝟓𝟎𝐌𝐁).",
        'error_unsupported': "✕ 𝐋𝐢𝐧𝐤 𝐧𝐨𝐭 𝐬𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝 𝐨𝐫 𝐩𝐫𝐢𝐯𝐚𝐭𝐞.",
        'send_url': "⚠︎ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐚 𝐯𝐚𝐥𝐢𝐝 𝐔𝐑𝐋.",
        'caption': "❖ <b>{title}</b>\n\n➢ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐝 𝐛𝐲: @{bot_user}",
        'sites_btn': "⟡ 𝐒𝐮𝐩𝐩𝐨𝐫𝐭𝐞𝐝 𝐒𝐢𝐭𝐞𝐬 ⟡",
        'settings_btn': "⚙️ 𝐒𝐞𝐭𝐭𝐢𝐧𝐠𝐬",
        'back_btn': "🔙 𝐁𝐚𝐜𝐤",
        'select_lang': "❖ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐒𝐞𝐥𝐞𝐜𝐭 𝐘𝐨𝐮𝐫 𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞",
        'lang_set': "✅ 𝐋𝐚𝐧𝐠𝐮𝐚𝐠𝐞 𝐬𝐞𝐭 𝐭𝐨 𝐄𝐧𝐠𝐥𝐢𝐬𝐡",
        'help_title': "💠 How to download from YouTube:\n🏷 Send me the video URL or search by name.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Instagram:\n🏷 Send me the post/reel URL or username for stories.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Facebook:\n🏷 Send me the public video URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Pinterest:\n🏷 Send me the pin URL or search by image.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Likee:\n🏷 Send me the video URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Twitter:\n🏷 Send me the tweet URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from TikTok:\n🏷 Send me the video URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Snapchat:\n🏷 Send me the public profile URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Telegram:\n🏷 Send me the story link.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from SoundCloud:\n🏷 Send me the track URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Dailymotion:\n🏷 Send me the video URL.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 How to download from Vimeo:\n🏷 Send me the video URL.",
        'make_bot': "🔨 <b>To make a similar bot</b>\n\nContact the developer:\n@avetaar\nOr visit the source channel:\nhttps://t.me/+rawFtlErSFRlZjhk",
        'admin_panel': "♛ <b>𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</b> ♛\n\n👥 𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬: <code>{total}</code>\n⚙️ 𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐮𝐬: {status}\n📡 𝐏𝐢𝐧𝐠: <code>{ping}ms</code>",
        'status_online': "🟢 𝐎𝐧𝐥𝐢𝐧𝐞",
        'status_maintenance': "🔴 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞",
        'broadcast_start': "➢ 𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 (𝐓𝐞𝐱𝐭/𝐏𝐡𝐨𝐭𝐨/𝐕𝐢𝐝𝐞𝐨):",
        'broadcast_progress': "➢ 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭𝐢𝐧𝐠...",
        'broadcast_done': "✅ 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞𝐝\n🟢 𝐒𝐮𝐜𝐜𝐞𝐬𝐬: {success}\n🔴 𝐅𝐚𝐢𝐥𝐞𝐝: {failed}",
        'ban_prompt': "➢ 𝐒𝐞𝐧𝐝 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐁𝐚𝐧:",
        'unban_prompt': "➢ 𝐒𝐞𝐧𝐝 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐔𝐧𝐛𝐚𝐧:",
        'user_banned': "🚫 𝐔𝐬𝐞𝐫 {uid} 𝐁𝐚𝐧𝐧𝐞𝐝.",
        'user_unbanned': "✅ 𝐔𝐬𝐞𝐫 {uid} 𝐔𝐧𝐛𝐚𝐧𝐧𝐞𝐝.",
        'user_not_banned': "⚠️ 𝐔𝐬𝐞𝐫 𝐧𝐨𝐭 𝐢𝐧 𝐛𝐚𝐧 𝐥𝐢𝐬𝐭.",
        'invalid_id': "⚠️ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐬𝐞𝐧𝐝 𝐚 𝐯𝐚𝐥𝐢𝐝 𝐧𝐮𝐦𝐛𝐞𝐫.",
        'maintenance_on': "🔒 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞 𝐦𝐨𝐝𝐞 𝐞𝐧𝐚𝐛𝐥𝐞𝐝.",
        'maintenance_off': "🔓 𝐌𝐚𝐢𝐧𝐭𝐞𝐧𝐚𝐧𝐜𝐞 𝐦𝐨𝐝𝐞 𝐝𝐢𝐬𝐚𝐛𝐥𝐞𝐝.",
        'access_denied': "⛔ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐃𝐞𝐧𝐢𝐞𝐝.",
    },
    
    'fa': {
        'welcome': "❖ <b>خوش آمدید {name}</b> ❖\n\n⚡︎ <b>سریع‌ترین ربات دانلود مدیا</b> ⚡︎\n\n➢ پشتیبانی: یوتیوب، تیک تاک، اینستا، فیسبوک...\n➢ و بیش از ۱۰۰۰ سایت دیگر.\n➢ فقط لینک را ارسال کنید.\n\n❴ قدرت گرفته از yt-dlp ❵",
        'maintenance': "⚠︎ ربات در حال تعمیرات است.",
        'process': "➢ در حال پردازش درخواست شما ⚡︎...",
        'downloading': "⬇︎ در حال دانلود با بهترین کیفیت...",
        'uploading': "⬆︎ در حال آپلود به تلگرام...",
        'error_generic': "✕ خطا: {error}",
        'error_size': "✕ فایل بیش از حد بزرگ است (حداکثر ۵۰ مگابایت).",
        'error_unsupported': "✕ لینک پشتیبانی نمی‌شود یا خصوصی است.",
        'send_url': "⚠︎ لطفاً یک لینک معتبر ارسال کنید.",
        'caption': "❖ <b>{title}</b>\n\n➢ دانلود شده توسط: @{bot_user}",
        'sites_btn': "⟡ سایت‌های پشتیبانی شده ⟡",
        'settings_btn': "⚙️ تنظیمات",
        'back_btn': "🔙 بازگشت",
        'select_lang': "❖ لطفاً زبان خود را انتخاب کنید",
        'lang_set': "✅ زبان به فارسی تنظیم شد",
        'help_title': "💠 روش دانلود از یوتیوب:\n🏷 لینک ویدیو یا نام آن را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از اینستاگرام:\n🏷 لینک پست/ریل یا یوزرنیم برای استوری ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از فیسبوک:\n🏷 لینک ویدیوی عمومی را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از پینترست:\n🏷 لینک پین یا جستجو با تصویر.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از لایکی:\n🏷 لینک ویدیو را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از توییتر:\n🏷 لینک توییت را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از تیک تاک:\n🏷 لینک ویدیو را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از اسنپ چت:\n🏷 لینک پروفایل عمومی را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از تلگرام:\n🏷 لینک استوری را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از ساندکلاود:\n🏷 لینک آهنگ را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از دِیلی‌موشن:\n🏷 لینک ویدیو را ارسال کنید.\n┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉ ┉\n💠 روش دانلود از ویمئو:\n🏷 لینک ویدیو را ارسال کنید.",
        'make_bot': "🔨 <b>ساخت ربات مشابه</b>\n\nارتباط با توسعه‌دهنده:\n@avetaar\nیا کانال منبع:\nhttps://t.me/+rawFtlErSFRlZjhk",
        'admin_panel': "♛ <b>پنل مدیریت</b> ♛\n\n👥 کل کاربران: <code>{total}</code>\n⚙️ وضعیت ربات: {status}\n📡 پینگ: <code>{ping}ms</code>",
        'status_online': "🟢 فعال",
        'status_maintenance': "🔴 تعمیرات",
        'broadcast_start': "➢ پیام را ارسال کنید (متن/عکس/ویدئو) برای همگانی:",
        'broadcast_progress': "➢ در حال ارسال همگانی...",
        'broadcast_done': "✅ همگانی انجام شد\n🟢 موفق: {success}\n🔴 ناموفق: {failed}",
        'ban_prompt': "➢ شناسه کاربری برای مسدود کردن را ارسال کنید:",
        'unban_prompt': "➢ شناسه کاربری برای رفع مسدودیت را ارسال کنید:",
        'user_banned': "🚫 کاربر {uid} مسدود شد.",
        'user_unbanned': "✅ کاربر {uid} از مسدودیت خارج شد.",
        'user_not_banned': "⚠️ کاربر در لیست مسدود نیست.",
        'invalid_id': "⚠️ لطفاً یک شماره معتبر ارسال کنید.",
        'maintenance_on': "🔒 حالت تعمیرات فعال شد.",
        'maintenance_off': "🔓 حالت تعمیرات غیرفعال شد.",
        'access_denied': "⛔ دسترسی غیرمجاز.",
    }
}

# ==================== قاعدة البيانات ====================
class Database:
    def __init__(self, db_path=DATABASE_NAME):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # جدول المستخدمين
            c.execute('''CREATE TABLE IF NOT EXISTS users 
                        (user_id INTEGER PRIMARY KEY, 
                         username TEXT, 
                         first_name TEXT, 
                         last_name TEXT,
                         joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                         language TEXT DEFAULT 'ar')''')
            # جدول الإعدادات
            c.execute('''CREATE TABLE IF NOT EXISTS settings 
                        (id INTEGER PRIMARY KEY CHECK (id=1), 
                         maintenance_mode INTEGER DEFAULT 0, 
                         ban_list TEXT DEFAULT '')''')
            c.execute('INSERT OR IGNORE INTO settings (id, maintenance_mode, ban_list) VALUES (1, 0, "")')
            conn.commit()
    
    def add_user(self, user_id, username, first_name, last_name=None):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''INSERT OR IGNORE INTO users 
                        (user_id, username, first_name, last_name) 
                        VALUES (?, ?, ?, ?)''',
                     (user_id, username, first_name, last_name))
            conn.commit()
    
    def get_user_lang(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            return result[0] if result else 'ar'
    
    def set_user_lang(self, user_id, lang):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
            conn.commit()
    
    def get_all_users(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT user_id FROM users')
            return [row[0] for row in c.fetchall()]
    
    def count_users(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM users')
            return c.fetchone()[0]
    
    def get_settings(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT maintenance_mode, ban_list FROM settings WHERE id = 1')
            row = c.fetchone()
            return {'maintenance_mode': row[0], 'ban_list': row[1] if row[1] else ''}
    
    def set_maintenance(self, mode):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE settings SET maintenance_mode = ? WHERE id = 1', (1 if mode else 0,))
            conn.commit()
    
    def get_ban_list(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT ban_list FROM settings WHERE id = 1')
            ban_str = c.fetchone()[0]
            return [int(x) for x in ban_str.split(',') if x.strip()]
    
    def add_to_ban_list(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT ban_list FROM settings WHERE id = 1')
            current = c.fetchone()[0]
            ban_list = [x for x in current.split(',') if x] + [str(user_id)]
            c.execute('UPDATE settings SET ban_list = ? WHERE id = 1', (','.join(ban_list),))
            conn.commit()
    
    def remove_from_ban_list(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('SELECT ban_list FROM settings WHERE id = 1')
            current = c.fetchone()[0]
            ban_list = [x for x in current.split(',') if x and int(x) != user_id]
            c.execute('UPDATE settings SET ban_list = ? WHERE id = 1', (','.join(ban_list),))
            conn.commit()
    
    def is_banned(self, user_id):
        return user_id in self.get_ban_list()

db = Database()

# ==================== خدمة التحميل ====================
class DownloadService:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': os.path.join(DOWNLOAD_PATH, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def download(self, url: str, unique_id: str) -> Dict:
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = os.path.join(DOWNLOAD_PATH, f'{unique_id}.%(ext)s')
        
        loop = asyncio.get_event_loop()
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                
                if info is None:
                    raise Exception("فشل استخراج المعلومات")
                
                filename = ydl.prepare_filename(info)
                
                # البحث عن الملف إذا كان الامتداد مختلفاً
                if not os.path.exists(filename):
                    for f in os.listdir(DOWNLOAD_PATH):
                        if f.startswith(unique_id):
                            filename = os.path.join(DOWNLOAD_PATH, f)
                            break
                    else:
                        raise Exception("لم يتم العثور على الملف بعد التحميل")
                
                filesize = os.path.getsize(filename)
                
                if filesize > MAX_FILE_SIZE:
                    os.remove(filename)
                    raise Exception(f"حجم الملف كبير: {filesize} > {MAX_FILE_SIZE}")
                
                return {
                    'path': filename,
                    'title': info.get('title', 'بدون عنوان'),
                    'ext': os.path.splitext(filename)[1][1:].lower(),
                    'filesize': filesize,
                    'webpage_url': info.get('webpage_url', url)
                }
                
        except yt_dlp.utils.DownloadError as e:
            raise Exception(f"خطأ في التحميل: {str(e)}")
        except Exception as e:
            raise Exception(f"خطأ غير متوقع: {str(e)}")
    
    def cleanup(self, filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.error(f"فشل حذف {filepath}: {e}")

downloader = DownloadService()

# ==================== أدوات مساعدة ====================
def get_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return db.get_user_lang(user_id)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_ping() -> int:
    return int(time.time() * 1000) % 1000

def get_main_keyboard(lang: str, user_id: int):
    buttons = [
        [InlineKeyboardButton(LANG[lang]['help_title'].split('\n')[0][:15] + "...", callback_data='help')],
        [InlineKeyboardButton(LANG[lang]['settings_btn'], callback_data='settings')],
        [InlineKeyboardButton("صنع بوت مشابه", callback_data='make_bot')]
    ]
    
    if is_admin(user_id):
        buttons.insert(0, [InlineKeyboardButton("♛ لوحة التحكم ♛", callback_data='admin_panel')])
    
    dev_buttons = [
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    
    return InlineKeyboardMarkup(buttons + dev_buttons)

# ==================== معالج /start ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # حفظ المستخدم
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # التحقق من وجود لغة
    lang = db.get_user_lang(user.id)
    
    if not lang or lang not in LANG:
        # عرض اختيار اللغة
        keyboard = [
            [InlineKeyboardButton("🇮🇶 العربية", callback_data='lang_ar'),
             InlineKeyboardButton("🇺🇸 English", callback_data='lang_en'),
             InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_fa')],
            [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
            [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
        ]
        
        await update.message.reply_text(
            "❖ Welcome / أهلاً بك / خوش آمدید\n\n☟ Please Select Your Language ☟\n☟ اختر لغة البوت ☟\n☟ لطفاً زبان خود را انتخاب کنید ☟",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # التحقق من الحظر والصيانة
    if db.is_banned(user.id):
        return
    
    settings = db.get_settings()
    if settings['maintenance_mode'] and not is_admin(user.id):
        await update.message.reply_text(LANG[lang]['maintenance'])
        return
    
    # عرض القائمة الرئيسية
    text = LANG[lang]['welcome'].format(name=user.first_name)
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_main_keyboard(lang, user.id)
    )

# ==================== معالج الأزرار ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # معالج تغيير اللغة
    if data.startswith('lang_'):
        lang = data.split('_')[1]
        db.set_user_lang(user_id, lang)
        
        await query.edit_message_text(
            LANG[lang]['lang_set'],
            parse_mode=ParseMode.HTML
        )
        
        # عرض القائمة الرئيسية
        text = LANG[lang]['welcome'].format(name=query.from_user.first_name)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard(lang, user_id)
        )
        return
    
    # الحصول على لغة المستخدم
    lang = db.get_user_lang(user_id)
    
    # معالج المساعدة
    if data == 'help':
        back_button = [[InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')]]
        dev_buttons = [
            [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
            [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
        ]
        await query.edit_message_text(
            LANG[lang]['help_title'],
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(back_button + dev_buttons)
        )
    
    # معالج الإعدادات
    elif data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🇮🇶 العربية", callback_data='lang_ar'),
             InlineKeyboardButton("🇺🇸 English", callback_data='lang_en'),
             InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_fa')],
            [InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')],
            [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
            [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
        ]
        await query.edit_message_text(
            LANG[lang]['select_lang'],
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # معالج صنع بوت مشابه
    elif data == 'make_bot':
        back_button = [[InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')]]
        dev_buttons = [
            [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
            [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
        ]
        await query.edit_message_text(
            LANG[lang]['make_bot'],
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(back_button + dev_buttons)
        )
    
    # العودة للقائمة الرئيسية
    elif data == 'back_home':
        text = LANG[lang]['welcome'].format(name=query.from_user.first_name)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_keyboard(lang, user_id)
        )
    
    # لوحة التحكم للأدمن
    elif data == 'admin_panel' and is_admin(user_id):
        await show_admin_panel(update, context)

# ==================== معالج الروابط ====================
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text.strip()
    
    # التحقق من الحظر
    if db.is_banned(user.id):
        return
    
    # التحقق من الصيانة
    settings = db.get_settings()
    lang = db.get_user_lang(user.id)
    
    if settings['maintenance_mode'] and not is_admin(user.id):
        await update.message.reply_text(LANG[lang]['maintenance'])
        return
    
    # التحقق من الرابط
    if not re.match(r'^https?://', url):
        await update.message.reply_text(LANG[lang]['send_url'])
        return
    
    # إرسال رسالة المعالجة
    status_msg = await update.message.reply_text(LANG[lang]['process'])
    
    # إنشاء معرف فريد
    unique_id = f"{user.id}_{int(time.time())}"
    
    try:
        # تحديث الحالة
        await status_msg.edit_text(LANG[lang]['downloading'])
        
        # التحميل
        result = await downloader.download(url, unique_id)
        
        # تحديث الحالة
        await status_msg.edit_text(LANG[lang]['uploading'])
        
        # إعداد التسمية
        caption = LANG[lang]['caption'].format(
            title=result['title'][:100],
            bot_user=context.bot.username
        )
        
        # رفع الملف حسب نوعه
        with open(result['path'], 'rb') as f:
            if result['ext'] in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
                await update.message.reply_video(
                    video=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
            elif result['ext'] in ['mp3', 'm4a', 'wav', 'ogg']:
                await update.message.reply_audio(
                    audio=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            elif result['ext'] in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                await update.message.reply_photo(
                    photo=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await update.message.reply_document(
                    document=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        
        # تنظيف الملف
        downloader.cleanup(result['path'])
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        error_msg = str(e)
        
        if "File too large" in error_msg or "filesize" in error_msg:
            await status_msg.edit_text(LANG[lang]['error_size'])
        elif "Unsupported" in error_msg or "not supported" in error_msg:
            await status_msg.edit_text(LANG[lang]['error_unsupported'])
        else:
            await status_msg.edit_text(LANG[lang]['error_generic'].format(error="رابط غير صالح أو خاص"))
        
        # تنظيف في حالة الخطأ
        if 'result' in locals():
            downloader.cleanup(result['path'])

# ==================== لوحة تحكم الأدمن ====================
async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer(LANG['ar']['access_denied'], show_alert=True)
        return
    
    lang = db.get_user_lang(user_id)
    total_users = db.count_users()
    settings = db.get_settings()
    
    status = LANG[lang]['status_online'] if not settings['maintenance_mode'] else LANG[lang]['status_maintenance']
    ping = get_ping()
    
    text = LANG[lang]['admin_panel'].format(total=total_users, status=status, ping=ping)
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data='admin_broadcast'),
         InlineKeyboardButton("📊 Stats", callback_data='admin_stats')],
        [InlineKeyboardButton("🔒 Lock Bot", callback_data='admin_lock'),
         InlineKeyboardButton("🔓 Unlock Bot", callback_data='admin_unlock')],
        [InlineKeyboardButton("🚫 Ban User", callback_data='admin_ban'),
         InlineKeyboardButton("✅ Unban User", callback_data='admin_unban')],
        [InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')],
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_admin_panel(update, context)

async def admin_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    
    db.set_maintenance(True)
    lang = db.get_user_lang(query.from_user.id)
    await query.answer(LANG[lang]['maintenance_on'])
    await show_admin_panel(update, context)

async def admin_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    
    db.set_maintenance(False)
    lang = db.get_user_lang(query.from_user.id)
    await query.answer(LANG[lang]['maintenance_off'])
    await show_admin_panel(update, context)

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    
    lang = db.get_user_lang(query.from_user.id)
    await query.edit_message_text(LANG[lang]['broadcast_start'])
    return BROADCAST

async def admin_broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    lang = db.get_user_lang(user_id)
    status_msg = await update.message.reply_text(LANG[lang]['broadcast_progress'])
    
    users = db.get_all_users()
    success = 0
    failed = 0
    
    for uid in users:
        try:
            if update.message.text:
                await context.bot.send_message(uid, update.message.text, parse_mode=ParseMode.HTML)
            elif update.message.photo:
                await context.bot.send_photo(uid, update.message.photo[-1].file_id, caption=update.message.caption, parse_mode=ParseMode.HTML)
            elif update.message.video:
                await context.bot.send_video(uid, update.message.video.file_id, caption=update.message.caption, parse_mode=ParseMode.HTML)
            elif update.message.document:
                await context.bot.send_document(uid, update.message.document.file_id, caption=update.message.caption, parse_mode=ParseMode.HTML)
            success += 1
        except Exception as e:
            logger.warning(f"فشل البث للمستخدم {uid}: {e}")
            failed += 1
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(LANG[lang]['broadcast_done'].format(success=success, failed=failed))
    return ConversationHandler.END

async def admin_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    
    lang = db.get_user_lang(query.from_user.id)
    await query.edit_message_text(LANG[lang]['ban_prompt'])
    return BAN

async def admin_ban_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    lang = db.get_user_lang(user_id)
    text = update.message.text.strip()
    
    if not text.isdigit():
        await update.message.reply_text(LANG[lang]['invalid_id'])
        return BAN
    
    uid = int(text)
    db.add_to_ban_list(uid)
    await update.message.reply_text(LANG[lang]['user_banned'].format(uid=uid))
    return ConversationHandler.END

async def admin_unban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    
    lang = db.get_user_lang(query.from_user.id)
    await query.edit_message_text(LANG[lang]['unban_prompt'])
    return UNBAN

async def admin_unban_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    lang = db.get_user_lang(user_id)
    text = update.message.text.strip()
    
    if not text.isdigit():
        await update.message.reply_text(LANG[lang]['invalid_id'])
        return UNBAN
    
    uid = int(text)
    ban_list = db.get_ban_list()
    
    if uid in ban_list:
        db.remove_from_ban_list(uid)
        await update.message.reply_text(LANG[lang]['user_unbanned'].format(uid=uid))
    else:
        await update.message.reply_text(LANG[lang]['user_not_banned'])
    
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return ConversationHandler.END
    
    lang = db.get_user_lang(user_id)
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

# ==================== التشغيل الرئيسي ====================
def main():
    """تشغيل البوت"""
    logger.info("🚀 بدء تشغيل البوت...")
    
    # إنشاء التطبيق
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # محادثة البث
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern='^admin_broadcast$')],
        states={
            BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, admin_broadcast_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)],
        per_user=True
    )
    
    # محادثة الحظر
    ban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_ban_start, pattern='^admin_ban$')],
        states={
            BAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)],
        per_user=True
    )
    
    # محادثة إلغاء الحظر
    unban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_unban_start, pattern='^admin_unban$')],
        states={
            UNBAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_unban_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)],
        per_user=True
    )
    
    # إضافة المعالجات
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('admin', show_admin_panel))
    app.add_handler(CommandHandler('cancel', admin_cancel))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    app.add_handler(CallbackQueryHandler(admin_lock, pattern='^admin_lock$'))
    app.add_handler(CallbackQueryHandler(admin_unlock, pattern='^admin_unlock$'))
    
    app.add_handler(broadcast_conv)
    app.add_handler(ban_conv)
    app.add_handler(unban_conv)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # تشغيل البوت
    logger.info("✅ البوت يعمل...")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}", exc_info=True)