# Этап 1 - выделение цветом нужного диапозона
# выделение нужной картинки по цветовому диапозону
# обрезка кадра
# как убрать постоянные помехи? (линии отражения)
# выделение контуров
# выделение нужного контура
# выделение трека

# 2.0 - все настройки в файле опций, код структурирован, где-то сокращены необязательные переменные
# удалены методы по разнице кадров

import cv2
import utilFunctions as uF
from enum import Enum

import time
import os
import numpy as np

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ---------------------------------------------------------------------------------------------------------------


def f(x): return x


def chooseObject(event, x, y, flags, param):                                                                            # Функция обработчика нажатия мыши

    global cx, cy, img, mouseDown
    if event == cv2.EVENT_LBUTTONDOWN:
        cx = x
        cy = y
        mouseDown = True
    if event == cv2.EVENT_LBUTTONUP:
        mouseDown = False


# ИЦИНИАЛИЗАЦИЯ
# ---------------------------------------------------------------------------------------------------------------

print('Input filename:')
filename = input()

fOptions = open('options.txt', 'r')
opt = {}
topt = {}
line = fOptions.readline()
while line:
    if line[0] != '#' and line != "\n":
        line = line.split(' ')
        line[1] = line[1].replace('\n','')
        if line[1].isnumeric():
            opt[line[0]] = int(line[1])
        else:
            topt[line[0]] = line[1]
    line = fOptions.readline()
fOptions.close()

print(opt)
print(topt)


class Out(Enum):
    source, resImg, copy, set, track = range(5)


numx, numy = 0, 0
for win in Out:
    xw = opt['x0']+numx*opt['w0']
    if "track" in win.name:
        xw = opt['x0']
        numx = 0
        numy+=1

    yw = opt['y0']+numy*opt['h0']

    cv2.namedWindow(win.name)
    cv2.setMouseCallback(win.name, chooseObject)
    cv2.moveWindow(win.name, xw, yw)
    cv2.resizeWindow(win.name, opt['w0']-20, opt['h0'])
    numx += 1

    if "set" in win.name:
        for n in ['x0', 'width', 'y0', 'height', 'delay']:                                                              # 4 бегунка для настройки обрезки кадра + для задержки кадров
            cv2.createTrackbar(n, win.name, opt[n], opt[n+'_Max'], f)

        for n in ['h1','h2','s1','s2','v1','v2']:                                                                       # 6 бегунков для настройки начального и конечного цвета фильтра
            cv2.createTrackbar(n, win.name, opt[n], 255, f)

        cv2.resizeWindow(win.name, 400, 250)


# НАЧАЛО ВЫПОЛНЕНИЯ ОСНОВНОГО ЦИКЛА ПРОГРАММЫ
# ---------------------------------------------------------------------------------------------------------------

flExit = False
mouseDown = False

# Цикл прокрутки видео заново по кругу до выхода
while not flExit:

    cap = cv2.VideoCapture(filename)
    ret, img = cap.read()

    results = [uF.initPath(img) for i in Out]
    counter = 0
    cx = 0
    cy = 0

    length = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    while not flExit:
        ret, results[Out.source.value] = cap.read()
        counter +=1

        # при достижении последнего фрейма - перезапуск видео
        if (not ret) and counter < length:
            break

        try:
            results[Out.set.value] = uF.imgCut(results[Out.source.value], Out.set.name)                                 # Обрезка кадра
            results[Out.copy.value] = results[Out.set.value].copy()                                                     # Создание копии изображения
            results[Out.resImg.value] = uF.imageFilter(results[Out.set.value], Out.set.name)                            # Наложение фильтров

            if counter == 1:                                                                                            # Для первого кадра - нажатие мышкой
                trace = uF.initPath(results[Out.set.value])
                last = [[cx, cy]]
                cv2.imshow(Out.source.name, results[Out.source.value])
                cv2.waitKey()
                flagFirst = False

            tempx, tempy, area = uF.findMaxCenter(results[Out.resImg.value])                                            # Поиск центра максимального контура в кадре
            cx, cy = uF.circleIf([tempx, tempy, area], [cx, cy], (255, 0, 0), opt['maxjump'], results[Out.copy.value])  # Новое положение круга-метки центра

            for img in Out:                                                                                             # отображение - перерисовка всех окон, кроме окна опций
                if img.name != Out.set.name:
                    cv2.imshow(img.name, results[img.value])
            cv2.imshow(Out.track.name, trace)                                                                           # Дорисовка трека

            if not (cx*2 == last[len(last)-1][0] and cy*2 == last[len(last)-1][1]):                                     # строим линию основного трека, если текущие отвечают условиям
                last.append([cx*2, cy*2])
                cv2.line(trace, (last[len(last)-1][0], last[len(last)-1][1]), (last[len(last)-2][0], last[len(last)-2][1]), (opt['bT'],opt['gT'],opt['rT']), 1)

        except:
            cap.release()
            raise

        cv2.waitKey(cv2.getTrackbarPos('delay', Out.set.name))

    uF.analizeTrace(last, 30)
    track = uF.printTrace(trace, last, (opt['bL'], opt['gL'], opt['rL']))
    cv2.imshow(Out.track.name, track)
    cv2.imwrite(topt['trackFile'], track)
    cv2.waitKey()
    flExit = True
    cap.release()

cv2.destroyAllWindows()