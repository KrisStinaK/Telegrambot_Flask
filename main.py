import datetime

import telebot
from config import TOKEN
import time
from telebot import types
import requests

from data import db_session
from data.users import User


bot = telebot.TeleBot(TOKEN)

db_session.global_init('db/record.sqlite')
session = db_session.create_session()


@bot.message_handler(commands=['start'])
def startcommand(message):
    time.sleep(0.3)
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Записать расходы')
    btn2 = types.KeyboardButton('Показать расходы')
    btn3 = types.KeyboardButton('Куда сходить?')
    markup.add(btn1, btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}👋!')
    time.sleep(0.3)
    bot.send_message(message.chat.id, text="Это бот для учёта финансовых расходов.", reply_markup=markup)
    bot.send_message(message.chat.id, 'Вызовите команду "/help" для просмотра команд и возможностей')


@bot.message_handler(commands=['help'])
def help_command(message):
    time.sleep(0.3)
    text = f'Записать расходы \nПосмотреть расходы\nРасходы по датам' \
           f'\nОбщая сумма расходов за день\nКуда сходить?\nКонвертировать валюту'
    bot.send_message(message.chat.id, text)


@bot.message_handler()
def on_click(message):
    if message.text.lower() == 'записать расходы':
        bot.send_message(message.chat.id, 'Введите расход через дефис в виде [КАТЕГОРИЯ-ЦЕНА-ВАЛЮТА]:')
        bot.register_next_step_handler(message, repeat_all_messages)
    elif message.text.lower() == 'показать расходы':
        for user in session.query(User).all():
            text_message = f'{user.today} \nПользователь: {user.user_name} \nкатегория: {user.category} \nсумма: {user.price}\n'
            bot.send_message(message.chat.id, text_message)
    elif message.text.lower() == 'куда сходить?':
        bot.register_next_step_handler(message, organization)
    elif message.text.lower() == 'расходы по датам':
        bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
        bot.register_next_step_handler(message, expenses_by_dates)
    elif message.text.lower() == 'общая сумма расходов за день':
        bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
        bot.register_next_step_handler(message, amount_of_expenses)
    elif message.text.lower() == 'конвертировать валюту':
        bot.send_message(message.chat.id, 'Введите валюту в формате [Из какой(GBP)-В какую(GBP)-Сколько]')
        bot.register_next_step_handler(message, currency)
    if 'прив' in message.text.lower():
        time.sleep(0.3)
        bot.send_message(message.chat.id, 'Привет!☺')


def repeat_all_messages(message):
    try:
        category, price, currency = message.text.split('-')
        today = datetime.date.today()
        text_message = f'На {today} в таблицу расходов добавлена запись: категория {category}, сумма {price} {currency}'
        bot.send_message(message.chat.id, text_message)

        # открываем таблицу и добавляем запись
        user = User()
        user.user_name = message.from_user.first_name
        user.category = category
        user.price = price
        user.currency = currency
        user.today = today
        session.add(user)
        session.commit()
    except:
        # если пользователь ввел неправильную информацию, оповещаем его и просим вводить повторно
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


def organization(message):
    text_message = 'Выберите категорию и город в формате ["КАТЕГОРИЯ", "ГОРОД"]:'
    bot.send_message(message.chat.id, text_message)
    bot.register_next_step_handler(message, poisk)


def expenses_by_dates(message):
    expenses = []
    for user in session.query(User).all():
        if user.today == message.text:
            expenses.append(f'{user.today} \nПользователь: {user.user_name} \nкатегория: {user.category} \nсумма: {user.price}\n')
    if expenses:
        for i in expenses:
            bot.send_message(message.chat.id, i)
    else:
        bot.send_message(message.chat.id, 'На эту дату нет расходов')


def amount_of_expenses(message):
    total_amount = []
    for user in session.query(User).all():
        if user.today == message.text:
            total_amount.append(user.price)
    if total_amount:
        bot.send_message(message.chat.id, str(sum(list(map(int, total_amount)))))
        print(sum(list(map(int, total_amount))))
    else:
        bot.send_message(message.chat.id, 'На эту дату нет расходов')


def currency(message):
    cur, is_cur, bablo = message.text.split('-')
    url = f"https://api.apilayer.com/fixer/convert?to={cur}&from={is_cur}&amount={bablo}"

    payload = {}
    headers = {
        "apikey": "rUFaftGw0CkdMq4KL8ZMCMxezCLLeigq"
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    if response:
        try:
            json = response.json()['result']
            bot.send_message(message.chat.id, str(json))
        except:
            pass


def poisk(message):
    apikey = "9ec7254a-4fc4-49cf-b617-89cd8e5f5860"
    sp = message.text.split(', ')
    try:
        request = f'https://search-maps.yandex.ru/v1/?text={sp[0]},{sp[1]}&type=biz&lang=ru_RU&apikey={apikey}'
        response = requests.get(request)
        if response:
            try:
                for i in range(1, 10):
                    json = response.json()['features'][i]['properties']['CompanyMetaData']['Categories'][0]['name']
                    json1 = response.json()['features'][i]['properties']['CompanyMetaData']['Hours']['text']
                    json2 = response.json()['features'][i]['properties']['CompanyMetaData']['name']
                    json3 = response.json()['features'][i]['properties']['CompanyMetaData']['address']
                    json4 = response.json()['features'][i]['properties']['CompanyMetaData']['Phones'][0]['formatted']
                    text_message = f'{json}, {json2} \n{json3} \n{json1} \n{json4}\n'
                    bot.send_message(message.chat.id, text_message)
            except:
                pass

    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')
    # https://search-maps.yandex.ru/v1/?text=кафе,Псков&type=biz&lang=ru_RU&apikey=9ec7254a-4fc4-49cf-b617-89cd8e5f5860


# START
bot.polling(none_stop=True)
