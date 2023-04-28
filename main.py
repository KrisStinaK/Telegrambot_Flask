import datetime
import telebot
from config import TOKEN
import time
from telebot import types
import requests
import openai
import pygame

from data import db_session
from data.users import User


bot = telebot.TeleBot(TOKEN)
openai.api_key = "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"
db_session.global_init('db/record.sqlite')
session = db_session.create_session()

calc_mode = False
balanc = 0


@bot.message_handler(commands=['help'])
def help_command(message):
    time.sleep(0.3)
    text = f'/write_expenses - Записать расходы\n/view_expenses - Посмотреть расходы\n/expenses_dates - Расходы по датам' \
           f'\n/amount_day - Общая сумма расходов за день\n/organization_search - Поиск организации\n/convert_currency - Конвертировать валюту\n' \
           f'/currency_rate - Курс валюты \n/calc - Калькулятор\n/add_capital - Добавить капитал\n/balance - Баланс\n/gpt - Пообщайтесь с ии Chat gpt\n' \
           f'Вызовите функцию повторно чтобы ее отключить'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['start'])
def startcommand(message):
    time.sleep(0.3)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn = types.KeyboardButton('/help')
    btn1 = types.KeyboardButton('/write_expenses')
    btn2 = types.KeyboardButton('/view_expenses')
    btn3 = types.KeyboardButton('/expenses_dates')
    btn4 = types.KeyboardButton('/amount_day')
    btn5 = types.KeyboardButton('/organization_search')
    btn6 = types.KeyboardButton('/convert_currency')
    btn7 = types.KeyboardButton('/currency_rate')
    btn8 = types.KeyboardButton('/calc')
    btn9 = types.KeyboardButton('/add_capital')
    btn10 = types.KeyboardButton('/balance')
    btn11 = types.KeyboardButton('/gpt')
    markup.add(btn, btn1, btn2, btn3, btn4, btn5)
    markup.add(btn6, btn7, btn8, btn9, btn10, btn11)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}👋!')
    time.sleep(0.3)
    bot.send_message(message.chat.id, text="Это бот для учёта финансовых расходов.", reply_markup=markup)
    bot.send_message(message.chat.id, 'Вызовите команду "/help" для просмотра команд и возможностей')


@bot.message_handler(commands=['calc'])
def switch_calc_mode(message):
    global calc_mode
    if calc_mode:
        bot.send_message(message.chat.id, 'режим калькулятор выключен')
        calc_mode = False
        print(calc_mode)
    else:
        bot.send_message(message.chat.id, 'режим калькулятор включен')
        calc_mode = True
        print(calc_mode)


@bot.message_handler()
def on_click(message):
    if calc_mode:
        bot.reply_to(message, calculate(message.text))
    else:
        if message.text.lower() == '/write_expenses':
            bot.send_message(message.chat.id, 'Введите расход через дефис в виде [КАТЕГОРИЯ-ЦЕНА-ВАЛЮТА]:')
            bot.register_next_step_handler(message, repeat_all_messages)
        elif message.text.lower() == '/view_expenses':
            for user in session.query(User).all():
                text_message = f'{user.today} \nПользователь: {user.user_name} \nкатегория: {user.category} \nсумма: {user.price}\n'
                bot.send_message(message.chat.id, text_message)
        elif message.text.lower() == '/organization_search':
            text_message = 'Выберите категорию и город в формате ["КАТЕГОРИЯ", "ГОРОД"]:'
            bot.send_message(message.chat.id, text_message)
            bot.register_next_step_handler(message, poisk)
        elif message.text.lower() == '/expenses_dates':
            bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
            bot.register_next_step_handler(message, expenses_by_dates)
        elif message.text.lower() == '/amount_day':
            bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
            bot.register_next_step_handler(message, amount_of_expenses)
        elif message.text.lower() == '/convert_currency':
            bot.send_message(message.chat.id, 'Введите валюту в формате [В какую(GBP)-Из какой(GBP)-Сколько]')
            bot.register_next_step_handler(message, currency)
        elif message.text.lower() == '/currency_rate':
            bot.send_message(message.chat.id, 'Введите валюту в формате (GBP)')
            bot.register_next_step_handler(message, currency_exchange_rate)
        elif message.text.lower() == '/add_capital':
            bot.send_message(message.chat.id, 'Введите ваш капитал')
            bot.register_next_step_handler(message, capital)
        elif message.text.lower() == '/balance':
            bot.register_next_step_handler(message, balance)



@bot.message_handler()
def process_request(message):
    try:
        # Get user message
        user_message = message.text
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=user_message,
            max_tokens=100
        )

        # Get OpenAI response
        bot_response = response.choices[0].text

        # Send response to user
        bot.reply_to(message, bot_response)

    except Exception as e:
        # Handle errors
        bot.reply_to(message, "Sorry, I couldn't process your request. Please try again later.")


def calculate(message):
    try:
        result = eval(message)
        return str(result)
    except ZeroDivisionError:
        return 'Некорректное выражение'
    except:
        return 'Отключите режим калькулятора'


def is_calc_type(message):
    if '+' in message.text or '-' in message.text or '*' in message.text or\
            '/' in message.text or '//' in message.text or '%' in message.text and \
            message.text[1] != '/':
        return True
    else:
        return False


def repeat_all_messages(message):
    global balanc
    try:
        category, price, currency = message.text.split('-')
        today = datetime.date.today()
        text_message = f'На {today} в таблицу расходов добавлена запись: категория {category}, сумма {price} {currency}'
        bot.send_message(message.chat.id, text_message)
        balanc -= int(price)

        # открываем таблицу и добавляем запись
        user = User()
        user.user_name = message.from_user.first_name
        user.category = category
        user.price = price
        user.currency = currency
        user.today = today
        user.capital = balanc
        session.add(user)
        session.commit()
    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


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


def capital(message):
    global balanc
    try:
        balanc += int(message.text)
        user = User()
        user.capital = int(message.text)
        session.add(user)
        session.commit()
        bot.send_message(message.chat.id, 'Теперь я могу считывать ваш баланс!')
    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


def balance(message):
    global balanc
    bot.send_message(message.chat.id, str(balanc))


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
            bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
            bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


def currency_exchange_rate(message):
    try:
        data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        bot.send_message(message.chat.id, f"{data['Valute'][message.text]['Value']} ₽")
    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


def poisk(message):
    apikey = "9ec7254a-4fc4-49cf-b617-89cd8e5f5860"
    sp = message.text.split(', ')
    sp2 = []
    request = f'https://search-maps.yandex.ru/v1/?text={sp[0]},{sp[1]}&type=biz&lang=ru_RU&apikey={apikey}'
    response = requests.get(request)
    if response:
        try:
            for i in range(1, 20):
                json = response.json()['features'][i]['properties']['CompanyMetaData']['Categories'][0]['name']
                json1 = response.json()['features'][i]['properties']['CompanyMetaData']['Hours']['text']
                json2 = response.json()['features'][i]['properties']['CompanyMetaData']['name']
                json3 = response.json()['features'][i]['properties']['CompanyMetaData']['address']
                json4 = response.json()['features'][i]['properties']['CompanyMetaData']['Phones'][0]['formatted']
                json_st = response.json()['features'][i]['geometry']['coordinates'][0]
                json_st2 = response.json()['features'][i]['geometry']['coordinates'][1]
                sp2.append(json_st), sp2.append(json_st2)
                text_message = f'{json}, {json2} \n{json3} \n{json1} \n{json4}\n'
                bot.send_message(message.chat.id, text_message)
        except:

            bot.send_message(message.chat.id, 'ОШИБКА! Что-то пошло не так, введите команду заново и повторите попытку')
            pygame.init()

        request = f'https://static-maps.yandex.ru/1.x/?pt={sp2[0]},{sp2[1]},org~{sp2[2]},' \
                  f'{sp2[3]},org~{sp2[4]},{sp2[5]},org~{sp2[6]},{sp2[7]},org~{sp2[8]},{sp2[9]},org,&z=13&size=650,450&l=map'
        print(sp2)
        response = requests.get(request)
        if response:
            with open('map.jpeg', mode='wb') as map_file:
                map_file.write(response.content)
            photo = open('map.jpeg', 'rb')
            bot.send_photo(message.chat.id, photo)
        else:
            raise RuntimeError


    # https://search-maps.yandex.ru/v1/?text=кафе,Псков&type=biz&lang=ru_RU&apikey=9ec7254a-4fc4-49cf-b617-89cd8e5f5860


# START
bot.polling(none_stop=True)