import datetime
import telebot
from config import TOKEN
import time
from telebot import types
import requests
import openai

from data import db_session
from data.users import User


bot = telebot.TeleBot(TOKEN)
openai.api_key = "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"
db_session.global_init('db/record.sqlite')
session = db_session.create_session()

calc_mode = False
gpt_mode = False


@bot.message_handler(commands=['help'])
def help_command(message):
    time.sleep(0.3)
    text = f'Записать расходы \nПосмотреть расходы\nРасходы по датам' \
           f'\nОбщая сумма расходов за день\nКуда сходить?\nКонвертировать валюту\n' \
           f'Курс валюты \nКалькулятор\nДобавить капитал\nБаланс'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['start'])
def startcommand(message):
    time.sleep(0.3)
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Записать расходы')
    btn2 = types.KeyboardButton('Показать расходы')
    btn3 = types.KeyboardButton('Куда сходить?')
    btn4 = types.KeyboardButton('Расходы по датам')
    btn5 = types.KeyboardButton('Общая сумма расходов за день')
    btn6 = types.KeyboardButton('Конвертировать валюту')
    btn7 = types.KeyboardButton('Курс валюты')
    btn8 = types.KeyboardButton('/calc')
    btn9 = types.KeyboardButton('Добавить капитал')
    btn10 = types.KeyboardButton('Баланс')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    markup.row(btn6, btn7, btn8, btn9, btn10)
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


@bot.message_handler(func=lambda message: True)
def process_request(message):
    try:
        if message.text.lower() not in ['записать расходы', 'показать расходы',
                                        'куда сходить?', 'расходы по датам',
                                        'общая сумма расходов за день', 'конвертировать валюту',
                                        'курс валюты', 'калькулятор', 'добавить капитал', 'Баланс']:

            # Get user message
            user_message = message.text
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=user_message,
                max_tokens=50
            )

            # Get OpenAI response
            bot_response = response.choices[0].text

            # Send response to user
            bot.reply_to(message, bot_response)
        else:
            bot.register_next_step_handler(message, on_click)

    except Exception as e:
        # Handle errors
        bot.reply_to(message, "Sorry, I couldn't process your request. Please try again later.")


@bot.message_handler()
def on_click(message):
    if calc_mode:
        bot.reply_to(message, calculate(message.text))
    else:
        if message.text.lower() == 'записать расходы':
            bot.send_message(message.chat.id, 'Введите расход через дефис в виде [КАТЕГОРИЯ-ЦЕНА-ВАЛЮТА]:')
            bot.register_next_step_handler(message, repeat_all_messages)
        elif message.text.lower() == 'показать расходы':
            for user in session.query(User).all():
                text_message = f'{user.today} \nПользователь: {user.user_name} \nкатегория: {user.category} \nсумма: {user.price}\n'
                bot.send_message(message.chat.id, text_message)
        elif message.text.lower() == 'куда сходить?':
            text_message = 'Выберите категорию и город в формате ["КАТЕГОРИЯ", "ГОРОД"]:'
            bot.send_message(message.chat.id, text_message)
            bot.register_next_step_handler(message, poisk)
        elif message.text.lower() == 'расходы по датам':
            bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
            bot.register_next_step_handler(message, expenses_by_dates)
        elif message.text.lower() == 'общая сумма расходов за день':
            bot.send_message(message.chat.id, 'Введите дату в формате дд-мм-гг')
            bot.register_next_step_handler(message, amount_of_expenses)
        elif message.text.lower() == 'конвертировать валюту':
            bot.send_message(message.chat.id, 'Введите валюту в формате [В какую(GBP)-Из какой(GBP)-Сколько]')
            bot.register_next_step_handler(message, currency)
        elif message.text.lower() == 'курс валюты':
            bot.send_message(message.chat.id, 'Введите валюту в формате (GBP)')
            bot.register_next_step_handler(message, currency_exchange_rate)
        elif message.text.lower() == 'добавить капитал':
            bot.send_message(message.chat.id, 'Введите ваш капитал')
            bot.register_next_step_handler(message, capital)
        elif message.text.lower() == 'Баланс':
            bot.register_next_step_handler(message, balance)


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
            bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
            bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')
            bot.register_next_step_handler(message, balance)


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
    try:
        user = User()
        user.capital = int(message.text)
        session.add(user)
        session.commit()
        bot.send_message(message.chat.id, 'Теперь я могу считывать ваш баланс!')
    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')


def balance(message):
    pass


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
                bot.send_message(message.chat.id, 'ОШИБКА! Что-то пошло не так, введите команду заново и повторите попытку')

    except:
        bot.send_message(message.chat.id, 'ОШИБКА! Неправильный формат данных!')
        bot.send_message(message.chat.id, 'Введите команду заново и повторите попытку')
    # https://search-maps.yandex.ru/v1/?text=кафе,Псков&type=biz&lang=ru_RU&apikey=9ec7254a-4fc4-49cf-b617-89cd8e5f5860


# START
bot.polling(none_stop=True)