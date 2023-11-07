import importlib
import json
from datetime import datetime

from aiogram import Dispatcher

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor

from keyboard import greet_kb1
import os

token = '6419893616:AAG-tbu524ZN7IGIulbJA_ZxNLykdaJWeU0'

bot = Bot(token)
dp = Dispatcher(bot)

current_datetime = datetime.now()

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAIDZ2JEZuGR8N1D5s__y0O8cIUGMk9OAAIiEwACXWxwS64th70744A-IwQ')
    mess = f'Привет, <b>{message.from_user.first_name}</b>! Здесь будут уведомления об изменении цены и крупных сделках на фьючерсах биржи Binance!'
    await bot.send_message(message.chat.id, mess, parse_mode='html')

if __name__ == '__main__':
    executor.start_polling(dp)


