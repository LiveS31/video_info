# Телеграм бот для взаиможействия с файлами видео
import configparser  # читаем данные из файла
import datetime
import os

import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

if os.name == 'posix':
    video_cam = f'/home/lives/Видео'  # при необходимости заменить
else:
    video_cam = f'c:\video'  # при необходимости заменить
video_len = len(os.listdir(video_cam)) # количество папок видео


if os.name == 'posix':#
    screenshot_dir=f"/home/lives/Изображения"
else:
    screenshot_dir = f"c:\Изображения"
foto_len = len(os.listdir(screenshot_dir))  # количество папок фото


config = configparser.ConfigParser() # помещаем в переменную
with open('info.ini', 'r') as f: # Чтение файла
    config.read_file(f)

tel_key = config.get('section1', 'tel_bot') # выбираем ключ из файла
userid = config.get('section1', 'userid')
VideoBot = telebot.TeleBot(f'{tel_key}') # токен будет использоваться для бота

# включаем клавиатуру
markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
#Делаем нужные кнопки
button1 = KeyboardButton("ВИДЕО 📹")
button2 = KeyboardButton("ФОТО 📷")
markup.add(button1, button2) # выводим их в нужном порядке
button3 = KeyboardButton('Посмотреть поток')
markup.add(button3)


@VideoBot.message_handler(commands=['start'])
def start_message(message):
    VideoBot.send_message(message.chat.id, "Привет! Выбери опцию:", reply_markup=markup)


@VideoBot.message_handler(content_types=['text'])
def message_user(message):
    #выбираем клавиатуру
    us = types.InlineKeyboardMarkup()
    #проверяем папки с видео
    if (message.from_user.id == 0 or message.from_user.id == int(userid)) and message.text.lower() == 'видео 📹':

        # считаем сколько внутри папок и выводимв интерактивное меню
        for i in range (video_len):
            # интерактивное меню
            buti = types.InlineKeyboardButton(f'{os.listdir(video_cam)[i]}', callback_data=f'skan_video{i}')
            us.add(buti)

    if (message.from_user.id == 0 or message.from_user.id == int(userid)) and message.text.lower() == 'фото 📷':
        # считаем сколько внутри папок и выводимв интерактивное меню
        for ii in range (foto_len):
            # интерактивное меню
            buti = types.InlineKeyboardButton(f'{os.listdir(screenshot_dir)[ii]}', callback_data=f'skan_foto{ii}')
            us.add(buti)
    # Dыводим информацию пользователю
    VideoBot.send_message(message.from_user.id, 'Выберите папку:', reply_markup=us)







# while True:
#     try:
#         VideoBot.polling(none_stop=True)
#     except:
#         continue
VideoBot.polling(none_stop=True)