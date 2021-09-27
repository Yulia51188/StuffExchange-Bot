from enum import Enum
from textwrap import dedent

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
import random
from django.db.models import Q


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


# TO DO: add db functions
def create_new_stuff(chat_id, user, title):
    profile = Profile.objects.filter(name=user.username)[0]
    stuff = Stuff.objects.create(
        profile=profile,
        description=title,
    )
    stuff_id = stuff.id
    return stuff_id


def add_photo_to_new_stuff(chat_id, photo_url, _new_stuff_id):
    add_image_url = Stuff.objects.filter(id=_new_stuff_id).update(image_url=photo_url)


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
    return profile.tg_username or profile.contact


def make_exchange(chat_id, stuff_id):
    stuff_info = Stuff.objects.get(id=stuff_id)
    status_like = stuff_info.status_like_users
    if status_like is False:
        new_status_like = [chat_id]
        stuff_info = Stuff.objects.get(id=stuff_id)
        stuff_info.status_like_users = new_status_like
        stuff_info.save()
        stuff_info = Stuff.objects.get(id=stuff_id)
        status_like_users = stuff_info.status_like_users
        logger.info(status_like_users)
        username = stuff_info.profile
        users_stuff = Stuff.objects.filter(profile=username)
        is_available = False
        for stuff in users_stuff:
            if stuff.status_like_users is False:
                pass
            else:
                for user in stuff.status_like_users:
                    if user == username.id:
                        is_available = True
        stuff = {'id': chat_id, 'title': stuff_info.description}
        exchange_stuff = {'id': stuff_id, 'title': stuff_info.description}
        owner = {'chat_id': chat_id, 'username': username}
        return is_available, stuff, exchange_stuff, owner
    else:
        stuff_info = Stuff.objects.get(id=stuff_id)
        users_likes = stuff_info.status_like_users
        new_users_likes = users_likes + [chat_id]
        logger.info(new_users_likes)
        stuff_info.status_like_users = new_users_likes
        stuff_info.save()
        username = stuff_info.profile
        users_stuff = Stuff.objects.filter(profile=username)
        is_available = False
        for stuff in users_stuff:
            if stuff.status_like_users is False:
                pass
            else:
                for user in stuff.status_like_users:
                    if user == username.id:
                        is_available = True
        stuff = {'id': chat_id, 'title': stuff_info.description}
        exchange_stuff = {'id': stuff_id, 'title': stuff_info.description}
        owner = {'chat_id': chat_id, 'username': username}
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
    is_contact = add_user_to_db(update.message.chat_id, user)
    if not is_contact:
        update.message.reply_text(
            text=dedent(f'''
            Привет, {user.first_name}!
            У тебя не указано имя пользователя в Телеграме.

            Укажи телефон или email, чтобы при обмене с тобой можно было\
            связаться'''
            )
        ) 
        return States.INPUT_CONTACT
    update.message.reply_text(
        text=f'Привет, {user.first_name}!',
        reply_markup=get_start_keyboard_markup()
    ) 
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


def handle_add_contact(update, context):
    profile = Profile.objects.get(external_id=update.message.chat_id)
    profile.contact = update.message.text
    profile.save()
    update.message.reply_text(
        f'В профиль добавлен контакт для связи: {profile.contact}',
        reply_markup=get_start_keyboard_markup()
    )
    logger.info(f'Пользователю {profile.chat_id} добавлен контакт {profile.contact}')
    return States.WAITING_FOR_CLICK


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!',
        reply_markup=get_empty_keyboard())
    return ConversationHandler.END


def handle_add_stuff(update, context):
    global _current_stuff_id
    _current_stuff_id = None

    update.message.reply_text(f'Введите название вещи')
    return States.WAITING_INPUT_TITLE


def handle_new_stuff_photo(update, context):
    global _new_stuff_id
    stuff_photo = update.message.photo[0]
    add_photo_to_new_stuff(update.message.chat_id, stuff_photo.file_id,
        _new_stuff_id)
    update.message.reply_text(
        f'Фото вещи добавлено',
        reply_markup=get_start_keyboard_markup()
    )    
    return States.WAITING_FOR_CLICK


def handle_new_stuff_title(update, context):
    global _new_stuff_id

    stuff_title = update.message.text
    stuff_id = create_new_stuff(update.message.chat_id, update.effective_user,
        stuff_title)
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


def get_empty_keyboard():
    return ReplyKeyboardMarkup()


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
            },
            fallbacks=[CommandHandler('stop', handle_stop)]
        )
        dispatcher.add_handler(conv_handler)

        # 3 -- запустить бесконечную обработку входящих сообщений
        updater.start_polling()
        updater.idle()