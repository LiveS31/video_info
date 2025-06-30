# Телеграм бот для взаиможействия с файлами видео
import configparser  # читаем данные из файла
import datetime
import os

import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


if os.name == 'posix':
    video_cam = f'/home/lives/Видео'  # при необходимости заменить
    sl = '/'
else:
    video_cam = f'c:\video'  # при необходимости заменить
    sl = "'\'"
video_len = len(os.listdir(video_cam)) # количество папок видео


if os.name == 'posix':#
    screenshot_dir=f"/home/lives/Изображения" # изменить на нужный путь
    sl = '/'
else:
    screenshot_dir = f"c:\Изображения"
    sl = "'\'"
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
    # проверяем папки с видео
    if (message.from_user.id == 0 or message.from_user.id == int(userid)) and message.text.lower() == 'видео 📹':

        # считаем сколько внутри папок и выводимв интерактивное меню
        for i in range (video_len):
            # интерактивное меню
            buti = types.InlineKeyboardButton(f'{os.listdir(video_cam)[i]}', callback_data=f'skan_video_{os.listdir(video_cam)[i]}')
            us.add(buti)
##
    if (message.from_user.id == 0 or message.from_user.id == int(userid)) and message.text.lower() == 'фото 📷':
        # считаем сколько внутри папок и выводимв интерактивное меню
        for ii in range (foto_len):
            # интерактивное меню
            buti = types.InlineKeyboardButton(f'{os.listdir(screenshot_dir)[ii]}', callback_data=f'skan_foto_{os.listdir(screenshot_dir)[ii]}')
            us.add(buti)
    # Выводим информацию пользователю
    VideoBot.send_message(message.from_user.id, 'Выбери папку:', reply_markup=us)


    # if inf_us:
    #     inf_us=None
    #     # Отправляем пользователю сообщение аларм
    #     print ('fdsdfsdfsdfsdfsdfsdfsdfds')
    #     VideoBot.send_message(message.from_user.id, 'dsgfdsgjdslkgndfslknglkrjagljgvdslvn' )


    @VideoBot.callback_query_handler(func=lambda call: True)

    def callback_query(call):
        global up_load
        us2 = types.InlineKeyboardMarkup()

        if call.data[:10] == 'skan_video':
            video_fale = os.listdir(video_cam + sl + call.data[11:])
            for i in range(len(video_fale)):
                buti = types.InlineKeyboardButton(video_fale[i], callback_data=f'up{video_fale[i]}')
                us2.add(buti)
            VideoBot.send_message(call.from_user.id, f'Выбери файл:', reply_markup=us2)
            up_load = f'{video_cam}{sl}{call.data[11:]}{sl}'


        elif call.data[:9] == 'skan_foto':
            foto_fale = os.listdir(f'{screenshot_dir}{sl}{call.data[10:]}')
            for i in range(len(foto_fale)):
                buti = types.InlineKeyboardButton(foto_fale[i], callback_data=f'up{foto_fale[i]}')
                us2.add(buti)
            VideoBot.send_message(call.from_user.id, f'Выбери файл:', reply_markup=us2)
            up_load = f'{screenshot_dir}{sl}{call.data[10:]}{sl}'



        if call.data[:2] == 'up':
            file_path = f'{up_load}{call.data[2:]}'  # Замените на путь к вашему файлу
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    VideoBot.send_document(call.from_user.id, f)
            else:
                VideoBot.send_message(call.from_user.id, "Файл не найден.")






# while True:
#     try:
#         VideoBot.polling(none_stop=True)
#     except:
#         continue
VideoBot.polling(none_stop=True)
