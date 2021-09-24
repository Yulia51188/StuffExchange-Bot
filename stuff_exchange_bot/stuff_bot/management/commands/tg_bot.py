import os
from enum import Enum

from django.conf import settings
from django.core.management.base import BaseCommand

from stuff_bot.models import Profile, Stuff
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from telegram.utils.request import Request
import logging


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
_current_stuff_id = None
_new_stuff_id = None


class States(Enum):
    START = 0
    WAITING_FOR_CLICK = 1
    WAITING_INPUT_TITLE = 2
    WAITING_INPUT_PHOTO = 3


# TO DO: add db functions
def create_new_stuff(chat_id, user, title):
    profile, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': user.username,
        }
    )
    stuff = Stuff(
        profile=profile,
        description=title,
    )
    stuff.save()
    

def add_photo_to_new_stuff(chat_id, photo_url, stuff_id):
    #
    pass


def add_user_to_db(chat_id, user):
    p, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={
            'name': user.username,
        }
    )
    p.save()


def make_exchange(chat_id, stuff_id):
    # Need DB
    # Test Data
    is_available = True
    stuff = {'id': 3, 'title': 'Зайчик'}
    exchange_stuff = {'id': 2, 'title': 'Книга о вкусной и здоровой пище'}
    owner = {'chat_id': '1967131305', 'username': 'yulya6a'}
    # --------
    return is_available, stuff, exchange_stuff, owner


def get_random_stuff(chat_id):
    return None


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
    global _current_stuff_id

    random_stuff = get_random_stuff(
        update.message.chat_id)
    if not random_stuff:
        update.message.reply_text(
            text='Не найдено вещей других пользователей',
            reply_markup=get_start_keyboard_markup()
        ) 
        _current_stuff_id = None              
    
    stuff_id, stuff_title, stuff_photo_url = random_stuff
    update.message.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=stuff_photo_url,
        caption=f'{stuff_title}',
        reply_markup=get_full_keyboard_markup()
    )

    _current_stuff_id = stuff_id

    return States.WAITING_FOR_CLICK


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')
    return ConversationHandler.END


def handle_add_stuff(update, context):
    global _current_stuff_id
    _current_stuff_id = None

    update.message.reply_text('Введите название вещи')
    return States.WAITING_INPUT_TITLE


def handle_new_stuff_photo(update, context): 
    global _new_stuff_id
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, stuff_photo.file_id,
        _new_stuff_id)
    update.message.reply_text(
        'Фото вещи добавлено',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK


def handle_new_stuff_title(update, context):  
    global _new_stuff_id

    stuff_title = update.message.text
    stuff_id = create_new_stuff(update.message.chat_id, update.effective_user,
        stuff_title)
    update.message.reply_text(f'Добавлена вещь, {stuff_title}')
    logger.info(
        f'Добавлена вещь {stuff_title} #{stuff_id} от {update.message.chat_id}')
    _new_stuff_id = stuff_id
    update.message.reply_text('Добавьте фотографию')
    return States.WAITING_INPUT_PHOTO


def handle_exchange(update, context):
    global _current_stuff_id

    is_available, stuff, exchange_stuff, owner = make_exchange(
        update.message.chat_id, _current_stuff_id)
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

    _current_stuff_id = None
    
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


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        # 1 -- правильное подключение
        request = Request(
            connect_timeout=0.5,
            read_timeout=1.0,
        )
        bot = Bot(
            request=request,
            token=settings.TOKEN,
            base_url=getattr(settings, 'PROXY_URL', None),
        )
        print(bot.get_me())

        # 2 -- обработчики
        updater = Updater(settings.TOKEN)
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

        # 3 -- запустить бесконечную обработку входящих сообщений
        updater.start_polling()
        updater.idle()
