import telebot
import os
import time
import json
import os

token = '6419893616:AAG-tbu524ZN7IGIulbJA_ZxNLykdaJWeU0'
bot = telebot.TeleBot(token, parse_mode = None)
users_id = [412850740]

def send_message(txt_file):
    if os.stat(txt_file).st_size > 0:
        with open(txt_file, 'r', encoding='utf-8') as fr:
            mess = fr.read()
        for user in users_id:
            try:
                bot.send_message(user, mess)
            except:
                continue
        with open(txt_file, 'w') as fw:
            pass

while True:
    time.sleep(1)
    send_message('signal_vol.txt')



bot.infinity_polling()


