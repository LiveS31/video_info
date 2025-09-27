# видеонаблюдение

from multiprocessing import Process
import cv2
import time
import os
import datetime
from collections import deque
import numpy as np
from rec_foto import screen_mov
import configparser
import telebot
from codr import start_conv_video #, starting

# Читаем конфиг из info.ini
config = configparser.ConfigParser()
with open('info.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)


tel_key = config.get('section1', 'tel_bot') # получаем значение бота
userid = config.get('section1', 'userid') # получаем значение пользователя
bot_instance = telebot.TeleBot(f'{tel_key}') # вводим токен бота в переменную
mov_in = int(config.get('section2', 'pre_record_time')) # пред запись видео
mov_out = int(config.get('section2', 'post_record_time'))
fpsinf = int(config.get('section2', 'fps_inf'))
obj = int(config.get('section2', 'object'))
brightnes = int(config.get('section2', 'brightness'))
# Новые параметры для разрешения
frame_width_conf = int(config.get('section2', 'width'))
frame_height_conf = int(config.get('section2', 'height'))
# архивация через x дней посл записи
arh_day = int(config.get('section2', 'day_arh'))
# время запуска архивации
time_arh = config.get('section2', 'arh_time').replace(':','')

# Глобальный флаг для остановки видеопотока
stop_video_stream = False

# Определяем константы для времени записи в секундах
PRE_MOTION_RECORD_TIME = mov_in
POST_MOTION_RECORD_TIME = mov_out
FPS = fpsinf # устанавливаем кадры в сек
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')

def video_cap(videos=3): # если нет аргумента - камера id 0
    global stop_video_stream # глобальная переменная
    stop_video_stream = False # Сбрасываем флаг при запуске нового потока
    cap = cv2.VideoCapture(videos)

    if not cap.isOpened():
        print("Ошибка:\nНе удалось открыть видеопоток")
        try:
            bot_instance.send_message(int(userid), "Ошибка:\nНе удалось открыть видеопоток камеры.")
        except Exception as e:
            print(f"Ошибка при отправке сообщения об ошибке камеры:\n{e}")
        return False
    else:
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # Установка разрешения камеры из конфига
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width_conf)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height_conf)
        vide = 'камерa' if str(videos) == '0' else videos # дублируется на всякий
        print(f'Видео запущено из источника: {vide} в {time.strftime("%H:%M:%S")}')
        video_start(cap)
    return True

# ### регулировка работает, но тогда начинает реагировать на шум. + все зависит от камеры смысла кока не вижу
def adjust_brightness(image, target_brightness=brightnes):
    """
    Регулирует яркость изображения, делая ее близкой к целевой.
    Args:
        image: Входное изображение (numpy array).
        target_brightness: Желаемая средняя яркость изображения (по умолчанию 127,
                           середина диапазона 0-255).
    Returns:
        Измененное изображение с регулированной яркостью.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    current_brightness = np.mean(gray)
    brightness_diff = target_brightness - current_brightness
    # Увеличение или уменьшение яркости
    adjusted_image = cv2.convertScaleAbs(image, alpha=1.0, beta=brightness_diff)
    return adjusted_image

# ####
def video_start(cap):
    global stop_video_stream#, video_filename # Используем глобальный флаг

    times = 0
    recording = False
    motion_detected_time = 0
    out = None
    frame_buffer = deque(maxlen=FPS * PRE_MOTION_RECORD_TIME)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Используемое разрешение: {frame_width}x{frame_height}")

    frame_size = (frame_width, frame_height)

    if os.name == 'posix':
        video_base_dir = os.path.expanduser("~/Видео")
    else:
        video_base_dir = f'C:\\video'

    while True:
        # Проверяем флаг остановки в начале каждого цикла
        if stop_video_stream:
            print("Получена команда на остановку видеопотока.")
            break

        ret, frame1 = cap.read()
        ret, frame2 = cap.read()
        #adjusted_frame = adjust_brightness(frame1)

        if not ret:
            print("Видеопоток завершен")
            break

        frame_buffer.append(frame1.copy())
        #frame_buffer.append(adjusted_frame.copy())

        diff = cv2.absdiff(frame1, frame2)
        #diff = cv2.absdiff(adjusted_frame, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)

        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # timestamp_text = datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')
        #cv2.putText(frame1, f"Time: {timestamp_text}",
        #
        #
        ##cv2.putText(adjusted_frame, f"Movement: {timestamp_text}",
        #            (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

        motion_found = False
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)
            if cv2.contourArea(contour) < obj: # реагировать на движения
                continue

            motion_found = True
            timestamp_text = datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')
            #пока закомитим. сокращаем кол-во сообщений в бот так как оказаалось есть лимит
            #info = f"Обнаружен движущийся объект!\n{timestamp_text}"
            #print(info)

            cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 1)
            #cv2.rectangle(adjusted_frame, (x, y), (x+w, y+h), (0, 255, 0), 1)
            cv2.putText(frame1, f"Move: {timestamp_text}",
            #cv2.putText(adjusted_frame, f"Movement: {timestamp_text}",
                        (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA)
            if int(time.time()) > times:
                print(screen_mov(frame1, timestamp_text, bot_instance, userid)) # делаем скрины и передаем их дальше
                times = int(time.time()) + 120 # примерно слать фото только каждые 2 минуты (если есть движение)
            #
            try:
                pass # bot_instance.send_message(int(userid), info=None)
            except Exception as e:
                print(f"Ошибка при отправке сообщения в Telegram: {e}")

        # Запуск конвертации в отдельном процессе в заданное время
        if time.strftime('%H%M') == time_arh: # условия для запуска конвертации
            try:
                p = Process(target=start_conv_video, args=(arh_day,)) # <--- указываем количество дней для архивации
                p.start() # запускаем фунцию
                print("Запущен процесс конвертации видео...")
                time.sleep(61) # Чтобы не запускать процесс каждую секунду в указанную минуту
            except Exception as e:
                print(f"Ошибка при запуске процесса конвертации: {e}")

        if motion_found and not recording:
            recording = True
            video_cam_day_dir = os.path.join(video_base_dir, f"video_{datetime.datetime.now().strftime('%d%m%Y')}")
            if not os.path.exists(video_cam_day_dir):
                os.makedirs(video_cam_day_dir)

            motion_detected_time = time.time()
            video_filename = os.path.join(
                video_cam_day_dir,
                f"motion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            out = cv2.VideoWriter(video_filename, FOURCC, FPS, frame_size)

            for buffered_frame in frame_buffer:
                out.write(buffered_frame)
            print(f"Начало записи видео: {video_filename}")
            # лимитируем сообщения в бот
            #bot_instance.send_message(int(userid), f"Начало записи видео.")
            bot_instance.send_message(int(userid), f"Обнаружен движущийся объект!\n"
                                                  f"Начало записи видео:\n"
                                                  f"{datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y')}")

        if recording:
            out.write(frame1)
            #out.write(adjusted_frame)
            if not motion_found and (time.time() - motion_detected_time) > POST_MOTION_RECORD_TIME:
                recording = False
                out.release()
                out = None
                print(f"Завершение записи видео.\nСохранено:\n{video_filename}")
                #лимитируем сообщения в бот
                #bot_instance.send_message(int(userid), f"Видеозапись завершена!")
            elif motion_found:
                motion_detected_time = time.time()

        cv2.imshow("Motion Detection", frame1) # Экран отображения. Если не нужно можно отключить
        #cv2.imshow(f"Motion Detection", adjusted_frame) # экран с автоматической яркостью
        if cv2.waitKey(1) & 0xFF == ord('q'): #  условия выхода
            break

    cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()
    print("Программа остановлена.")
