import cv2
from enum import Enum
from random import randrange

import os
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import math

import shutil
from WindowMgr import WindowMgr

import utilFunctions as uF
import constants as cs

# Глобальные переменные для обработчиков событий (необязательная инициализация, просто определённые имена в одном месте)
# ---------------------------------------------------------------------------------------------------------------
cx = 0                      # global mouse/track x position
cxd = 0                     # global track x position change by trackbar
cy = 0                      # global mouse/track x position
cyd = 0                     # global track x position change by trackbar
delay = 0
drawing = False             # true if mouse is pressed
waiting = False             # true if waitKey()

window = WindowMgr()        # для установки активного окна - выводить на передний план после диалогов, чтобы приложение реагировало на нажатие кнопок
last = {}


class WE(Enum):
    # TODO добавить plot - для построения графика
    source, resImg, set, track = range(4)


# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ---------------------------------------------------------------------------------------------------------------
def on_chg_delay(x):
    global delay
    delay = x
    return x


def on_chg_filter(x):
    global results
    if waiting:
        results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)
        frame_exec()


def on_chg_frm(x):
    global cap, waiting, results, counter
    if waiting:
        cv2.setTrackbarPos('Hours', WE.set.name, int(counter / opt['FPS']) // 3600)
        cv2.setTrackbarPos('Min', WE.set.name, int(counter / opt['FPS']) % 3600 // 60)
        cv2.setTrackbarPos('Sec', WE.set.name, int(counter / opt['FPS']) % 60)

        counter = x
        cap.set(cv2.CAP_PROP_POS_FRAMES, x)
        ret, img = cap.read()
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

        results[WE.source.value] = uF.img_cut(img, WE.set.name)
        results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)

        frame_exec()


def on_chg_s(x):
    global cap, waiting, results, counter
    if waiting:
        counter = counter + (x - 120)
        cap.set(cv2.CAP_PROP_POS_FRAMES, counter)

        ret, img = cap.read()
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

        results[WE.source.value] = uF.img_cut(img, WE.set.name)
        results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)
        frame_exec()


def on_chg_size(dir, x):
    global results, counter, cx, cxd, cy, cyd

    if dir == 'x0':
        cx = cx + x
        cxd = cxd - x

    if dir == 'y0':
        cy = cy + x
        cyd = cyd - x

    if waiting:
        cap.set(cv2.CAP_PROP_POS_FRAMES, counter)
        ret, img = cap.read()
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

        results[WE.source.value] = uF.img_cut(img, WE.set.name)
        results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)
        frame_exec()


def f(x):
    return x


# Функция обработчика нажатия мыши
def chs_obj(event, x, y, flags, param):
    global cx, cy, drawing, counter, results
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        cx = x
        cy = y
        if waiting:
             frame_exec()
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            cx = x
            cy = y
            if waiting:
                cap.set(cv2.CAP_PROP_POS_FRAMES, counter)
                ret, img = cap.read()
                img = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)

                results[WE.source.value] = uF.img_cut(img, WE.set.name)
                results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)
                frame_exec()
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        #cv2.setTrackbarPos('Moment', WE.source.name, 120)


def frame_exec():
    global results, WE, trace, cx, cy

    if not (cx == 0 and cy == 0):
        cv2.circle(results[WE.source.value], (cx, cy), 10, (255, 0, 0), -1)

    # отображение - перерисовка всех окон, кроме окна опций
    for img in [WE.source, WE.resImg]:
        cv2.imshow(img.name, results[img.value])

    # Дорисовка трека
    cv2.imshow(WE.track.name, trace)


# ИЦИНИАЛИЗАЦИЯ
# ---------------------------------------------------------------------------------------------------------------
root = tk.Tk()
root.withdraw()

fOptions = open(cs.FILE_OPTIONS_FOLDER, 'r')
topt = {}
line = fOptions.readline()
while line:
    if line[0] != '#' and line != "\n":
        topt[line[:line.find(' ')]] = line[line.find(' '):]
    line = fOptions.readline()
fOptions.close()

print('Last video folder:', topt['last_video'])
video_name = filedialog.askopenfilename(initialdir=topt['last_video'],
                                        title=cs.DIALOG_TITLE_OPEN_VIDEO,
                                        filetypes=(("video files", "*.avi *.mp4"), ("all files", "*.*")))

topt['last_video'] = video_name[:video_name.rfind('/')]

if video_name == '':
    messagebox.showinfo(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_ERROR_OPEN_FILE)
    exit()

options_dir = video_name[:video_name.rfind('/')] + cs.DIR_OPTIONS
track_dir = video_name[:video_name.rfind('/')] + cs.DIR_TRACKS

options_name = options_dir + '/options_' + video_name[video_name.rfind('/')+1:-4] + '.txt'
if not (os.path.exists(options_dir) and os.path.isfile(options_name)):
        options_name = cs.FILE_OPTIONS_DEFAULT


fOptions = open(options_name, 'r')
opt = {}
line = fOptions.readline()
while line:
    if line[0] != '#' and line != "\n":
        line = line.split(' ')
        line[1] = line[1].replace('\n', '')
        if line[1].isnumeric():
            opt[line[0]] = int(line[1])
    line = fOptions.readline()
fOptions.close()


numx, numy = 0, 0
for win in WE:
    xw = opt['winX0']+numx*opt['winW0']
    if "track" in win.name:
        xw = opt['winX0']
        numx = 0
        numy += 1

    yw = opt['winY0'] + numy * opt['winH0']

    cv2.namedWindow(win.name)
    cv2.setMouseCallback(win.name, chs_obj)
    cv2.moveWindow(win.name, xw, yw)
    cv2.resizeWindow(win.name, opt['winW0']-20, opt['winH0'])
    numx += 1

    if "set" in win.name:
        cv2.createTrackbar('delay', win.name, opt['delay'], opt['delay_Max'], on_chg_delay)
        cv2.setTrackbarMin('delay', win.name, 1)
        delay = opt['delay']

        cv2.createTrackbar('FrameDelta', win.name, opt['FrameDelta'], opt['FrameDelta_Max'], f)
        cv2.setTrackbarMin('FrameDelta', win.name, 1)

        # 4 бегунка для настройки позиций обрезки кадра
        for n in ['width', 'height']:
            cv2.createTrackbar(n, win.name, opt[n], opt[n + '_Max'], lambda x: on_chg_size(n, 0))

        cv2.createTrackbar('x0', win.name, opt['x0'], opt['x0_Max'], lambda x: on_chg_size('x0', cxd-x))
        cxd = opt['x0']

        cv2.createTrackbar('y0', win.name, opt['y0'], opt['y0_Max'], lambda y: on_chg_size('y0', cyd - y))
        cyd = opt['y0']

        # 6 бегунков для настройки начального и конечного цвета фильтра
        for n in ['h1', 'h2', 's1', 's2', 'v1', 'v2']:
            if n[:1] == 'h':
                size = 179
            else:
                size = 255
            cv2.createTrackbar(n, win.name, opt[n], size, on_chg_filter)

        cv2.resizeWindow(win.name, 400, 250)

window.find_window_wildcard("source")

# НАЧАЛО ВЫПОЛНЕНИЯ ОСНОВНОГО ЦИКЛА ПРОГРАММЫ
# ---------------------------------------------------------------------------------------------------------------

flExit = False
# Цикл прокрутки видео заново по кругу до выхода
while not flExit:

    cap = cv2.VideoCapture(video_name)

    cv2.createTrackbar('Frame', WE.set.name, 1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT))-1, on_chg_frm)
    cv2.setTrackbarMin('Frame', WE.set.name, 1)

    time_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)/opt['FPS'])

    #cv2.createTrackbar('Moment', WE.source.name, 120, 240, on_chg_s)

    print('Opened video: ' + video_name
          + '\nVideo Length (from OpenCV and def FPS): '
          + str(time_length // 3600)
          + ' ' + str(time_length % 3600 // 60)
          + ' ' + str(time_length % 60)
          + '\nOpened options file: ' + options_name)

    ret, img = cap.read()
    h, w = img.shape[:2]
    #h *= 2
    #w *= 2
    img = cv2.resize(img, (w, h), interpolation = cv2.INTER_CUBIC)

    results = [np.zeros((h, w, 3), np.uint8) for i in WE]
    track = trace = np.zeros((h, w, 3), np.uint8)

    counter = 0

    cx = 0
    cy = 0

    length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    keys = sorted(last.keys())
    ellipse_area = []

    start = True

    while not flExit:
        waiting = False
        for number in range(cv2.getTrackbarPos('FrameDelta', WE.set.name)):
            ret, img = cap.read()
            results[WE.source.value] = cv2.resize(img, (w, h), interpolation=cv2.INTER_CUBIC)
            counter += 1

        cv2.setTrackbarPos('Frame', WE.set.name, counter)

        # при достижении последнего фрейма - сброс на паузу
        if (not ret) or counter >= length:
            flExit = True
            break

        ch = 0
        try:
            results[WE.source.value] = uF.img_cut(results[WE.source.value], WE.set.name)
            results[WE.resImg.value] = uF.img_filter(results[WE.source.value], WE.set.name)
            frame_exec()

            if start:  # Для первого кадра - нажатие мышкой
                start = False
                waiting = True
                messagebox.showinfo(cs.DIALOG_TITLE_GENERAL, cs.INSTRUCTIONS)
                window.set_foreground()
                cv2.waitKey()
                last = {counter: [cx, cy]}
                keys.append(counter)

            #cx, cy, area, cnt = uF.find_center(results[WE.resImg.value])
            cx, cy, area = uF.find_center(results[WE.resImg.value])

            # if cx == 0 and cy == 0 and area == 0 and cnt == 0:
            #     waiting = True
            #
            # if isinstance(cnt, np.ndarray):
            #     if len(cnt) > 5:
            #         ellipse = cv2.fitEllipse(cnt)
            #         (elx, ely), (MA, ma), angle = cv2.fitEllipse(cnt)
            #         ea = math.pi/4*ma*MA
            #         ellipse_area.append(ea)
            #         # print(max(MA, ma)/min(MA, ma), angle)
            #         cv2.ellipse(results[WE.source.value], ellipse, (0, 255, 0), 2)
            #         cv2.imshow(WE.source.name, results[WE.source.value])
            #
            #         if ea > 6200 or ea < 200:
            #             waiting = True

            if waiting:
                ch = 32
            else:
                last[counter] = [(cx + cv2.getTrackbarPos('x0', WE.set.name)),
                                 (cy + cv2.getTrackbarPos('y0', WE.set.name))]

                keys.append(counter)

                if len(keys) > 1:
                    #trace = results[WE.plot.value]
                    p2 = last[keys[-1]]
                    p1 = last[keys[-2]]
                    cv2.line(trace, (p1[0], p1[1]), (p2[0], p2[1]), (opt['bT'], opt['gT'], opt['rT']), 1)

                cv2.imshow(WE.track.name, trace)

        except:
            cap.release()
            raise

        if not waiting:
            ch = cv2.waitKey(delay)


        # 32 - пробел, 27 - esc
        if ch == 27:
            if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):
                flExit = True
            else:
                window.set_foreground()

        elif ch == 32:
            waiting = True
            # uF.analizeTrace(last, 30)
            #track, plot = uF.print_trace(trace, last, counter, (opt['bL'], opt['gL'], opt['rL']), opt['FPS'], opt['SpeedDelta'])
            #track, plot = uF.print_trace(trace, last, (opt['bL'], opt['gL'], opt['rL']))
            #track = uF.print_trace(trace, last, (opt['bL'], opt['gL'], opt['rL']))
            cv2.imshow(WE.track.name, track)
            ch = cv2.waitKey()

            if ch == 27:
                if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):
                    flExit = True
                else:
                    window.set_foreground()

    cap.release()

fOptions = open('dir_options.txt', 'w')
for key in topt.keys():
    fOptions.write('#\n'+key + " " + str(topt[key]) + '\n\n')
fOptions.close()

if messagebox.askyesno(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_TRACK):
    if not os.path.exists(track_dir):
        os.makedirs(track_dir)
    ind = str(randrange(10000))
    trackname = track_dir + 'track_' \
                                   + video_name[video_name.rfind('/')+1:-4] \
                                   + '_' \
                                   + ind+'.png'

    retval = cv2.imwrite(trackname, trace)
    print('Track file:', trackname, 'saved' if (retval == True) else 'UNSAVED!')

    # TODO test speed
    # plotname = track_dir + 'track_' \
    #            + video_name[video_name.rfind('/') + 1:-4] \
    #            + '_' \
    #            + ind + '.txt'
    #
    # fOptions = open(plotname, 'w')
    # for point in sorted(plot.keys()):
    #     time = str(int(point / opt['FPS']) // 3600)\
    #            + ':' + str(int(point / opt['FPS']) % 3600 // 60)\
    #            + ':' + str(int(point / opt['FPS']) % 60)
    #
    #     speed = str(plot.get(point))\
    #         .replace('.', ',')\
    #         .replace('[', '')\
    #         .replace(']', '')
    #
    #     fOptions.write(time + '\t' + speed + '\n')

    # TODO test ellipse area
    # for s in ellipse_area:
    #     fOptions.write(str(s)+'\n')

    fOptions.close()

    # print('Saved speed plot:', plotname)

if messagebox.askyesno(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_OPTIONS):

    if not os.path.exists(options_dir):
        os.makedirs(options_dir)

    options_name = options_dir + 'options_' + video_name[video_name.rfind('/')+1:-4] + '.txt'

    fOptions = open(options_name, 'w')

    for key in opt.keys():
        value = cv2.getTrackbarPos(key, WE.set.name)
        if value > -1:
            fOptions.write('#\n'+key + " " + str(value) + '\n\n')
        else:
            fOptions.write('#\n'+key + " " + str(opt[key]) + '\n\n')

    fOptions.close()

    print('Saved options file:', options_name)
    if messagebox.askyesno(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_OPTIONS_DEFAULT):
        shutil.copy(options_name, './'+cs.FILE_OPTIONS_DEFAULT)

cv2.destroyAllWindows()
