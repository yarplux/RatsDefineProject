import cv2
import config as cfg
import imgFunctions as imgF


def f(x):
    return x


def on_chg_delay(x):
    cfg.delay = x
    return x


def on_chg_filter(x):
    if cfg.waiting:
        cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
        frame_exec()


def on_chg_size(direction, x):

    if direction == 'x0':
        cfg.cx = cfg.cx + x
        cfg.cxd = cfg.cxd - x

    if direction == 'y0':
        cfg.cy = cfg.cy + x
        cfg.cyd = cfg.cyd - x

    if cfg.waiting:
        cfg.cap.set(cv2.CAP_PROP_POS_FRAMES, cfg.counter)
        ret, img = cfg.cap.read()
        img = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)

        cfg.results[cfg.WE.source.value] = imgF.img_cut(img, cfg.WE.set.name)
        cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
        frame_exec()


def on_chg_frm(x):
    if cfg.waiting:
        cv2.setTrackbarPos('Hours', cfg.WE.set.name, int(cfg.counter / cfg.opt['FPS']) // 3600)
        cv2.setTrackbarPos('Min', cfg.WE.set.name, int(cfg.counter / cfg.opt['FPS']) % 3600 // 60)
        cv2.setTrackbarPos('Sec', cfg.WE.set.name, int(cfg.counter / cfg.opt['FPS']) % 60)

        cfg.counter = x
        cfg.cap.set(cv2.CAP_PROP_POS_FRAMES, x)
        ret, img = cfg.cap.read()
        img = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)

        cfg.results[cfg.WE.source.value] = imgF.img_cut(img, cfg.WE.set.name)
        cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)

        frame_exec()


def on_chg_s(x):
    if cfg.waiting:
        cfg.counter = cfg.counter + (x - 120)
        cfg.cap.set(cv2.CAP_PROP_POS_FRAMES, cfg.counter)

        ret, img = cfg.cap.read()
        img = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)

        cfg.results[cfg.WE.source.value] = imgF.img_cut(img, cfg.WE.set.name)
        cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
        frame_exec()


# Функция обработчика нажатия мыши
def chs_obj(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cfg.drawing = True
        cfg.cx = x
        cfg.cy = y
        if cfg.waiting:
            frame_exec()
    elif event == cv2.EVENT_MOUSEMOVE:
        if cfg.drawing:
            cfg.cx = x
            cfg.cy = y
            if cfg.waiting:
                cfg.cap.set(cv2.CAP_PROP_POS_FRAMES, cfg.counter)
                ret, img = cfg.cap.read()
                img = cv2.resize(img, (cfg.w, cfg.h), interpolation=cv2.INTER_CUBIC)

                cfg.results[cfg.WE.source.value] = imgF.img_cut(img, cfg.WE.set.name)
                cfg.results[cfg.WE.resImg.value] = imgF.img_filter(cfg.results[cfg.WE.source.value], cfg.WE.set.name)
                frame_exec()
    elif event == cv2.EVENT_LBUTTONUP:
        cfg.drawing = False
#       cv2.setTrackbarPos('Moment', cfg.WE.source.name, 120)


def frame_exec():

    if not (cfg.cx == 0 and cfg.cy == 0):
        cv2.circle(cfg.results[cfg.WE.source.value], (cfg.cx, cfg.cy), 10, (255, 0, 0), -1)

    # отображение - перерисовка всех окон, кроме окна опций
    for img in [cfg.WE.source, cfg.WE.resImg]:
        cv2.imshow(img.name, cfg.results[img.value])

    # Дорисовка трека
    cv2.imshow(cfg.WE.track.name, cfg.trace)
