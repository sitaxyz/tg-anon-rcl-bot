from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List

hash_data_keyboard = {}

def inline_button_builder(buttons=list(list(dict()))):
    if hash(str(buttons)) in hash_data_keyboard:
        return hash_data_keyboard.get(hash(str(buttons)))
    keyboard = InlineKeyboardMarkup()
    for row in buttons:
        keyboard.add(*[InlineKeyboardButton(text=button['text'], callback_data=button.get('callback_data'), url=button.get('url')) for button in row if 'text' in button])
    
    hash_data_keyboard[hash(str(buttons))] = keyboard

    return keyboard

def button_builder(buttons=list(list(dict()))):
    if hash(str(buttons)) in hash_data_keyboard:
        return hash_data_keyboard.get(hash(str(buttons)))
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in buttons:
        keyboard.add(*[KeyboardButton(text=button['text']) for button in row])
    
    hash_data_keyboard[hash(str(buttons))] = keyboard
    
    return keyboard
