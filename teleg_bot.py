#teleg_bot

import configparser
import os
import time

import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
from PIL import Image
import io

# Импортируем ВЕСЬ модуль main
import main

# Глобальные переменные для управления видеопотоком
video_thread = None
is_video_running = False

# Чтение конфигурации из info.ini
config = configparser.ConfigParser()
with open('info.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)

tel_key = config.get('section1', 'tel_bot')
userid = config.get('section1', 'userid')
id_cam = int(config.get('section2', 'id_cam'))

VideoBot = telebot.TeleBot(f'{tel_key}')

# Пути к папкам
if os.name == 'posix':
    screenshot_base_dir = os.path.expanduser("~/Изображения")
    video_cam_base_path = os.path.expanduser("~/Видео")
    sl = '/'
else:
    video_cam_base_path = f'C:\\video'
    screenshot_base_dir = f"C:\\Изображения"
    sl = '\\'

def get_folders_list(base_path):
    if not os.path.exists(base_path):
        os.makedirs(base_path, exist_ok=True)
    try:
        return [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
    except Exception as e:
        print(f"Ошибка при получении списка папок из {base_path}: {e}")
        return []

# Клавиатура для основного меню
markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True,
                             one_time_keyboard=True) #Делаем клавиатуру
#Делаем кнопки
button1 = KeyboardButton("ВИДЕО")
button2 = KeyboardButton("ФОТО")
button3 = KeyboardButton('Старт программы')
button4 = KeyboardButton('Остановить программу')
markup.add(button1, button2, button3)#, button4) #Выводим кнопки (оставнока работет через раз и можетт незапуститься)

# активируем по "/start"
@VideoBot.message_handler(commands=['start'])
def start_message(message):
    VideoBot.send_message(message.chat.id, "Привет! Выбери опцию:",
                          reply_markup=markup)

# работаем с обычным кодом
@VideoBot.message_handler(content_types=['text'])
def message_user(message):
    global is_video_running, video_thread
    if not (message.from_user.id == 0 or message.from_user.id == int(userid)): # прописывает id разрешенных пользователей
        VideoBot.send_message(message.chat.id, "Нет доступа.")
        return

    # выбираем клавиатуру
    us = types.InlineKeyboardMarkup()
    # делаем интерактивные кнопки
    if message.text.lower() == 'видео':
        current_video_folders = get_folders_list(video_cam_base_path)
        if not current_video_folders:
            VideoBot.send_message(message.from_user.id, 'Папка пуста или отсутствует.')
            return
        for folder_name in current_video_folders:
            buti = types.InlineKeyboardButton(folder_name,
                                              callback_data=f'skan_video_{folder_name}')
            us.add(buti)
        VideoBot.send_message(message.from_user.id, 'Выбери папку:', reply_markup=us)

    elif message.text.lower() == 'фото':
        current_foto_folders = get_folders_list(screenshot_base_dir)
        if not current_foto_folders:
            VideoBot.send_message(message.from_user.id, 'Папка пуста или отсутствует.')
            return
        for folder_name in current_foto_folders:
            buti = types.InlineKeyboardButton(folder_name,
                                              callback_data=f'skan_foto_{folder_name}')
            us.add(buti)
        VideoBot.send_message(message.from_user.id, 'Выбери папку:', reply_markup=us)

    elif message.text.lower() == 'старт программы':
        if not is_video_running or (video_thread and not video_thread.is_alive()):
            video_thread = threading.Thread(target=main.video_cap, args=(id_cam,)) # <--- указать номер камеры
            video_thread.start()
            is_video_running = True
            VideoBot.send_message(message.chat.id, "Запуск программы...")
        else:
            VideoBot.send_message(message.chat.id, "Программа была запущена ранее")

    elif message.text.lower() == 'остановить программу':
        if is_video_running and video_thread and video_thread.is_alive():
            main.stop_video_stream = True #
            is_video_running = False
            VideoBot.send_message(message.chat.id, "Отправлена команда на остановку видеопотока. \nЭто может занять несколько секунд...")
        else:
            VideoBot.send_message(message.chat.id, "Видеопоток не запущен или уже остановлен.")
    else:
        VideoBot.send_message(message.chat.id, "Неизвестная команда или у вас нет доступа.")

# перехватываем управление от интерактивной клавиатуры
@VideoBot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global up_load
    # делаем новую интерактивную клавиатуру
    us2 = types.InlineKeyboardMarkup()
    # проверяем пользователя
    if not (call.from_user.id == 0 or call.from_user.id == int(userid)):
        VideoBot.answer_callback_query(call.id, "У вас нет доступа.")
        return

    # сканируем папки на файлы и передаем дальше для выполнения действий
    if call.data.startswith('skan_video_'):
        folder_name = call.data[11:]
        current_video_path = os.path.join(video_cam_base_path, folder_name)
        if not os.path.exists(current_video_path):
            VideoBot.send_message(call.from_user.id, "Папка не найдена.")
            return
        video_files = [f for f in os.listdir(current_video_path) if
                       os.path.isfile(os.path.join(current_video_path, f))]
        if not video_files:
            VideoBot.send_message(call.from_user.id, 'В этой папке нет видео.')
            return
        for file_name in video_files:
            buti = types.InlineKeyboardButton(file_name, callback_data=f'up{file_name}')
            us2.add(buti)
        VideoBot.send_message(call.from_user.id, f'Выбери файл:', reply_markup=us2)
        up_load = f'{current_video_path}{sl}'

    # проверяем соответствующую функцию
    elif call.data.startswith('skan_foto_'):
        folder_name = call.data[10:]
        current_foto_path = os.path.join(screenshot_base_dir, folder_name)
        if not os.path.exists(current_foto_path):
            VideoBot.send_message(call.from_user.id, "Папка не найдена.")
            return
        foto_files = [f for f in os.listdir(current_foto_path) if
                      os.path.isfile(os.path.join(current_foto_path, f))]
        if not foto_files:
            VideoBot.send_message(call.from_user.id, 'B папке нет фото.')
            return
        for file_name in foto_files:
            buti = types.InlineKeyboardButton(file_name, callback_data=f'up{file_name}')
            us2.add(buti)
        VideoBot.send_message(call.from_user.id, f'Выбери файл:', reply_markup=us2)
        up_load = f'{current_foto_path}{sl}'

    elif call.data.startswith('up'):
        file_name_to_upload = call.data[2:]
        if 'up_load' in globals():
            file_path = f'{up_load}{file_name_to_upload}'
            if os.path.exists(file_path):
                try:
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            img = Image.open(file_path)
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format=img.format, quality=70) # Качество 70%
                            img_byte_arr.seek(0)
                            if img_byte_arr.getbuffer().nbytes > 10 * 1024 * 1024: # >10MB
                                VideoBot.send_message(call.from_user.id, "Размер больше допустимого.")
                            else:
                                VideoBot.send_photo(call.from_user.id, img_byte_arr)
                        except Exception as img_e:
                            print(f"Ошибка при сжатии или отправке фото: {img_e}. Попытка отправить оригинал.")
                            with open(file_path, 'rb') as f:
                                VideoBot.send_photo(call.from_user.id, f)
                    elif file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        with open(file_path, 'rb') as f:
                            VideoBot.send_video(call.from_user.id, f)
                    else:
                        with open(file_path, 'rb') as f:
                            VideoBot.send_document(call.from_user.id, f)
                except telebot.apihelper.ApiTelegramException as api_e:
                    if "file is too big" in str(api_e):
                        VideoBot.send_message(call.from_user.id, "Файл слишком большой для отправки через Telegram."
                                                              "\nПопробуйте сжать его или использовать облачное хранилище.")
                    else:
                        VideoBot.send_message(call.from_user.id, f"Ошибка Telegram: {api_e}")
                except Exception as e:
                    VideoBot.send_message(call.from_user.id, f"Ошибка при загрузке файла: {e}")
            else:
                VideoBot.send_message(call.from_user.id, "Файл не найден.")
        else:
            VideoBot.send_message(call.from_user.id, "Выберите папку.")

print("Бот запущен. Запустите программу...")
while True:
    try:
        VideoBot.polling(none_stop=True)
    except Exception:
        time.sleep(1)
        continue
