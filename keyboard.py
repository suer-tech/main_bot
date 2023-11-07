from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

button_pos = KeyboardButton("Pos")
button_balance = KeyboardButton("Balance")

greet_kb1 = ReplyKeyboardMarkup(resize_keyboard=True).add(button_pos, button_balance)





