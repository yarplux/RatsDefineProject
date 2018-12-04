import cv2
from random import randrange

import os
import numpy as np

import tkinter as tk
from tkinter import messagebox

import math

import shutil
from WindowMgr import WindowMgr

import imgFunctions as imgF
import constants as cs
import config as cfg
import onChgFunctions as ocF

# ИЦИНИАЛИЗАЦИЯ
# ---------------------------------------------------------------------------------------------------------------

tk.Tk().withdraw()

# Для установки активного окна
# (выводить на передний план после диалогов, чтобы приложение реагировало на нажатие кнопок)
window = WindowMgr()

numx, numy = 0, 0
for win in cfg.WE:
    xw = cfg.opt['winX0']+numx*cfg.opt['winW0']
    if "track" in win.name:
        xw = cfg.opt['winX0']
        numx = 0
        numy += 1

    yw = cfg.opt['winY0'] + numy * cfg.opt['winH0']

    cv2.namedWindow(win.name)
    cv2.setMouseCallback(win.name, ocF.chs_obj)
    cv2.moveWindow(win.name, xw, yw)
    cv2.resizeWindow(win.name, cfg.opt['winW0']-20, cfg.opt['winH0'])
    numx += 1

    if "set" in win.name:
        cv2.createTrackbar('delay', win.name, cfg.opt['delay'], cfg.opt['delay_Max'], ocF.on_chg_delay)
        cv2.setTrackbarMin('delay', win.name, 1)
        cfg.delay = cfg.opt['delay']

        cv2.createTrackbar('FrameDelta', win.name, cfg.opt['FrameDelta'], cfg.opt['FrameDelta_Max'], ocF.f)
        cv2.setTrackbarMin('FrameDelta', win.name, 1)

        # 4 бегунка для настройки позиций обрезки кадра
        cv2.createTrackbar('x0', win.name, cfg.opt['x0'], cfg.opt['x0_Max'],
                           lambda x: ocF.on_chg_size('x0', cfg.cxd - x))
        cfg.cxd = cfg.opt['x0']

        cv2.createTrackbar('width', win.name, cfg.opt['width'], cfg.opt['width' + '_Max'],
                           lambda x: ocF.on_chg_size('width', 0))

        cv2.createTrackbar('y0', win.name, cfg.opt['y0'], cfg.opt['y0_Max'],
                           lambda y: ocF.on_chg_size('y0', cfg.cyd - y))
        cfg.cyd = cfg.opt['y0']

        cv2.createTrackbar('height', win.name, cfg.opt['height'], cfg.opt['height' + '_Max'],
                           lambda x: ocF.on_chg_size('height', 0))

        # 6 бегунков для настройки начального и конечного цвета фильтра
        for n in ['h1', 'h2', 's1', 's2', 'v1', 'v2']:
            if n[:1] == 'h':
                size = 179
            else:
                size = 255
            cv2.createTrackbar(n, win.name, cfg.opt[n], size, ocF.on_chg_filter)

        cv2.resizeWindow(win.name, 400, 250)

window.find_window_wildcard("source")


# НАЧАЛО ВЫПОЛНЕНИЯ ОСНОВНОГО ЦИКЛА ПРОГРАММЫ
# ---------------------------------------------------------------------------------------------------------------

flExit = False
# Цикл прокрутки видео заново по кругу до выхода
while not flExit:

    cfg.cap = cv2.VideoCapture(cfg.video_name)

    cv2.createTrackbar('Frame', cfg.WE.set.name, 1, int(cfg.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1, ocF.on_chg_frm)
    cv2.setTrackbarMin('Frame', cfg.WE.set.name, 1)

    time_length = int(cfg.cap.get(cv2.CAP_PROP_FRAME_COUNT)/cfg.opt['FPS'])

#   cv2.createTrackbar('Moment', cfg.WE.source.name, 120, 240, on_chg_s)

    print('Opened video: ' + cfg.video_name
          + '\nVideo Length (from OpenCV and def FPS): '
          + str(time_length // 3600)
          + ' ' + str(time_length % 3600 // 60)
          + ' ' + str(time_length % 60)
          + '\nOpened options file: ' + cfg.options_name)

    ret, img = cfg.cap.read()
    cfg.h, cfg.w = img.shape[:2]
#   h *= 2
#   w *= 2
    img = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)

    cfg.results = [np.zeros((cfg.h, cfg.w, 3), np.uint8) for i in cfg.WE]
    track = cfg.trace = np.zeros((cfg.h, cfg.w, 3), np.uint8)

    cfg.counter = 0

    cfg.cx = 0
    cfg.cy = 0

    length = cfg.cap.get(cv2.CAP_PROP_FRAME_COUNT)
    keys = sorted(cfg.last.keys())
    ellipse_area = []

    start = True

    while not flExit:
        cfg.waiting = False
        for number in range(cv2.getTrackbarPos('FrameDelta', cfg.WE.set.name)):
            ret, img = cfg.cap.read()
            # при достижении последнего фрейма - выход или сначала
            if (not ret) or cfg.counter >= length:
                ret = False
                break

            cfg.results[cfg.WE.source.value] = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)
            cfg.counter += 1

        cv2.setTrackbarPos('Frame', cfg.WE.set.name, cfg.counter)

        # при достижении последнего фрейма - сначала
        if not ret:
            cfg.waiting = True
            ch = 27
        else:
            ch = 0

        try:
            cfg.results[cfg.WE.source.value] = imgF.img_cut(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
            cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
            ocF.frame_exec()

            if start:  # Для первого кадра - нажатие мышкой
                start = False
                cfg.waiting = True
                if cfg.counter == 1:
                    messagebox.showinfo(cs.DIALOG_TITLE_GENERAL, cs.INSTRUCTIONS)

                window.set_foreground()
#               cv2.waitKey()
                cfg.last = {cfg.counter: [cfg.cx, cfg.cy]}
                keys.append(cfg.counter)

            cfg.cx, cfg.cy, area, cnt = imgF.find_center(cfg.results[cfg.WE.resImg.value])

            tar = (cfg.cx, cfg.cy, area, cnt)
            if not any(tar):
                cfg.waiting = True

            if isinstance(cnt, np.ndarray):
                if len(cnt) > 5:
                    ellipse = cv2.fitEllipse(cnt)
                    (elx, ely), (MA, ma), angle = cv2.fitEllipse(cnt)
                    ea = math.pi/4*ma*MA
                    ellipse_area.append(ea)
                    # print(max(MA, ma)/min(MA, ma), angle)
                    cv2.ellipse(cfg.results[cfg.WE.source.value], ellipse, (0, 255, 0), 2)
                    cv2.imshow(cfg.WE.source.name, cfg.results[cfg.WE.source.value])

                    if ea > 6200 or ea < 200:
                        cfg.waiting = True

            if cfg.waiting and not ch == 27:
                ch = 32
            else:
                cfg.last[cfg.counter] = [(cfg.cx + cv2.getTrackbarPos('x0', cfg.WE.set.name)),
                                     (cfg.cy + cv2.getTrackbarPos('y0', cfg.WE.set.name))]

                keys.append(cfg.counter)

                if len(keys) > 1:
                    p2 = cfg.last[keys[-1]]
                    p1 = cfg.last[keys[-2]]
#                   cfg.trace = cfg.results[cfg.WE.plot.value]
                    cv2.line(cfg.trace, (p1[0], p1[1]), (p2[0], p2[1]), (cfg.opt['bT'], cfg.opt['gT'], cfg.opt['rT']), 1)

                cv2.imshow(cfg.WE.track.name, cfg.trace)

        except:
            cfg.cap.release()
            raise

        if not cfg.waiting:
            ch = cv2.waitKey(cfg.delay)

#       32 - пробел, 27 - esc
        if ch == 27:
            if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):
                flExit = True
            elif not ret:
                cfg.cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
                ret, img = cfg.cap.read()
                cfg.counter = 2
                start = True
            else:
                window.set_foreground()

        elif ch == 32:
            cfg.waiting = True
#           uF.analizeTrace(last, 30)
#           track, plot = uF.print_cfg.trace(cfg.trace, last, cfg.counter,
#                                           (opt['bL'], opt['gL'], opt['rL']), opt['FPS'], opt['SpeedDelta'])
#           track, plot = uF.print_cfg.trace(cfg.trace, last, (opt['bL'], opt['gL'], opt['rL']))
#           track = uF.print_cfg.trace(cfg.trace, last, (opt['bL'], opt['gL'], opt['rL']))
            cv2.imshow(cfg.WE.track.name, track)

            ch = cv2.waitKeyEx()
            print(ch)

            while ch == 2555904 or ch == 2424832:
                t = 0

                # -> 2555904
                if ch == 2555904:
                    t = cv2.getTrackbarPos('FrameDelta', cfg.WE.set.name)

                # <- 2424832
                elif ch == 2424832:
                    t = -cv2.getTrackbarPos('FrameDelta', cfg.WE.set.name)

                pos = cv2.getTrackbarPos('Frame', cfg.WE.set.name) + t
                cv2.setTrackbarPos('Frame', cfg.WE.set.name, pos)
                ch = cv2.waitKeyEx()
                print(ch)

            if ch == 27:
                if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):
                    flExit = True
                else:
                    window.set_foreground()

    cfg.cap.release()

fOptions = open('dir_options.txt', 'w')
for key in cfg.topt.keys():
    fOptions.write('#\n'+key + " " + str(cfg.topt[key]) + '\n\n')
fOptions.close()

if messagebox.askyesno(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_TRACK):
    if not os.path.exists(cfg.track_dir):
        os.makedirs(cfg.track_dir)
    ind = str(randrange(10000))
    trackname = cfg.track_dir + 'track_'\
                            + cfg.video_name[cfg.video_name.rfind('/')+1:-4] \
                            + '_' \
                            + ind+'.png'

    retval = cv2.imwrite(trackname, cfg.trace)
    print('Track file:', trackname, 'saved' if retval else 'UNSAVED!')

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

    if not os.path.exists(cfg.options_dir):
        os.makedirs(cfg.options_dir)

    options_name = cfg.options_dir + '/options_' + cfg.video_name[cfg.video_name.rfind('/')+1:-4] + '.txt'

    fOptions = open(options_name, 'w')

    for key in cfg.opt.keys():
        value = cv2.getTrackbarPos(key, cfg.WE.set.name)
        if value > -1:
            fOptions.write('#\n'+key + " " + str(value) + '\n\n')
        else:
            fOptions.write('#\n'+key + " " + str(cfg.opt[key]) + '\n\n')

    fOptions.close()

    print('Saved options file:', options_name)
    if messagebox.askyesno(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_OPTIONS_DEFAULT):
        shutil.copy(options_name, './' + cs.FILE_OPTIONS_DEFAULT)

cv2.destroyAllWindows()
