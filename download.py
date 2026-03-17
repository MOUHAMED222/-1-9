import os
import time
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import db
from languages import LANG
from utils.helpers import get_lang, check_banned, check_maintenance
from services.downloader import DownloadService, DownloadError
from config import MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)
downloader = DownloadService()

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process URL messages."""
    user = update.effective_user
    # Check ban and maintenance
    if db.is_banned(user.id):
        return
    settings = db.get_settings()
    lang = get_lang(update)
    if settings['maintenance_mode'] and user.id != ADMIN_ID:
        await update.message.reply_text(LANG[lang]['maintenance'])
        return
    
    url = update.message.text.strip()
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text(LANG[lang]['send_url'])
        return
    
    # Send processing message
    msg = await update.message.reply_text(LANG[lang]['process'])
    
    # Generate unique ID for this download
    unique_id = f"{user.id}_{int(time.time())}"
    
    try:
        # Update status to downloading
        await msg.edit_text(LANG[lang]['downloading'])
        
        # Perform download
        result = await downloader.download(url, unique_id)
        
        # Update status to uploading
        await msg.edit_text(LANG[lang]['uploading'])
        
        # Prepare caption
        caption = LANG[lang]['caption'].format(title=result['title'], bot_user=context.bot.username)
        
        # Send file based on extension
        with open(result['path'], 'rb') as f:
            if result['ext'] in ['mp4', 'mov', 'avi', 'mkv']:
                await update.message.reply_video(
                    video=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
            elif result['ext'] in ['mp3', 'm4a', 'wav']:
                await update.message.reply_audio(
                    audio=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            elif result['ext'] in ['jpg', 'jpeg', 'png', 'gif']:
                await update.message.reply_photo(
                    photo=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                # As document
                await update.message.reply_document(
                    document=f,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
        
        # Cleanup
        downloader.cleanup(result['path'])
        await msg.delete()
        
    except DownloadError as e:
        logger.error(f"Download error for {url}: {e}")
        if "File too large" in str(e):
            await msg.edit_text(LANG[lang]['error_size'])
        else:
            await msg.edit_text(LANG[lang]['error_unsupported'])
    except Exception as e:
        logger.exception(f"Unexpected error in handle_url: {e}")
        await msg.edit_text(LANG[lang]['error_generic'].format(error=str(e)))
        if 'result' in locals():
            downloader.cleanup(result['path'])