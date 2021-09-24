import logging
import os
import random
from enum import Enum

from dotenv import load_dotenv
import pandas as pd
from telegram import ReplyKeyboardMarkup
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
_current_stuff = None


class States(Enum):
    START = 0
    WAITING_FOR_CLICK = 1
    WAITING_INPUT_TITLE = 2
    WAITING_INPUT_PHOTO = 3
STUFF_DB_FILENAME = 'stuff.csv'

#TO DO: add db functions 
def create_new_stuff(chat_id, user, title, db_filename=STUFF_DB_FILENAME):
    if not os.path.exists(db_filename):
        stuff_df = pd.DataFrame(columns=['stuff_id', 'chat_id', 'username',
            'stuff_title', 'image_url']).set_index('stuff_id')
        stuff_id = 0
    else:
        stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
        stuff_id = stuff_df.index.max() + 1

    new_stuff = pd.Series(
        data={
            'chat_id': chat_id, 
            'username': user.username,
            'stuff_title': title,
            'image_url': '',
        },
        name=stuff_id
    )
    new_stuff_df = stuff_df.append(new_stuff)
    new_stuff_df.to_csv(db_filename)


def add_photo_to_new_stuff(chat_id, photo_url, db_filename=STUFF_DB_FILENAME):
    stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
    stuff_id = stuff_df[stuff_df.chat_id == chat_id].index.max() 
    stuff_df['image_url'][stuff_id] = photo_url
    stuff_df.to_csv(db_filename)


def add_user_to_db(chat_id, user):
    # Need DB 
    pass


def make_exchange(chat_id, stuff_id):
    # Need DB 
    # Test Data
    is_available = True
    stuff = {'id': 3, 'title': 'Зайчик'}
    exchange_stuff = {'id': 2, 'title': 'Книга о вкусной и здоровой пище'}
    owner = {'chat_id': '1967131305', 'username': 'yulya6a'}
    # --------
    return is_available, stuff, exchange_stuff, owner


def get_random_stuff(chat_id, db_filename=STUFF_DB_FILENAME):
    stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
    alias_stuff_df = stuff_df[stuff_df.chat_id != chat_id]
    if alias_stuff_df.empty:
        return None
    rand_index = random.choice(alias_stuff_df.index)
    rand_stuff = stuff_df.loc[rand_index]
    return rand_stuff.name, rand_stuff["stuff_title"], rand_stuff["image_url"]


def handle_error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)


def handle_start(update, context):
    user = update.effective_user
    update.message.reply_text(
        text=f'Привет, {user.username}!',
        reply_markup=get_start_keyboard_markup()
    ) 
    add_user_to_db(update.message.chat_id, user)
    return States.WAITING_FOR_CLICK


def handle_find_stuff(update, context):
    global _current_stuff

    random_stuff = get_random_stuff(
        update.message.chat_id)
    if not random_stuff:
        update.message.reply_text(
            text='Не найдено вещей других пользователей',
            reply_markup=get_start_keyboard_markup()
        ) 
        _current_stuff = None              
    
    stuff_id, stuff_title, stuff_photo_url = random_stuff
    update.message.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=stuff_photo_url,
        caption=f'{stuff_title}',
        reply_markup=get_full_keyboard_markup()
    )

    _current_stuff = stuff_id

    return States.WAITING_FOR_CLICK


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')
    return ConversationHandler.END


def handle_add_stuff(update, context):
    global _current_stuff
    _current_stuff = None

    update.message.reply_text('Введите название вещи')
    return States.WAITING_INPUT_TITLE


def handle_new_stuff_photo(update, context): 
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, stuff_photo.file_id)
    update.message.reply_text(
        'Фото вещи добавлено',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK


def handle_new_stuff_title(update, context):  
    stuff_title = update.message.text
    create_new_stuff(update.message.chat_id, update.effective_user,
        stuff_title)
    update.message.reply_text(f'Добавлена вещь, {stuff_title}')
    update.message.reply_text('Добавьте фотографию')
    return States.WAITING_INPUT_PHOTO


def handle_exchange(update, context):
    global _current_stuff

    is_available, stuff, exchange_stuff, owner = make_exchange(
        update.message.chat_id, _current_stuff)
    update.message.reply_text('Заявка на обмен принята')
    if is_available:
        update.message.reply_text(f'Контакты для обмена '
            f'"{stuff["title"]}#{stuff["id"]}": @{owner["username"]}',
            reply_markup=get_start_keyboard_markup()
        )
        update.message.bot.send_message(
            chat_id=int(owner["chat_id"]),
            text=f'''Контакты для обмена "{exchange_stuff["title"]}\
                #{exchange_stuff["id"]}": @{update.effective_user.username}'''
        )

    _current_stuff = None
    
    return States.WAITING_FOR_CLICK


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


def get_full_keyboard_markup():
    keyboard = [
        ['Добавить вещь'],
        ['Найти вещь'],
        ['Хочу обменяться'],
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
                MessageHandler(Filters.regex('^Найти вещь$'),
                    handle_find_stuff),
                MessageHandler(Filters.regex('^Хочу обменяться$'),
                    handle_exchange),
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
