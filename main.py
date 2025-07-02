# видеонаблюдение
import cv2
import time
import os
import datetime
from collections import deque
from rec_foto import screen_mov
import configparser
import telebot

# Глобальный флаг для остановки видеопотока
stop_video_stream = False

# Определяем константы для времени записи в секундах
PRE_MOTION_RECORD_TIME = 10
POST_MOTION_RECORD_TIME = 10
FPS = 20 # устанавливаем кадры в сек
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')

# Читаем конфиг из info.ini
config = configparser.ConfigParser()
with open('info.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)

tel_key = config.get('section1', 'tel_bot') # получаем значение бота
userid = config.get('section1', 'userid')  # получаем значение пользователя
bot_instance = telebot.TeleBot(f'{tel_key}') # вводим токен бота в переменную

def video_cap(videos=0):
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
        vide = 'камера' if str(videos) == '0' else videos
        print(f'Видео запущено из источника: {vide} в {time.strftime('%H:%M:%S')} ')
        video_start(cap)
        return True

def video_start(cap):
    global stop_video_stream # Используем глобальный флаг
    times = 0
    recording = False
    motion_detected_time = 0
    out = None
    frame_buffer = deque(maxlen=FPS * PRE_MOTION_RECORD_TIME)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_size = (frame_width, frame_height)


    if os.name == 'posix':
        video_base_dir = f'/home/lives/Видео'
    else:
        video_base_dir = f'C:\\video'

    while True:
        # Проверяем флаг остановки в начале каждого цикла
        if stop_video_stream:
            print("Получена команда на остановку видеопотока.")
            break

        ret, frame1 = cap.read()
        ret, frame2 = cap.read()

        if not ret:
            print("Видеопоток завершен")
            break

        frame_buffer.append(frame1.copy())

        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        motion_found = False
        for contour in contours:
            (x, y, w, h) = cv2.boundingRect(contour)

            if cv2.contourArea(contour) < 1000: # реагировать на движения
                continue

            motion_found = True
            info = f"Обнаружен движущийся объект!\n{time.strftime('%H:%M:%S %d.%m.%Y')}"
            print(info)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (1, 255, 205), 2)
            cv2.putText(frame1, f"Movement", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA)



            if int(time.time()) > times:
                print(screen_mov(frame2, time.strftime('%H%M%S_%d%m%Y'), bot_instance, userid)) # делаем скрины и передаем их дальше
                times = int(time.time()) + 120 # примерно слать фото только каждые 2 минуты (если есть движение)
                try:
                    bot_instance.send_message(int(userid), info)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения в Telegram: {e}")


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
            bot_instance.send_message(int(userid), f"Начало записи видео.")

        if recording:
            out.write(frame1)

            if not motion_found and (time.time() - motion_detected_time) > POST_MOTION_RECORD_TIME:
                recording = False
                out.release()
                out = None
                print(f"Завершение записи видео. Записано:\n{video_filename}")
                bot_instance.send_message(int(userid), f"Видеозапись завершена!")
            elif motion_found:
                motion_detected_time = time.time()

        cv2.imshow("Motion Detection", frame1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    if out is not None:
        out.release()
    cv2.destroyAllWindows()
    print("Программа остановлена.")

