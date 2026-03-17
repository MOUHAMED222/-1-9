from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import db
from languages import LANG
from utils.helpers import get_lang, get_main_menu_keyboard, check_banned, check_maintenance
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    # Add user to database if not exists, update info
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Check if language is set
    lang = db.get_user_lang(user.id)
    if not lang:
        # Show language selection
        keyboard = [
            [InlineKeyboardButton("🇮🇶 العربية", callback_data='set_lang_ar'),
             InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en'),
             InlineKeyboardButton("🇮🇷 فارسی", callback_data='set_lang_fa')],
            [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar"),
             InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
        ]
        await update.message.reply_text(
            "❖ <b>Welcome</b> / <b>أهلاً بك</b>\n\n☟ Please Select Your Language ☟\n☟ اختر لغة البوت ☟",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Check maintenance and ban (decorators would be cleaner, but we'll call manually)
    settings = db.get_settings()
    if db.is_banned(user.id):
        return
    if settings['maintenance_mode'] and user.id != ADMIN_ID:
        await update.message.reply_text(LANG[lang]['maintenance'])
        return
    
    # Show main menu
    await show_main_menu(update, context, lang)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str):
    """Display main menu with buttons."""
    user = update.effective_user
    text = LANG[lang]['welcome'].format(name=user.first_name)
    reply_markup = get_main_menu_keyboard(lang, user.id)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    data = query.data
    lang_code = data.split('_')[-1]  # ar, en, fa
    
    user_id = query.from_user.id
    db.set_user_lang(user_id, lang_code)
    
    # Confirm and show main menu
    await query.edit_message_text(LANG[lang_code]['lang_set'], parse_mode=ParseMode.HTML)
    await show_main_menu(update, context, lang_code)