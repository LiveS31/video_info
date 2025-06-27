# делаем фотки каждые 5 секунд при движении
import os
import cv2



# делаем screen по двидению
def screen_mov(frame, times): #
    screenshot_dir=f"/home/lives/Изображения/mot_pic{times[6:]}"
    if not os.path.exists(screenshot_dir): # если нет папки в текущем каталоге
        os.makedirs(screenshot_dir) # - создаем ее

    #time # получаем время создание скрина
    filename = os.path.join(screenshot_dir, f"foto_detect_{times}.jpg")
    cv2.imwrite(filename, frame) # Сохраняем весь кадр как картинку

    return f"Сохранен скрин: foto_detect_{times}.jpg"