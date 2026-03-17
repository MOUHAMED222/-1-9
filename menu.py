from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from languages import LANG
from utils.helpers import get_lang, get_main_menu_keyboard
from config import ADMIN_ID
import logging

logger = logging.getLogger(__name__)

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help text."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    text = LANG[lang]['help_title']
    back_button = [[InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')]]
    dev_buttons = [
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    reply_markup = InlineKeyboardMarkup(back_button + dev_buttons)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu (language selection)."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    text = LANG[lang]['select_lang']
    keyboard = [
        [InlineKeyboardButton("🇮🇶 العربية", callback_data='set_lang_ar'),
         InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en'),
         InlineKeyboardButton("🇮🇷 فارسی", callback_data='set_lang_fa')],
        [InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')],
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def make_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show information about making a similar bot."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    text = LANG[lang]['make_bot'].format(dev_username="avetaar", source_link="https://t.me/+rawFtlErSFRlZjhk")
    back_button = [[InlineKeyboardButton(LANG[lang]['back_btn'], callback_data='back_home')]]
    dev_buttons = [
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    reply_markup = InlineKeyboardMarkup(back_button + dev_buttons)
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await show_main_menu(update, context, lang)

# Import at bottom to avoid circular
from handlers.start import show_main_menu