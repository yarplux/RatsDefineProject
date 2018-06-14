# Этап 1 - выделение цветом нужного диапозона
# выделение нужной картинки по цветовому диапозону
# обрезка кадра
# как убрать постоянные помехи? (линии отражения)
# выделение контуров
# выделение нужного контура
# выделение трека

import numpy as np
import cv2
import os
import utilFunctions as uF
from enum import Enum


class Out(Enum):
    #source, resImg, ed, resDiff, edDiff, copy, resMark, edMark, resDiffMark, edDiffMark, track, settOrigin, settDiff, setGeneral = range(14)
    #source, resImg, resDiff, copy, resMark, resDiffMark, track, settOrigin, settDiff, setGeneral = range(10)
    #source, resImg, resDiff, copy, resMark, resDiffMark, track, settOrigin, setGeneral = range(9)
    source, resImg, resDiff, copy, track, settOrigin, setGeneral = range(7)

def f(x): return x


# Функция обработчика нажатия мыши
def chooseObject(event, x, y, flags, param):
    global coord, img, mouseDown
    if event == cv2.EVENT_LBUTTONDOWN:
        for i in coord:
            i[0] = x
            i[1] = y
        mouseDown = True
    if event == cv2.EVENT_LBUTTONUP:
        mouseDown = False


numx = 0
numy = 0

x0 = 20
y0 = 20
w0 = 350
h0 = 280



# 6 бегунков для настройки начального и конечного цвета фильтра
hsvList = [0, 73, 185, 255, 97, 255]
nameList = ['h1','s1','v1','h2','s2','v2']

# 4 бегунка для настройки обрезки кадра + для задержки кадров
coordList = [[16,120], [300,300], [30,120], [275,300], [1,1000]]
nameCoordList = ['x0', 'width', 'y0', 'height', 'delay']

for win in Out:
    xw = x0+numx*w0
    #if xw > 1500:
    if xw > 1000:
        xw = x0
        numx = 0
        numy+=1

    yw = y0+numy*h0

    cv2.namedWindow(win.name)
    cv2.setMouseCallback(win.name, chooseObject)
    cv2.moveWindow(win.name, xw, yw)
    cv2.resizeWindow(win.name, w0-20, h0)
    numx += 1

    if "sett" in win.name:
        cv2.resizeWindow(win.name, 550, 300)
        i = 0
        for num in hsvList:
            cv2.createTrackbar(nameList[i], win.name, num, 255, f)
            i = i + 1

    if "General" in win.name:
        i = 0
        for n in coordList:
            cv2.createTrackbar(nameCoordList[i], win.name, n[0], n[1], f)
            i = i+1


# Создаём объект для захвата кадров из видео
print('Input filename:')
filename = input()

flExit = False
mouseDown = False
# Цикл прокрутки видео заново по кругу до выхода
while not flExit:

    delta = 3
    diff = 0
    imgs = [0 for i in range (3)]
    indImg = 0
    flag = False
    flagFirst = True

    # Вывод в цикле
    # абсолютный cчётчик фреймов
    counter = 0

    # максимальный "скачок" точки отмечающей положение крысы за 1 кадр
    maxjump = 100

    path_color = (255, 0, 0)

    cap = cv2.VideoCapture(filename)
    ret, img = cap.read()
    results = [uF.initPath(img) for i in Out]
    # создаём массив координат, по которым будет отслеживаться крыса для всех вариантов
    # resImg, resDiffImg
    # x y для каждой
    coord = [[0, 0], [0, 0]]

    while not flExit:
        # Захват текущего кадра
        ret, results[Out.source.value] = cap.read()
        counter +=1

        # при достижении последнего фрейма - перезапуск видео
		
		#print(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if not ret:
            break
        #    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        try:
            # Модификации кадра__________________________
            # Обрезка копии кадра
            results[Out.settOrigin.value] = uF.imgCut(results[Out.source.value], Out.setGeneral.name)
            results[Out.copy.value] = results[Out.settOrigin.value].copy()

            # Захват разницы кадров

            if counter%delta == 0:
                imgs[indImg] = uF.imageFilter(results[Out.source.value], Out.settOrigin.name)
                indImg = indImg + 1
                if indImg == 3:
                    results[Out.resDiff.value] = uF.diffImg(imgs[indImg - 3], imgs[indImg - 2], imgs[indImg - 1])
                    imgs[indImg - 3] = imgs[indImg - 2]
                    imgs[indImg - 2] = imgs[indImg - 1]
                    indImg = 2
                    flag = True

            if counter == 1:
                trace = uF.initPath(results[Out.settOrigin.value])

            if flag:
                results[Out.resImg.value] = uF.imageFilter(results[Out.settOrigin.value], Out.settOrigin.name)

                if flagFirst:
                    # Для "первого" кадра - нажимается мышкой
                    # coord[0][0], coord[0][1], area = uF.findMaxCenter(results[Out.resImg.value])
                    # coord[1][0], coord[1][1], area = uF.findMaxCenter(results[Out.resDiff.value])
                    last = [coord[0]]
                    cv2.imshow(Out.source.name, results[Out.source.value])
                    cv2.waitKey()
                    flagFirst = False

                #results[Out.resMark.value] = results[Out.resImg.value].copy()
                tempx, tempy, area = uF.findMaxCenter(results[Out.resImg.value])
                x, y = uF.circleIf([tempx, tempy, area], coord[0], (255, 0, 0), maxjump, results[Out.copy.value])
                #uF.circleIf([tempx, tempy], coord, 0, maxjump, results[Out.resMark.value])

                #results[Out.resDiffMark.value] = results[Out.resDiff.value].copy()
                tempx, tempy, area = uF.findMaxCenter(results[Out.resDiff.value])
                uF.circleIf([tempx, tempy, area], coord[1], (0, 0, 255), maxjump, results[Out.copy.value])
                #uF.circleIf([tempx, tempy], coord, 1, maxjump, results[Out.resDiffMark.value])

                # отображение
                outList = [[i.name, i.value] for i in Out]
                for i in range (0, Out.track.value):
                    cv2.imshow(outList[i][0], results[outList[i][1]])
                cv2.imshow(Out.track.name, trace)

                #print (len(last)-1, x*2, last[len(last)-1][0], y*2, last[len(last)-1][1])
                if not (x*2 == last[len(last)-1][0] and y*2 == last[len(last)-1][1]):
                    last.append([x*2, y*2])
                    cv2.line(trace, (last[len(last)-1][0], last[len(last)-1][1]), (last[len(last)-2][0], last[len(last)-2][1]), path_color, 1)
        except:
            cap.release()
            raise

        s = cv2.getTrackbarPos('delay',Out.setGeneral.name)
        ch = cv2.waitKey(s)
        if ch == 32:
            ch = cv2.waitKey()
            if (ch == 13):
                #os.mkdir('temptrack')
                #cv2.imwrite('./img.png', results[Out.source.value])
                cv2.imwrite('./resImg.png', results[Out.resImg.value])
                break
        if ch == 27:
            flExit = True

    uF.analizeTrace(last, 30)
    track = uF.printTrace(trace, last, (255, 255, 255))
    cv2.imshow('Track', track)
    cv2.imwrite('./track.png', track)
    cv2.waitKey()
    cap.release()

cv2.destroyAllWindows()