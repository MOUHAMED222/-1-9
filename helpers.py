import time
import logging
from functools import wraps
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import db
from config import ADMIN_ID

logger = logging.getLogger(__name__)

def get_lang(update: Update) -> str:
    """Get user language from database or default to 'ar'."""
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    return lang if lang else 'ar'

def restricted(func):
    """Decorator to restrict access to admins only."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔ Access Denied.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def check_banned(func):
    """Decorator to block banned users."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if db.is_banned(user_id):
            return  # Ignore banned users
        return await func(update, context, *args, **kwargs)
    return wrapped

def check_maintenance(func):
    """Decorator to block if maintenance mode is on (except admin)."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        settings = db.get_settings()
        if settings['maintenance_mode'] and user_id != ADMIN_ID:
            lang = get_lang(update)
            from languages import LANG
            await update.message.reply_text(LANG[lang]['maintenance'])
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def get_ping():
    """Return current ping in ms."""
    return round(time.time() * 1000) % 1000  # Dummy ping

async def send_or_edit(update: Update, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
    """Helper to either edit or send a new message."""
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)

def get_main_menu_keyboard(lang: str, user_id: int):
    """Build main menu inline keyboard."""
    from languages import LANG
    buttons = [
        [InlineKeyboardButton(LANG[lang]['help_title'].split('\n')[0][:20] + "...", callback_data='help')],
        [InlineKeyboardButton(LANG[lang]['settings_btn'], callback_data='settings')],
        [InlineKeyboardButton("صنع بوت مشابه", callback_data='make_bot')]  # Fixed text
    ]
    if user_id == ADMIN_ID:
        buttons.insert(0, [InlineKeyboardButton("♛ لوحة التحكم ♛", callback_data='admin_panel')])
    # Developer buttons (fixed)
    dev_buttons = [
        [InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/avetaar")],
        [InlineKeyboardButton("𓄼𝗦𝗼𝘂𝗿𝗰𝗲𓄹", url="https://t.me/+rawFtlErSFRlZjhk")]
    ]
    return InlineKeyboardMarkup(buttons + dev_buttons)

# Import here to avoid circular imports
from telegram import InlineKeyboardButton