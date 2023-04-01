import telebot
from config import TOKEN
from datetime import date
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
    btn3 = types.KeyboardButton('Интересные места')
    markup.add(btn1, btn2)
    markup.row(btn3)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}👋!')
    time.sleep(0.3)
    bot.send_message(message.chat.id, text="Это бот для учёта финансовых расходов.", reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_command(message):
    time.sleep(0.3)
    text_message = f'''Нажмите кнопку "Записать расходы" для записи расходов
Нажмите кнопку "Показать расходы" чтобы посмотреть добавленные расходы'''
    bot.send_message(message.chat.id, text_message)


@bot.message_handler()
def on_click(message):
    if message.text == 'Записать расходы':
        bot.send_message(message.chat.id, 'Введите расход через дефис в виде [КАТЕГОРИЯ-ЦЕНА]:')
        bot.register_next_step_handler(message, repeat_all_messages)
    elif message.text == 'Показать расходы':
        for user in session.query(User).all():
            text_message = f'{user.today} \nПользователь: {user.user_name} \nкатегория: {user.category} \nсумма: {user.price}\n'
            bot.send_message(message.chat.id, text_message)
    elif message.text == 'Интересные места':
        bot.register_next_step_handler(message, organization)



def repeat_all_messages(message):
        try:
            today = date.today().strftime("%d.%m.%Y")

            #  разделяем сообщение на 2 части, категория и цена
            category, price = message.text.split("-", 1)
            text_message = f'На {today} в таблицу расходов добавлена запись: категория {category}, сумма {price} сум'
            bot.send_message(message.chat.id, text_message)

            # открываем таблицу и добавляем запись
            user = User()
            user.user_name = message.from_user.first_name
            user.category = category
            user.price = price
            session.add(user)
            session.commit()
        except:
            # если пользователь ввел неправильную информацию, оповещаем его и просим вводить повторно
            bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите расход через дефис в виде [КАТЕГОРИЯ-ЦЕНА]:')


@bot.message_handler()
def get_message_text(message):
    if 'прив' in message.text.lower():
        time.sleep(0.3)
        bot.send_message(message.chat.id, 'Привет!☺☺☺')


def organization(message):
    if message.text == 'Интересные места':
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Еда', callback_data='food')
        btn2 = types.InlineKeyboardButton('Кино', callback_data='cinema')
        btn3 = types.InlineKeyboardButton('Спорт', callback_data='sport')
        markup.add(btn1, btn2, btn3)
        text_message = 'Выберите категорию:'
        bot.send_message(message.chat.id, text_message, reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_1(callback):
    bot.send_message(callback.message.chat.id, 'Выберите город')
    bot.register_next_step_handler(callback.message, poisk)


def poisk(message):
    apikey = "9ec7254a-4fc4-49cf-b617-89cd8e5f5860"
    if message.text == 'Еда':
        request = f'https://search-maps.yandex.ru/v1/?text=Еда,Псков&type=biz&lang=ru_RU&apikey={apikey}'
    elif message.text == 'Кино':
        request = f'https://search-maps.yandex.ru/v1/?text=Кинотеатры,Псков&type=biz&lang=ru_RU&apikey={apikey}'
    elif message.text == 'Спорт':
        request = f'https://search-maps.yandex.ru/v1/?text=Фитнесклубы,Псков&type=biz&lang=ru_RU&apikey={apikey}'
    else:
        request = f'https://search-maps.yandex.ru/v1/?text=Клубы,Псков&type=biz&lang=ru_RU&apikey={apikey}'
    responce = requests.get(request)
    if responce:
        try:
            for i in range(1, 10):
                json = responce.json()['features'][i]['properties']['CompanyMetaData']['Categories'][0]['name']
                json1 = responce.json()['features'][i]['properties']['CompanyMetaData']['Hours']['text']
                json2 = responce.json()['features'][i]['properties']['CompanyMetaData']['name']
                json3 = responce.json()['features'][i]['properties']['CompanyMetaData']['address']
                json4 = responce.json()['features'][i]['properties']['CompanyMetaData']['Phones'][0]['formatted']
                text_message = f'{json}, {json2} \n{json3} \n{json1} \n{json4}\n'
                bot.send_message(message.chat.id, text_message)
        except:
            pass
    # https://search-maps.yandex.ru/v1/?text=кафе,Псков&type=biz&lang=ru_RU&apikey=9ec7254a-4fc4-49cf-b617-89cd8e5f5860


# START
bot.polling(none_stop=True)
