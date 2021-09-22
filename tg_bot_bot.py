from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from dotenv import load_dotenv
import os
import sqlite3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


conn = sqlite3.connect('tg_bot_database/tg_bot_database.db',
    check_same_thread=False)
cursor = conn.cursor()


def handle_start(update, context):
    keyboard = [
        [InlineKeyboardButton("Добавить вещь", callback_data='1')],
        [InlineKeyboardButton("Найти вещь", callback_data='2')],
        [InlineKeyboardButton("Хочу обменяться", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\!',
        reply_markup=reply_markup
    )


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')


def echo(update, context):
    update.message.reply_text(update.message.text)


def add_user_to_db(user_id, user_name):
    cursor.execute('INSERT INTO db_users (id, username) VALUES (?, ?)',
        (user_id, user_name))
    conn.commit()


def main():
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
  
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", handle_start))
    dispatcher.add_handler(CommandHandler("stop", handle_stop))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
