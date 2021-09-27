
import logging
import random

from enum import Enum
from textwrap import dedent

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from dotenv import load_dotenv
from stuff_bot.models import Profile, Stuff
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)
from telegram.utils.request import Request


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
    INPUT_CONTACT = 4
    INPUT_LOCATION = 5


# TO DO: add db functions
def create_new_stuff(chat_id, user, title):
    profile = Profile.objects.get(external_id=chat_id)
    stuff = Stuff.objects.create(
        profile=profile,
        description=title,
    )
    return stuff.id


def add_photo_to_new_stuff(chat_id, photo_url, _new_stuff_id):
    add_image_url = Stuff.objects \
        .filter(id=_new_stuff_id) \
        .update(image_url=photo_url)


def add_user_to_db(chat_id, user):
    profile, _ = Profile.objects.get_or_create(external_id=chat_id)

    logger.info(f'Get profile {profile}')
    profile.tg_username = user.username or ''
    profile.first_name = user.first_name or ''
    profile.last_name = user.last_name or ''

    profile.save()

    logger.info(f'Update_user {profile.external_id}, username '
        f'{profile.tg_username}, contact {profile.contact}')
    logger.info(f'Is user contact: {bool(profile.tg_username or profile.contact)}')
    return profile.tg_username or profile.contact, bool(profile.lat)


def make_exchange(chat_id, stuff_id):
    stuff_info = Stuff.objects.get(id=stuff_id)
    status_like = stuff_info.status_like_users
    if status_like is False:
        new_status_like = [chat_id]
        stuff_info = Stuff.objects.get(id=stuff_id)
        stuff_info.status_like_users = new_status_like
        stuff_info.save()
        username_1 = Profile.objects.get(external_id=chat_id)
        users_stuff = Stuff.objects.filter(profile=username_1)
        stuff_username_2 = Stuff.objects.get(id=stuff_id)
        username_2 = stuff_username_2.profile
        is_available = False
        for stuff in users_stuff:
            if stuff.status_like_users is False:
                pass
            else:
                for user in stuff.status_like_users:
                    if user == username_2.external_id:
                        is_available = True
        stuff = {'id': chat_id, 'title': stuff_info.description}
        exchange_stuff = {'id': stuff_id, 'title': stuff_info.description}
        owner = {'chat_id': username_2.external_id, 'username': username}
        logger.info(is_available)
        return is_available, stuff, exchange_stuff, owner
    else:
        stuff_info = Stuff.objects.get(id=stuff_id)
        users_likes = stuff_info.status_like_users
        new_users_likes = users_likes + [chat_id]
        logger.info(new_users_likes)
        stuff_info.status_like_users = new_users_likes
        stuff_info.save()

        username_1 = Profile.objects.get(external_id=chat_id)
        users_stuff = Stuff.objects.filter(profile=username_1)
        stuff_username_2 = Stuff.objects.get(id=stuff_id)
        username_2 = stuff_username_2.profile
        is_available = False
        for stuff in users_stuff:
            if stuff.status_like_users is False:
                pass
            else:
                for user in stuff.status_like_users:
                    if user == username_2.external_id:
                        is_available = True
        stuff = {'id': chat_id, 'title': stuff_info.description}
        exchange_stuff = {'id': stuff_id, 'title': stuff_info.description}
        owner = {'chat_id': username_2.external_id, 'username': username_2}
        return is_available, stuff, exchange_stuff, owner


def get_random_stuff(chat_id):
    user = Profile.objects.get(external_id=chat_id)
    username = user.id
    random_stuff = list(Stuff.objects.filter(~Q(profile=username)))
    if not any(random_stuff):
        return None
    random_item = random.choice(random_stuff)
    stuff_id = random_item.id
    stuff_title = random_item.description
    stuff_photo = random_item.image_url
    return stuff_id, stuff_title, stuff_photo


def handle_error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)


def handle_start(update, context):
    user = update.effective_user
    is_contact, is_location = add_user_to_db(update.message.chat_id, user)
    if not is_contact:
        update.message.reply_text(
            text=dedent(f'''
            Привет, {user.first_name}!
            У тебя не указано имя пользователя в Телеграме.

            Укажи телефон или email, чтобы при обмене с тобой можно было связаться'''
            )
        ) 
        return States.INPUT_CONTACT
    update.message.reply_text(
        text=f'Привет, {user.first_name}!',
        reply_markup=get_start_keyboard_markup()
    )
    if not is_location:
        update.message.reply_text(
            text=f'Укажи местоположение, чтобы я мог найти вещи рядом',
            reply_markup=get_location_keyboard()
        )         
        return States.INPUT_LOCATION
    return States.WAITING_FOR_CLICK


def handle_find_stuff(update, context):
    stuff_id, stuff_title, stuff_photo = get_random_stuff(
        update.message.chat_id)
    update.message.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=stuff_photo,
        caption=f'{stuff_title}',
        reply_markup=get_full_keyboard_markup()
    )

    global _current_stuff
    _current_stuff = stuff_id

    return States.WAITING_FOR_CLICK


def handle_add_contact(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.contact = update.message.text
    profile.save()
    update.message.reply_text(
        f'В профиль добавлен контакт для связи: {profile.contact}',
        reply_markup=get_start_keyboard_markup()
    )
    logger.info(f'Пользователю {profile.external_id} добавлен контакт {profile.contact}')
    if not profile.lat:
        update.message.reply_text(
            text=f'Укажи местоположение, чтобы я мог найти вещи рядом',
            reply_markup=get_location_keyboard()
        )         
        return States.INPUT_LOCATION
    return States.WAITING_FOR_CLICK


def handle_add_location(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    logger.info(f'{update.message.location.latitude}, {update.message.location.longitude}')
    profile.save() 
    if update.message.location: 
        profile.lat = update.message.location.latitude  
        profile.lon = update.message.location.longitude
        update.message.reply_text(
            f'В профиль добавлено местоположение: {profile.lat}, {profile.lon}',
            reply_markup=get_start_keyboard_markup()
        )
        logger.info(f'Пользователю {profile.external_id} добавлено местоположение '
            f'{profile.lat}, {profile.lon}')
    return States.WAITING_FOR_CLICK    


def handle_no_location(update, context):
    update.message.reply_text(
        'Местоположение не указано',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!',
        reply_markup=get_empty_keyboard())
    return ConversationHandler.END


def handle_add_stuff(update, context):
    global _current_stuff
    _current_stuff = None

    update.message.reply_text(f'Введите название вещи')
    return States.WAITING_INPUT_TITLE


def handle_new_stuff_photo(update, context):
    global _new_stuff_id
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, stuff_photo.file_id,
        _new_stuff_id)
    update.message.reply_text(
        f'Фото вещи добавлено',
        reply_markup=get_start_keyboard_markup(),
    )    
    return States.WAITING_FOR_CLICK


def handle_new_stuff_title(update, context):
    global _new_stuff_id

    stuff_title = update.message.text
    stuff_id = create_new_stuff(update.message.chat_id, update.effective_user,
        stuff_title)
    update.message.reply_text(f'Добавлена вещь, {stuff_title}')
    _new_stuff_id = stuff_id
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


def get_empty_keyboard():
    return ReplyKeyboardMarkup()


def get_location_keyboard():
    keyboard = [
        [KeyboardButton('Отправить свою локацию 🗺️', request_location=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_start_keyboard_markup():
    keyboard = [
        ['Добавить вещь'],
        ['Найти вещь'],
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_full_keyboard_markup():
    keyboard = [
        ['Добавить вещь'],
        ['Найти вещь'],
        ['Хочу обменяться'],
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
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
                    MessageHandler(Filters.text & ~Filters.command,
                        handle_unknown)
                ],
                States.WAITING_INPUT_TITLE: [
                    MessageHandler(Filters.text & ~Filters.command,
                                   handle_new_stuff_title)
                ],
                States.WAITING_INPUT_PHOTO: [
                    MessageHandler(Filters.photo, handle_new_stuff_photo),
                    MessageHandler(Filters.text & ~Filters.command,
                        handle_no_photo)
                ],
                States.INPUT_CONTACT: [
                    MessageHandler(Filters.text & ~Filters.command,
                        handle_add_contact)
                ],
                States.INPUT_LOCATION:
                [
                    MessageHandler(Filters.regex('^Нет$'), handle_no_location),
                    MessageHandler(None, handle_add_location),
                ],
            },
            fallbacks=[CommandHandler('stop', handle_stop)]
        )
        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
