import cv2
import numpy as np
import math

# Функция создания чистого чёрного полотна для траектории
def initPath ( img ):
    h, w = img.shape[:2]
    return np.zeros((h*2,w*2,3), np.uint8)


# Функция разницы двух картинок
def diffImg(t0, t1, t2):
    d1 = cv2.absdiff(t2, t1)
    d2 = cv2.absdiff(t1, t0)
    return cv2.bitwise_and(d1, d2)


# Функция нахождения расстояния
def dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]))


# Функция обрезки картинки
def img_cut(img, settings):
    x = cv2.getTrackbarPos('x0', settings)
    w = cv2.getTrackbarPos('width', settings)
    y = cv2.getTrackbarPos('y0', settings)
    h = cv2.getTrackbarPos('height', settings)
    return img[x:x + w, y:y + h]


def circleIf(newobj, old, color, maxjump, img):
    #print (old, isinstance(old, tuple))
    #print (color, isinstance(color, tuple))
    #print (img, isinstance(img, tuple))

    x = newobj[0]
    y = newobj[1]
    area = newobj[2]
    if 10 < dist(old, (x,y)) < maxjump:# or area > 500:
        cv2.circle(img, (x, y), 10, color, -1)
        old[0] = x
        old[1] = y
        return x, y
    else:
        cv2.circle(img, (old[0], old[1]), 10, color, -1)
    return old


# Функция поиска центра максимального контура на заданной картинке
def find_center(img):
    im, contours, hierarchy = cv2.findContours(img, 1, 2)

    max = 0
    index = 0
    x = 0
    y = 0
    area = 0

    for i in range(0, len(contours)):
        #length = cv2.arcLength(contours[i], True)
        length = cv2.contourArea(contours[i])
        if (length > max):
            max = length
            index = i
    if (index < len(contours)):
        M = cv2.moments(contours[index])
        area = M['m00']
        if (area != 0):
            x = int(M['m10'] / area)
            y = int(M['m01'] / area)

    return (x, y, area)


# Функция обработки изображения по данному фильтру
def img_filter(img, window):

    # Размытие
    blurGauss = cv2.GaussianBlur(img, (3, 3), 0)

    # Преобразуем RGB картинку в HSV модель
    imgHsv = cv2.cvtColor(blurGauss, cv2.COLOR_BGR2HSV)

    # Получение данных с движков настройки
    h1 = cv2.getTrackbarPos('h1', window)
    s1 = cv2.getTrackbarPos('s1', window)
    v1 = cv2.getTrackbarPos('v1', window)
    h2 = cv2.getTrackbarPos('h2', window)
    s2 = cv2.getTrackbarPos('s2', window)
    v2 = cv2.getTrackbarPos('v2', window)

    # формируем начальный и конечный цвет фильтра
    colHSV_Min = np.array((h1, s1, v1), np.uint8)
    colHSV_Max = np.array((h2, s2, v2), np.uint8)

    return cv2.inRange(imgHsv, colHSV_Min, colHSV_Max)


# Функция записи трека:
def print_trace(img, last, path_color):
    first = True
    track = img.copy()
    for i in range(0, len(last)):
        if first:
            first = False
            continue
        cv2.line(track, (last[i-1][0], last[i-1][1]), (last[i][0], last[i][1]), path_color, 1)
    return track


# Функция удаления резких выбросов из трека:
def analizeTrace(tail, max):

    i = 1
    end = len(tail)
    while i<end:
        if dist(tail[i], tail[i-1]) < max*2:
            i = i+1
        else:
            temp = tail[i-1]
            j = i+1
            count = 0
            flag = False
            while j<end and count < 3:
                if dist(temp, tail[j]) < max:
                    flag = True
                count = count + 1
                j = j+1
            if (flag):
                for k in range(i, j):
                    tail.pop(k)
                end = len(tail)
            else:
                i = i+1

        if i == end:
            break
