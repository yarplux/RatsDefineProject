import tkinter as tk
from tkinter import messagebox

import cv2
import os
import PIL.Image
import PIL.ImageTk
import time
import numpy as np

import constants as cs
import config as cfg
import imgFunctions as imgF


#
# Widget wrapper classes ===============================================================================================
#
class MyEntry(object):
    init = False

    def __init__(self, my_parent, my_list, my_callback, index, side):
        self.i = index
        self.function = my_callback
        self.my_list = my_list

        self.var = tk.StringVar()
        self.var.trace("w", lambda name, i, mode, sv=self.var: self.callback(sv))
        self.entry = tk.Entry(my_parent, font="Helvetica 16", width=50, textvariable=self.var)
        self.entry.pack(side=side)

        if my_list[self.i] == '':
            self.init = True
        else:
            self.entry.insert(tk.END, my_list[self.i])

    def callback(self, x):
        if self.init:
            self.my_list[self.i] = x.get()
            self.function()
        self.init = True


class MySlider(object):
    init = False

    def __init__(self, my_parent, my_min, my_list, my_callback, name):
        self.name = name
        self.function = my_callback
        self.min = my_min
        self.slider = tk.Scale(my_parent,
                               from_=my_min, to=my_list[name + "_Max"], label=cfg.labels[name],
                               orient=tk.HORIZONTAL, length=300,
                               command=self.callback)
        self.slider.pack()

        if my_list[name] == my_min:
            self.init = True
        else:
            self.slider.set(my_list[name])

    def callback(self, x):
        if self.init:
            self.function(x, self.name)
        self.init = True


class MyButton(object):
    def __init__(self, my_parent, my_text, my_callback, side):
        self.function = my_callback
        self.name = my_text
        self.button = tk.Button(my_parent, text=my_text, padx=3, command=self.callback)
        self.button.pack(side=side)

    def callback(self):
        self.function(self.name, self.button)


#
# Window wrapper classes ===============================================================================================
#
class Win:
    def __init__(self, window, window_title, maximize):
        self.window = window
        self.window.title(window_title)
        if maximize:
            self.window.state("zoomed")
        else:
            self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.quit)

    def quit(self):
        self.window.destroy()


class WinHelp(Win):
    def __init__(self, window, window_title, widget):
        Win.__init__(self, window, window_title, False)
        self.widget = widget
        self.widget.config(state='disabled')

        self.T = tk.Text(self.window, width=85, height=15)
        self.T.pack()
        self.T.insert(tk.END, cs.INSTRUCTIONS)
        self.window.mainloop()

    def quit(self):
        self.widget.config(state='active')
        Win.quit(self)


class MyVideo:
    vid = cv2.VideoCapture()
    counter = 0
    frame = np.zeros((0, 0, 3), np.uint8)

    def __init__(self, video_source=''):
        self.vid = cv2.VideoCapture(video_source)
        self.length = self.vid.get(cv2.CAP_PROP_FRAME_COUNT)

        if self.vid.isOpened():
            ret, MyVideo.frame = self.vid.read()
            MyVideo.frame = cv2.cvtColor(MyVideo.frame, cv2.COLOR_BGR2RGB)
        else:
            raise ValueError("Unable to open video source", video_source)

        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            MyVideo.counter += cfg.opt_process['FrameDelta']
            if MyVideo.counter >= self.length:
                MyVideo.counter = 0

            self.vid.set(cv2.CAP_PROP_POS_FRAMES, MyVideo.counter)
            ret, frame = self.vid.read()
            if ret:
                MyVideo.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            return ret, MyVideo.frame
        else:
            return False, None

    def set_frame(self, x, flag):
        if flag:
            self.vid.set(cv2.CAP_PROP_POS_FRAMES, x)
            ret, frame = self.vid.read()
            if ret:
                MyVideo.frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            MyVideo.counter = x

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()


#
# MAIN WINDOW CLASS ====================================================================================================
#
class MainWindow(Win):
    sliders = {}
    lines = {}
    tc = list()
    ti = list()

    active, paused, settings_state, settings_gen_state = True, True, True, True
    drawing, choosing = False, False
    tr, si, fi = None, None, None


#
# Initialization________________________________________________________________________________________________________
#
    def __init__(self, window=tk.Tk(), window_title='Наблюдение за крысами 2.0'):
        Win.__init__(self, window, window_title, True)

        cfg.init_gen_options()
        while not cfg.init_options():
            if not messagebox.askyesno(cs.DIALOG_TITLE_OPEN_VIDEO, cs.DIALOG_TEXT_ANOTHER):
                exit()

        self.window.focus_force()
        self.window.bind('<space>', self.pause)
        self.window.bind('<Escape>', self.my_exit)

        # Init Main Menu
        self.frame_menu = tk.Frame(self.window)
        self.frame_menu.pack(fill=tk.X, side=tk.TOP, padx=3, pady=3)

        self.menu = ['Помощь', 'Открыть другое видео', 'Сохранить общие настройки', 'Сохранить настройки видео']
        self.menu_functions = [self.help, self.reload, self.save_gen_settings, self.save_settings]

        for i in range(len(self.menu)):
            MyButton(self.frame_menu, self.menu[i], self.menu_functions[i], tk.LEFT)
            if self.menu[i].__contains__('Сохранить'):
                self.frame_menu.winfo_children()[i].config(state='disabled')

        tk.Frame(self.window, bg='black').pack(fill=tk.X, side=tk.TOP)

        # Init Settings
        self.frame_settings = tk.Frame(self.window)
        self.frame_settings.pack(fill=tk.Y, side=tk.RIGHT)

        frame = tk.Frame(self.frame_settings, bg="black")
        frame.pack(fill=tk.Y, pady=5, side=tk.LEFT)

        self.init_slider(cfg.opt_process, 1, self.ch_proc)
        tk.Frame(self.frame_settings, height=2, bg="black").pack(fill=tk.X, pady=5)
        tk.Label(self.frame_settings, text="Настройки видео:", font=("Helvetica", 16, 'bold')).pack()

        for v in ([cfg.opt_filters, 0, self.ch_filt],
                  [cfg.opt_size, 1, self.ch_win]):
            self.init_slider(v[0], v[1], v[2])
            tk.Frame(self.frame_settings, height=2, bg="black").pack(fill=tk.X, pady=5)

        tk.Label(self.frame_settings, text="Выбор областей:", font=("Helvetica", 16, 'bold')).pack()

        self.MODES = ['Время', 'Кормушка', 'Поилка', 'Центр']

        v = tk.StringVar()
        v.set(0)

        for text in self.MODES:
            b = tk.Radiobutton(self.frame_settings, text=text, variable=v, value=self.MODES.index(text), indicatoron=0)
            b.pack(anchor=tk.W, fill=tk.X, padx=10, pady=3)

        tk.Button(self.frame_settings, text="Зафиксировать", command=lambda ind=int(v.get()): self.choose_area(ind))\
            .pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10)

        # Init Video Frame
        self.vid = MyVideo(cfg.video_name)

        # Create a canvas that can fit the above video source size
        self.frame_main = tk.Frame(self.window)
        self.frame_main.pack(side=tk.TOP)

        self.canvas_source = tk.Canvas(self.frame_main, width=self.vid.width, height=self.vid.height)
        self.canvas_filtered = tk.Canvas(self.frame_main, width=self.vid.width, height=self.vid.height)
        self.canvas_source.pack(side=tk.LEFT)
        self.canvas_filtered.pack(side=tk.RIGHT)

        for canvas in [self.canvas_source, self.canvas_filtered]:
            canvas.bind('<ButtonPress-1>', self.draw)
            canvas.bind('<B1-Motion>', self.draw)

        self.canvas_source.bind('<ButtonPress-3>', self.choose_start)
        self.canvas_source.bind('<B3-Motion>', self.choose)

        frame = tk.Frame(self.window)
        frame.pack(fill=tk.X)
        self.slider = tk.Scale(frame, label='Текущий кадр',
                               from_=1, to=self.vid.length, orient=tk.HORIZONTAL,
                               command=lambda x, flag=self.paused: self.vid.set_frame(int(x), flag))

        self.slider.pack(fill=tk.X)
        tk.Frame(frame, bg="black").pack(fill=tk.X, pady=5)

        cfg.cx = 0
        cfg.cy = 0

        # Init Actions
        frame.pack(side=tk.LEFT, fill=tk.Y)
        self.frame_actions = tk.Frame(frame)
        self.frame_actions.pack(side=tk.TOP)

        tk.Button(self.frame_actions, text="Новое действие", command=self.action_create).pack(side=tk.TOP)

        for i in cfg.actions.keys():
            self.lines[i] = tk.Frame(self.frame_actions)
            self.lines[i].pack(side=tk.BOTTOM)
            self.action_init(i)

        self.update()
        self.window.mainloop()

#
# Settings functions____________________________________________________________________________________________________
#
    def new_settings(self):
        self.settings_state = False
        i = self.menu_functions.index(self.save_settings)
        self.frame_menu.winfo_children()[i].config(state='active')

    def new_gen_settings(self):
        self.settings_gen_state = False
        i = self.menu_functions.index(self.save_gen_settings)
        self.frame_menu.winfo_children()[i].config(state='active')

    def save_gen_settings(self, name=None, widget=None):
        self.settings_gen_state = True
        i = self.menu_functions.index(self.save_gen_settings)
        self.frame_menu.winfo_children()[i].config(state='disabled')

        f_options = open('general_options.txt', 'w')
        for key in cfg.topt.keys():
            f_options.write('#\n' + key + " " + str(cfg.topt[key]) + '\n\n')

        self.save_dict(f_options, cfg.opt_process, 'process')
        self.save_dict(f_options, cfg.actions, 'action', False, False)
        f_options.close()

    def save_settings(self, name=None, widget=None):
        self.settings_state = True
        i = self.menu_functions.index(self.save_settings)
        self.frame_menu.winfo_children()[i].config(state='disabled')

        if not os.path.exists(cfg.options_dir):
            os.makedirs(cfg.options_dir)
        options_name = cfg.options_dir + '/options_' + cfg.video_name[cfg.video_name.rfind('/') + 1:-4] + '.txt'

        f_options = open(options_name, 'w')

        f_options.write('#\nexclude')
        for key in cfg.exclude:
            f_options.write(' ' + str(key))
        f_options.write('\n\n')

        self.save_dict(f_options, cfg.opt_filters, 'filter')
        self.save_dict(f_options, cfg.opt_size, 'size')
        self.save_dict(f_options, cfg.opt)
        f_options.close()

        print('Saved options file:', options_name)

    def save_dict(self, file, my_dict, tag=None, labeled=True, keyed=True):
        tag = '' if tag is None else tag + ' '
        for key in my_dict.keys():
            if labeled:
                label = ' ' + cfg.labels[key] if self.check_option(key) else ''
            else:
                label = ''
            ck = key + ' ' if keyed else ''
            file.write('#\n' + tag + ck + str(my_dict[key]) + label + '\n\n')

#
# Menu other functions__________________________________________________________________________________________________
#
    def reload(self, name, button):
        self.active = False
        if cfg.init_options():
            for v in ([cfg.opt_process, 1, self.ch_proc],
                      [cfg.opt_filters, 0, self.ch_filt],
                      [cfg.opt_size, 1, self.ch_win]):
                self.init_slider(v[0], v[1], v[2], False)

            self.paused = True
            self.vid = MyVideo(cfg.video_name)
            self.slider.set(1)

            print(self.vid, MyVideo.counter)
        self.active = True

    def help(self, name, widget):
        WinHelp(tk.Toplevel(self.window), name, widget)

    def pause(self, event):
        self.paused = not self.paused
        print("Paused state changed to:"+str(self.paused))

#
# Event keyboard and mouse functions____________________________________________________________________________________
#
    def my_exit(self, event):
        if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):

            if not self.settings_gen_state:
                confirm = messagebox.askyesnocancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_GENERAL)
                if confirm:
                    self.save_gen_settings()
                elif confirm is None:
                    return

            if not self.settings_state:
                confirm = messagebox.askyesnocancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_OPTIONS)
                if confirm:
                    self.save_settings()
                elif confirm is None:
                    return

            Win.quit(self)

    def quit(self):
        self.my_exit(0)

    def draw(self, event):
        cfg.cx = event.x
        cfg.cy = event.y
        self.drawing = True

    def choose_start(self, event):
        cfg.rx0 = event.x
        cfg.ry0 = event.y
        self.choosing = True

    def choose(self, event):
        if event.x > 0:
            cfg.rx1 = event.x
        if event.y > 0:
            cfg.ry1 = event.y
        self.choosing = True

    def choose_area(self, event_type):
        tx, ty = cfg.opt_size['x0'], cfg.opt_size['y0']
        x0, x1 = min(cfg.rx0, cfg.rx1) + tx, max(cfg.rx1, cfg.rx0) + tx
        y0, y1 = min(cfg.ry0, cfg.ry1) + ty, max(cfg.ry1, cfg.ry0) + ty

        if all([x0, y0, x1 - x0, y1 - y0]) > 0:
            if y0 - ty < 5:
                y0 = 0  # время обычно выставлено сверху
            self.tr = [x0, x1, y0, y1]
            w = int((x1-x0)*self.tc[0].winfo_height()/(y1-y0))
            h = self.tc[0].winfo_height()
            self.tr.append(w)
            self.tr.append(h)
            for i in range(len(cfg.actions)):
                self.tc[i].config(width=w, height=h)

            self.choosing = False
            cfg.rx0, cfg.ry0, cfg.rx1, cfg.ry1 = 0, 0, 0, 0

#
# Mainframe functions___________________________________________________________________________________________________
#
    # TODO how to save frame
    # cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def update(self):
        if not self.active:
            self.window.after(1, self.update)
            return

        if self.paused:
            frame = MyVideo.frame
            ret = True
            delay = 1
        else:
            ret, frame = self.vid.get_frame()
            if not ret:
                print('Something error. ret = False')
            if MyVideo.counter == 0:
                self.paused = True
            self.slider.set(MyVideo.counter)
            delay = cfg.opt_process['delay']

        if ret:
            frame1 = imgF.img_cut(frame.copy())
            frame2 = frame1.copy()
            frame3 = frame.copy()

            if self.choosing:
                x0, x1 = min(cfg.rx0, cfg.rx1), max(cfg.rx1, cfg.rx0)
                y0, y1 = min(cfg.ry0, cfg.ry1), max(cfg.ry1, cfg.ry0)
                if x1-x0 > 0 and y1-y0 > 0:
                    cv2.rectangle(frame1, (x0, y0), (x1, y1), (0, 255, 0), 2)

            frame2 = imgF.img_filter(frame2)
            self.fi = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame2))
            self.canvas_filtered.create_image(0, 0, image=self.fi, anchor=tk.NW)

            cfg.last = {MyVideo.counter: [cfg.cx, cfg.cy]}
            cfg.cx, cfg.cy, area, cnt = imgF.find_center(frame2)

            if self.drawing:
                cv2.circle(frame1, (cfg.cx, cfg.cy), 7, (0, 0, 255), -1)
            self.si = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame1))
            self.canvas_source.create_image(0, 0, image=self.si, anchor=tk.NW)

            if self.tr is not None:
                x0, x1, y0, y1, w, h = self.tr
                for i in range(len(cfg.actions)):
                    self.ti.append(PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame3)
                                                          .crop((x0, y0, x1, y1))
                                                          .resize((w, h))))

                    self.tc[i].create_image(0, 0, image=self.ti[-1], anchor=tk.NW)

        self.window.after(delay, self.update)

#
# Settings functions____________________________________________________________________________________________________
#
    @staticmethod
    def check_option(option):
        for i in cfg.exclude:
            if option.__contains__(i):
                return False
        return True

    def init_slider(self, options_list, my_min, my_function, is_new=True):
        for option in options_list:
            if self.check_option(option):
                if is_new:
                    self.sliders[option] = MySlider(self.frame_settings, my_min, options_list, my_function, option)
                else:
                    self.sliders[option].init = False
                    self.sliders[option].slider.set(options_list[option])

            else:
                continue

    def ch_filt(self, x, name):
        self.new_settings()
        cfg.opt_filters[name] = int(x)

    def ch_proc(self, x, name):
        self.new_gen_settings()
        cfg.opt_process[name] = int(x)

    def ch_win(self, x, name):
        self.new_settings()
        cfg.opt_size[name] = int(x)

#
# Action functions______________________________________________________________________________________________________
#
    def action_start(self, index):
        print("Start: " + cfg.actions[index])

    def action_stop(self, index):
        print("Stop: " + cfg.actions[index])

    def action_init(self, i):
        tk.Button(self.lines[i], text="Start", command=lambda j=i: self.action_start(j)).pack(side=tk.LEFT)
        tk.Button(self.lines[i], text="Stop", command=lambda j=i: self.action_stop(j)).pack(side=tk.LEFT)
        MyEntry(self.lines[i], cfg.actions, self.new_gen_settings, i, tk.LEFT)
        self.tc.append(tk.Canvas(self.lines[i], bg='black', height=25))
        self.tc[-1].pack(side=tk.RIGHT)

    def action_create(self):
        i = len(cfg.actions)
        cfg.actions[i] = ''
        self.lines[i] = tk.Frame(self.frame_actions)
        self.lines[i].pack(side=tk.BOTTOM)
        self.action_init(i)


# Старт программы
MainWindow()
