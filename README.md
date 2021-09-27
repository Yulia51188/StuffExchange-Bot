# StuffExchange-Bot

!!!!!!!!! Free exchange service in Telegram !!!!!!!!!
To place an item for exchange, click the “Add item” button. After that, the things of other users will become available to you. Click the "Find item" button and the bot sends you photos of items to exchange. If you like a thing - press the button "Exchange", no - dial "Find a thing" again. Clicked "exchange"? - if the owner of the item likes one of your items, the bot sends contacts to both of you.

## Demo

![tg_bot_demo](stuff_exchange_bot/demo/bot_demo.gif)

### Installing

To get started go to terminal(mac os) or CMD (Windows)
- create virtualenv, [See example](https://python-scripts.com/virtualenv)

```bash
$python virtualenv venv
```

- clone github repository

```bash
$git clone https://github.com/Yulia51188/StuffExchange-Bot.git
```

- install packages

```bash
$pip install -r requirements.txt
```

- get the token can obtain from @BotFather in Telegram, [See example](https://telegra.ph/Awesome-Telegram-Bot-11-11)
- create the file .env end put your token in `TG_TOKEN`
- run the bot with command below and pass to your bot chat in Telegram 

```bash
$python manage.py tg_bot
```

- for Admin access to database create super user 

```bash
$python manage.py createsuperuser"

```

- run the local server and pass to `http://127.0.0.1:8000/admin` to login to admin webpage
```bash
python manage.py runserver
```

## Authors

* **Yuliya Sviridenko** - [Yulia51188](https://github.com/Yulia51188)
* **Stas Koshenkov** - [Staskosh](https://github.com/Staskosh)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details



