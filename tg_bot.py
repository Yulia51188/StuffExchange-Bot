from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from dotenv import load_dotenv
import os

import sqlite3
import telebot


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update, context):
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
    )


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
    bot = telebot.TeleBot(tg_token)
    conn = sqlite3.connect('tg_bot_database/tg_bot_database.db', check_same_thread=False)
    cursor = conn.cursor()

    def db_table_val(user_id: int, user_name: str):
        cursor.execute('INSERT INTO change_bot (user_id, user_name) VALUES (?, ?)',
                       (user_id, user_name))
        conn.commit()

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Добро пожаловать')

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text.lower() == 'привет':
            bot.send_message(message.chat.id, 'Привет! Ваше имя добавлено в базу данных!')

            us_id = message.from_user.id
            us_name = message.from_user.first_name

            db_table_val(user_id=us_id, user_name=us_name)

    db_table_val(user_id=us_id, user_name=us_name)

    bot.polling(none_stop=True)

# Код Юли
    updater = Updater(tg_token)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()

    updater.idle()



if __name__ == '__main__':
    main()
