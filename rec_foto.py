# запись фото и отправка его в телеграмм
import os
import cv2 # работа с видео
import configparser # для чтения ini

# Чтение конфигурации из info.ini
config = configparser.ConfigParser()
with open('info.ini', 'r') as f:
    config.read_file(f)

# Функция для создания скриншотов по движению
def screen_mov(frame, times, bot, user):
    times = times.replace(':', "").replace('.', "").replace(' ', '_')
    # путь линукс
    if os.name == 'posix':
        screenshot_dir = os.path.expanduser(f"~/Изображения/mot_pic_{times[6:17]}")
        sl = '/'
    else:
        # путь для windows
        screenshot_dir = f"C:\\Изображения\\mot_pic_{times[6:17]}"
        sl = '\\'

    # создаем папку если ее нет
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    # записываем файл с фото
    filename = os.path.join(screenshot_dir, f"foto_detect_{times}.jpg")
    cv2.imwrite(filename, frame)

    # Отрываем файл и отправляем фото
    with open(f'{screenshot_dir}{sl}foto_detect_{times}.jpg', 'rb') as f:
        bot.send_photo(int(user), f)

    return f"Сохранен скрин: foto_detect_{times}.jpg"
