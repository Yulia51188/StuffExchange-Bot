from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
    ConversationHandler)
from telegram import ReplyKeyboardMarkup
import logging
from dotenv import load_dotenv
import os
from enum import Enum

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class States(Enum):
    START = 0
    WAITING_FOR_CLICK = 1
    WAITING_INPUT_TITLE = 2
    WAITING_INPUT_PHOTO = 3


def create_new_stuff(chat_id, user, title):
    pass


def add_photo_to_new_stuff(chat_id, user, title):
    pass


def handle_error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)


def handle_start(update, context):
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\!',
        reply_markup=get_start_keyboard_markup()
    ) 
    return States.WAITING_FOR_CLICK


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')
    return ConversationHandler.END


def handle_add_stuff(update, context):
    update.message.reply_text('Введите название вещи')
    return States.WAITING_INPUT_TITLE


def handle_new_stuff_photo(update, context): 
    logger.info('handle_new_stuff_photo'.upper())
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, update.effective_user, stuff_photo)
    update.message.reply_text(
        'Фото вещи добавлено',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK


def handle_new_stuff_title(update, context):  
    stuff_title = update.message.text
    create_new_stuff(update.message.chat_id, update.effective_user, stuff_title)
    update.message.reply_text(f'Добавлена вещь, {stuff_title}')
    update.message.reply_text('Добавьте фотографию')
    return States.WAITING_INPUT_PHOTO


def handle_unknown(update, context):
    update.message.reply_text(
        'Сообщение не распознано',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK    


def handle_no_photo(update, context):
    update.message.reply_text(
        'Загрузите фото, пожалуйста'
    )    
    return States.WAITING_INPUT_PHOTO    


def get_start_keyboard_markup():
    keyboard = [
        ['Добавить вещь'],
        ['Найти вещь'],
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def main():
    load_dotenv()
    tg_token = os.getenv("TG_TOKEN")
  
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', handle_start)],
        states={
            States.WAITING_FOR_CLICK: [
                MessageHandler(Filters.regex('^Добавить вещь$'),
                    handle_add_stuff),
                MessageHandler(Filters.text & ~Filters.command, handle_unknown)
            ],
            States.WAITING_INPUT_TITLE: [
                MessageHandler(Filters.text & ~Filters.command,
                    handle_new_stuff_title)
            ],
            States.WAITING_INPUT_PHOTO: [
                MessageHandler(Filters.photo, handle_new_stuff_photo),
                MessageHandler(Filters.text & ~Filters.command, handle_no_photo)
            ]
        },
        fallbacks=[CommandHandler('stop', handle_stop)]
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
