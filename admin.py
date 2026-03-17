import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database import db
from languages import LANG
from utils.helpers import get_lang, restricted, get_ping
from config import ADMIN_ID

# States for conversation
(BROADCAST, BAN, UNBAN) = range(3)

logger = logging.getLogger(__name__)

@restricted
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display admin panel."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

@restricted
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats (just refresh panel)."""
    await admin_panel(update, context)

@restricted
async def admin_lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable maintenance mode."""
    db.set_maintenance(True)
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await query.edit_message_text(LANG[lang]['maintenance_on'])
    await asyncio.sleep(1)
    await admin_panel(update, context)

@restricted
async def admin_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable maintenance mode."""
    db.set_maintenance(False)
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await query.edit_message_text(LANG[lang]['maintenance_off'])
    await asyncio.sleep(1)
    await admin_panel(update, context)

@restricted
async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast conversation."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await query.edit_message_text(LANG[lang]['broadcast_start'])
    return BROADCAST

@restricted
async def admin_broadcast_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive broadcast message and send to all users."""
    lang = get_lang(update)
    msg = await update.message.reply_text(LANG[lang]['broadcast_progress'])
    
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
            logger.warning(f"Broadcast failed to {uid}: {e}")
            failed += 1
        await asyncio.sleep(0.05)  # Avoid flood
    
    await msg.edit_text(LANG[lang]['broadcast_done'].format(success=success, failed=failed))
    return ConversationHandler.END

@restricted
async def admin_ban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start ban conversation."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await query.edit_message_text(LANG[lang]['ban_prompt'])
    return BAN

@restricted
async def admin_ban_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive user ID to ban."""
    lang = get_lang(update)
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text(LANG[lang]['invalid_id'])
        return BAN
    uid = int(text)
    db.add_to_ban_list(uid)
    await update.message.reply_text(LANG[lang]['user_banned'].format(uid=uid))
    return ConversationHandler.END

@restricted
async def admin_unban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start unban conversation."""
    query = update.callback_query
    await query.answer()
    lang = get_lang(update)
    await query.edit_message_text(LANG[lang]['unban_prompt'])
    return UNBAN

@restricted
async def admin_unban_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive user ID to unban."""
    lang = get_lang(update)
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

@restricted
async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current admin operation."""
    lang = get_lang(update)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END