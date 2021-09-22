from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def handle_start(update, context):
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Привет, {user.mention_markdown_v2()}\!',
    )


def handle_stop(update, context):
    user = update.effective_user
    update.message.reply_text(f'До свидания, {user.username}!')


def echo(update, context):
    update.message.reply_text(update.message.text)


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
