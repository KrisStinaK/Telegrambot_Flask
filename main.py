import telebot
from config import TOKEN
import time

from data import db_session
from data.users import User


bot = telebot.TeleBot(TOKEN)

db_session.global_init('db/record.sqlite')

@bot.message_handler(commands=['start'])
def start(message):
    time.sleep(0.3)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}👋!')
    time.sleep(0.3)
    bot.send_message(message.chat.id, text="Это бот для учёта финансовых расходов.")



# START
bot.polling(none_stop=True)