 # видеонаблюдение адамтировано для минимально потребления трафика с низкой скорость интернета
 # Удаленноая рабоча черет телеграм бот
 # Возможность загрузки файлом на сервер прорабатывается ( неуверен, что это нужно)

import cv2
import time
import os
import datetime




from collections import deque  # Используем deque для буфера кадров
from rec_foto import screen_mov  # Предполагается, что эта функция делает скриншоты


# Определяем константы для времени записи в секундах
PRE_MOTION_RECORD_TIME = 10
POST_MOTION_RECORD_TIME = 10
FPS = 20  # Кадры в секунду для записываемого видео (можно настроить)
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')  # Кодек для сохранения видео (например, 'mp4v' для .mp4)


def video_cap(videos=0):  # получение кадра
    # Открыть видеопоток с камеры (индекс 0)
    cap = cv2.VideoCapture(videos)

    # Проверить, успешно ли открыт видеопоток
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть видеопоток")
        exit()
    else:
        if str(videos) == '0':
            vide = 'камера'
        else:
            vide = videos
        print(f'Видео запущено из источника: {vide} в {time.strftime('%H:%M:%S')} ')
        return video_start(cap)


def video_start(cap):  # работаем с видео
    times = 0
    recording = False  # Флаг для отслеживания состояния записи
    motion_detected_time = 0  # Время, когда было обнаружено движение
    out = None  # Объект для записи видео
    frame_buffer = deque(maxlen=FPS * PRE_MOTION_RECORD_TIME)  # Буфер для хранения кадров до движения

    # Получаем ширину и высоту кадра для настройки VideoWriter
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_size = (frame_width, frame_height)

    while True:
        # Прочитать кадр
        ret, frame1 = cap.read()  # кадр 1
        ret, frame2 = cap.read()  # кадр 2

        if not ret:
            print("Видеопоток завершен")
            break

        # Добавляем текущий кадр в буфер (для записи "до" движения)
        frame_buffer.append(frame1.copy())

        diff = cv2.absdiff(frame1, frame2)  # находим разницу между кадрами
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)  # делаем разницу видео чернобелым для более четкой обработки

        blur = cv2.GaussianBlur(gray, (5, 5), 0)  # фильтрация лишних контуров
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)  # метод для выделения кромки объекта белым цветом
        dilated = cv2.dilate(thresh, None,iterations=3)  # Данный метод противоположен методу erosion(), т.е. эрозии объекта, и расширяет выделенную на предыдущем этапе область
        сontours, _ = cv2.findContours(dilated, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)  # нахождение массива контурных точек

        motion_found = False
        for contour in сontours:
            (x, y, w, h) = cv2.boundingRect(
                contour)  # преобразование массива из предыдущего этапа в кортеж из четырех координат

            if cv2.contourArea(contour) < 700:  # условие при котором площадь выделенного объекта меньше 700 px
                continue

            motion_found = True
            info = f"{time.strftime('%H:%M:%S %d.%m.%Y')} Обнаружен движущийся объект!"
            print(info)
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (1, 255, 205), 2)  # получение прямоугольника из точек кортежа
            cv2.putText(frame1, f"Movement", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1, cv2.LINE_AA)

            # Проверяем, нужно ли сделать скриншот (старый функционал)
            if int(time.time()) > times:
                print(screen_mov(frame2, time.strftime('%H%M%S_%d%m%Y')))
                times = int(time.time()) + 4  # Задержка перед следующим скриншотом


        # --- НАЧАЛО БЛОКА КОДА ДЛЯ ЗАПИСИ ВИДЕО ПРИ ДВИЖЕНИИ ---
        if motion_found and not recording:
            # Движение обнаружено и запись еще не началась
            recording = True
            if os.name == 'posix':
                video_cam = f'/home/lives/Видео/video{datetime.datetime.now().strftime('_%d%m%Y')}' # при необходимости заменить
            else:
                video_cam = f'c:\video\video_{datetime.datetime.now().strftime('%d%m%Y')}'  # при необходимости заменить

            if not os.path.exists(video_cam):  # если нет папки в текущем каталоге
                os.makedirs(video_cam)
            motion_detected_time = time.time()
            #Формируем имя файла для видео
            video_filename = os.path.join(
                video_cam,  # Предполагается, что у вас есть папка 'video'
                f"motion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )
            # Убедимся, что папка для видео существует
            #os.makedirs(os.path.dirname(video_filename) or '.', exist_ok=True)

            # Инициализируем объект для записи видео
            out = cv2.VideoWriter(video_filename, FOURCC, FPS, frame_size)

            # Записываем кадры из буфера (кадры "до" движения)
            for buffered_frame in frame_buffer:
                out.write(buffered_frame)
            print(f"Начало записи видео: {video_filename}")

        if recording:
            # Если идет запись, записываем текущий кадр
            out.write(frame1)  # Записываем кадр с пометкой движения

            # Проверяем, прошло ли достаточно времени после последнего обнаружения движения
            # или с момента начала записи, если движение было продолжительным
            if not motion_found and (time.time() - motion_detected_time) > POST_MOTION_RECORD_TIME:
                # Движения нет и прошло 10 секунд после последнего обнаружения
                # Или просто прошло 10 секунд после того, как движение исчезло
                recording = False
                out.release()  # Завершаем запись видео
                out = None
                print(f"Завершение записи видео. Записано: {video_filename}")
            elif motion_found:
                # Если движение все еще есть, обновляем время последнего обнаружения
                motion_detected_time = time.time()
        # --- КОНЕЦ БЛОКА КОДА ДЛЯ ЗАПИСИ ВИДЕО ПРИ ДВИЖЕНИИ ---

        # Отображение кадра (необязательно, можно убрать для фоновой работы)
        cv2.imshow("Motion Detection", frame1)  # Показываем кадр с выделением движения

        # Нажмите 'q' для выхода из цикла
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Очистка ресурсов при выходе из цикла
    cap.release()
    if out is not None:
        out.release()  # Убедимся, что запись завершена, если цикл прервался во время записи
    cv2.destroyAllWindows()


video_cap()
