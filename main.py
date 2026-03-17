#!/usr/bin/env python3
"""
Telegram Media Downloader Bot
Production-ready bot using python-telegram-bot v20+ and yt-dlp.
"""

import logging
import os
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)
from config import BOT_TOKEN, DOWNLOAD_PATH
from database import db
from handlers.start import start, set_language
from handlers.menu import help_handler, settings_handler, make_bot_handler, back_home
from handlers.download import handle_url
from handlers.admin import (
    admin_panel,
    admin_stats,
    admin_lock,
    admin_unlock,
    admin_broadcast_start,
    admin_broadcast_receive,
    admin_ban_start,
    admin_ban_receive,
    admin_unban_start,
    admin_unban_receive,
    admin_cancel,
    BROADCAST, BAN, UNBAN
)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Ensure download directory exists
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    
    # Create application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ========== Conversation Handlers ==========
    # Broadcast conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern='^admin_broadcast$')],
        states={
            BROADCAST: [MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL, admin_broadcast_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_callback_cancel)],
        per_user=True,
        per_chat=True
    )
    
    # Ban conversation
    ban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_ban_start, pattern='^admin_ban$')],
        states={
            BAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_ban_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_callback_cancel)],
        per_user=True,
        per_chat=True
    )
    
    # Unban conversation
    unban_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_unban_start, pattern='^admin_unban$')],
        states={
            UNBAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_unban_receive)]
        },
        fallbacks=[CommandHandler('cancel', admin_callback_cancel)],
        per_user=True,
        per_chat=True
    )
    
    # ========== Regular Handlers ==========
    # Start command
    application.add_handler(CommandHandler('start', start))
    
    # Admin panel command (direct)
    application.add_handler(CommandHandler('admin', admin_panel))
    
    # Callback queries
    application.add_handler(CallbackQueryHandler(set_language, pattern='^set_lang_'))
    application.add_handler(CallbackQueryHandler(help_handler, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(settings_handler, pattern='^settings$'))
    application.add_handler(CallbackQueryHandler(make_bot_handler, pattern='^make_bot$'))
    application.add_handler(CallbackQueryHandler(back_home, pattern='^back_home$'))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    application.add_handler(CallbackQueryHandler(admin_lock, pattern='^admin_lock$'))
    application.add_handler(CallbackQueryHandler(admin_unlock, pattern='^admin_unlock$'))
    
    # Add conversation handlers (they are also callback-based)
    application.add_handler(broadcast_conv)
    application.add_handler(ban_conv)
    application.add_handler(unban_conv)
    
    # Message handler for URLs (must come after conversation handlers)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    # Start polling
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling()

async def admin_callback_cancel(update, context):
    """Cancel admin operation from command."""
    await admin_cancel(update, context)
    return ConversationHandler.END

if __name__ == '__main__':
    main()