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

from panels_menu import Win, WinHelp

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
        self.button = tk.Button(my_parent, text=my_text, bd=1, relief=tk.FLAT, command=self.callback)
        self.button.pack(side=side, pady=3, padx=5)

    def callback(self):
        self.function(self.name, self.button)


#
# Video wrapper classes ================================================================================================
#
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
    sliders = {}            # settings sliders list
    lines = {}              # actions frames list
    # tc = list()           # time canvas list

    active = True           # state of active update function
    paused = True           # state of catching new video frames in update function
    ss = True               # state of saved video settings
    sgs = True              # state of saved general settings
    drawing = False         # state of changing rat center place
    choosing = False        # state of defining areas

    started = False         # state of started action

    tr = [0]*6              # list, defininng time zone rectangle
    ti = [None]*2           # time start/end image list

    si = None               # temp source image
    fi = None               # temp filtered image

    ca = None               # current action
    cc = None               # current category of chosing area

#
# Initialization________________________________________________________________________________________________________
#
    def __init__(self, window=tk.Tk(), window_title='Наблюдение за крысами 2.0'):
        Win.__init__(self, window, window_title, True)

        cfg.init_gen_options()
        while not cfg.init_options():
            if not messagebox.askyesno(cs.DIALOG_TITLE_OPEN_VIDEO, cs.DIALOG_TEXT_ANOTHER):
                exit()

        self.ca = tk.StringVar()  # current action

        self.window.focus_force()

        # Init Main Menu
        self.frame_menu = tk.Frame(self.window)
        self.frame_menu.pack(fill=tk.X, side=tk.TOP, pady=5)

        self.menu = ['Помощь', 'Открыть другое видео', 'Сохранить общие настройки', 'Сохранить настройки видео']
        self.menu_functions = [self.help, self.reload, self.save_gen_settings, self.save_settings]

        for i in range(len(self.menu)):
            MyButton(self.frame_menu, self.menu[i], self.menu_functions[i], tk.LEFT)
            if self.menu[i].__contains__('Сохранить'):
                self.frame_menu.winfo_children()[i].config(state='disabled')


        # Init Settings
        self.frame_settings = tk.Frame(self.window, bd=1, relief=tk.SOLID)
        self.frame_settings.pack(fill=tk.Y, side=tk.RIGHT)

        self.init_slider(cfg.opt_process, 1, self.ch_proc)
        tk.Frame(self.frame_settings, height=2, bg="black").pack(fill=tk.X, pady=5)
        tk.Label(self.frame_settings, text="Настройки видео:", font=("Helvetica", 16, 'bold')).pack()

        for v in ([cfg.opt_filters, 0, self.ch_filt],
                  [cfg.opt_size, 1, self.ch_win]):
            self.init_slider(v[0], v[1], v[2])
            tk.Frame(self.frame_settings, height=2, bg="black").pack(fill=tk.X, pady=5)

        tk.Label(self.frame_settings, text="Выбор областей:", font=("Helvetica", 16, 'bold')).pack()

        self.MODES = ['Время', 'Кормушка', 'Поилка', 'Центр']
        self.cc = tk.StringVar()
        self.cc.set(0)

        for text in self.MODES:
            b = tk.Radiobutton(self.frame_settings, text=text, variable=self.cc, value=self.MODES.index(text), indicatoron=0)
            b.pack(fill=tk.X, padx=10, pady=3)

        tk.Button(self.frame_settings, text="Зафиксировать", command=lambda ind=self.cc: self.choose_area(ind))\
            .pack(fill=tk.X, padx=10, pady=10)

        # Init Video Frame
        self.vid = MyVideo(cfg.video_name)

        # Create a canvas that can fit the above video source size

        self.frame_main = tk.Frame(self.window, bd=1, relief=tk.SOLID)
        self.frame_main.pack()

        self.canvas_source = tk.Canvas(self.frame_main, width=self.vid.width, height=self.vid.height)
        self.canvas_filtered = tk.Canvas(self.frame_main, width=self.vid.width, height=self.vid.height)
        self.canvas_source.pack(side=tk.LEFT)
        self.canvas_filtered.pack(side=tk.RIGHT)

        for canvas in [self.canvas_source, self.canvas_filtered]:
            canvas.bind('<ButtonPress-1>', self.draw)
            canvas.bind('<B1-Motion>', self.draw)

        self.canvas_source.bind('<ButtonPress-3>', self.choose_start)
        self.canvas_source.bind('<B3-Motion>', self.choose)

        self.slider = tk.Scale(self.window, label='Текущий кадр',
                               from_=1, to=self.vid.length, orient=tk.HORIZONTAL,
                               command=lambda x, flag=self.paused: self.vid.set_frame(int(x), flag))

        self.slider.pack(fill=tk.X)
        tk.Frame(self.window, bg="black").pack(fill=tk.X, pady=5)

        cfg.cx = 0
        cfg.cy = 0

        # Init Actions
        self.ca.set(-1)
        self.ca.trace("w", lambda name, k, mode, sv=self.ca: self.action_start(sv))

        self.frame_actions = tk.Frame(self.window)
        self.frame_actions.pack(anchor=tk.NW, side=tk.LEFT)

        frame = tk.Frame(self.frame_actions)
        frame.pack(anchor=tk.NW)
        tk.Button(frame, text='Stop (s)', font='Helvetica 16 bold', fg='red', command=lambda sv=self.ca: self.action_stop(sv)).pack(side=tk.LEFT, padx=3, pady=3)
        tk.Button(frame, text='Новое действие', command=self.action_create).pack(side=tk.LEFT, padx=3, pady=3)

        for i in cfg.actions.keys():
            self.lines[i] = tk.Frame(self.frame_actions)
            self.lines[i].pack()
            self.action_init(i)

        # flat, groove, raised, ridge, solid, or sunken
        self.frame_time = tk.Frame(self.window, bd=2, relief=tk.RAISED)

        # self.frame_time.pack()
        tk.Canvas(self.frame_time, bg='black').pack(anchor=tk.N)
        tk.Entry(self.frame_time, font="Helvetica 14").pack(anchor=tk.N)
        tk.Canvas(self.frame_time, bg='black').pack(anchor=tk.N)
        tk.Entry(self.frame_time, font="Helvetica 14").pack(anchor=tk.N)
        tk.Button(self.frame_time, text='В отчёт', font='Helvetica 16 bold', fg='red', command=lambda sv=self.ca: self.action_write(sv)).pack(anchor=tk.N)

        # TEST
        self.tr = cs.TIME_AREA
        for i in [0, 2]:
            self.frame_time.winfo_children()[i].config(width=self.tr[4], height=self.tr[5])
        self.ti[0] = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(MyVideo.frame.copy())
                                                .crop(tuple(self.tr[0:4]))
                                                .resize(tuple(self.tr[4:])))
        self.frame_time.pack()

        self.window.bind('<space>', self.pause)
        self.window.bind('<Escape>', self.my_exit)
        self.window.bind('<s>', lambda event, sv=self.ca: self.action_stop(sv))
        self.window.bind('<Left>', self.left)
        self.window.bind('<Right>', self.right)
        self.window.bind('<Button-1>', self.unfocus)
        self.window.bind('<Button-3>', self.unfocus)
        self.window.bind('<Key>', self.action_start_but)
        self.window.bind('<Return>', self.enter)

        # for widget in self.window.winfo_children():
        #     widget.config(bd=10, relief=tk.SUNKEN)
        #     print(widget)

        self.update()
        self.window.mainloop()

#
# Settings functions____________________________________________________________________________________________________
#
    def new_settings(self):
        self.ss = False
        i = self.menu_functions.index(self.save_settings)
        self.frame_menu.winfo_children()[i].config(state='active')

    def new_gen_settings(self):
        self.sgs = False
        i = self.menu_functions.index(self.save_gen_settings)
        self.frame_menu.winfo_children()[i].config(state='active')

    def save_gen_settings(self, name=None, widget=None):
        self.sgs = True
        i = self.menu_functions.index(self.save_gen_settings)
        self.frame_menu.winfo_children()[i].config(state='disabled')

        f_options = open('general_options.txt', 'w')
        self.save_dict(f_options, cfg.opt_process, 'process')
        self.save_dict(f_options, cfg.actions, 'action', False, False)
        f_options.close()

    def save_settings(self, name=None, widget=None):
        self.ss = True
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

        self.active = True

    def help(self, name, widget):
        WinHelp(tk.Toplevel(self.window), name, widget)

    def choose_area(self, event_type):
        tx, ty = cfg.opt_size['x0'], cfg.opt_size['y0']
        x0, x1 = min(cfg.rx0, cfg.rx1) + tx, max(cfg.rx1, cfg.rx0) + tx
        y0, y1 = min(cfg.ry0, cfg.ry1) + ty, max(cfg.ry1, cfg.ry0) + ty

        if int(event_type.get()) == 0 and all([x0, y0, x1 - x0, y1 - y0]) > 0:
            # if y0 - ty < 5:
            #     y0 = 0  # время обычно выставлено сверху
            # для компенсации рамки в 2 пиксела
            y0-=2
            y1+=2

            # TODO в константы
            h = 50
            w = int((x1-x0)*h/(y1-y0))

            for i in [0, 2]:
                self.frame_time.winfo_children()[i].config(width=w, height=h)

            self.tr = [x0, y0, x1, y1, w, h]
            print(self.tr)

            self.choosing = False

            cfg.rx0, cfg.ry0, cfg.rx1, cfg.ry1 = 0, 0, 0, 0
            self.frame_time.pack(anchor=tk.NE, side=tk.RIGHT)

#
# Event keyboard and mouse functions____________________________________________________________________________________
#
    def enter(self, event):
        print(event.widget)
        if event.widget == self.frame_time.winfo_children()[1]:
            self.frame_time.winfo_children()[3].focus()
        elif event.widget == self.frame_time.winfo_children()[3]:
            self.action_write(self.ca)

    def action_start_but(self, event):
        if not isinstance(event.widget, tk.Entry):
            try:
                self.ca.set(int(event.char)-1)
            except:
                return

    def pause(self, event):
        if not isinstance(event.widget, tk.Entry) and not isinstance(event.widget, tk.Button):
            self.paused = not self.paused

    def unfocus(self, event):
        if not isinstance(event.widget, tk.Entry):
            self.window.focus()

    def left(self, event):
        if MyVideo.counter > 0:
            x = MyVideo.counter
            d = cfg.opt_process['FrameDelta']
            self.slider.set(x-d)

    def right(self, event):
        if MyVideo.counter < self.vid.length:
            x = MyVideo.counter
            d = cfg.opt_process['FrameDelta']
            self.slider.set(x+d)

    def my_exit(self, event):
        if messagebox.askokcancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_EXIT):

            if not self.sgs:
                confirm = messagebox.askyesnocancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_GENERAL)
                if confirm:
                    self.save_gen_settings()
                elif confirm is None:
                    return

            if not self.ss:
                confirm = messagebox.askyesnocancel(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_SAVE_OPTIONS)
                if confirm:
                    self.save_settings()
                elif confirm is None:
                    return

            f_options = open('general_options.txt', 'a')
            for key in cfg.topt.keys():
                f_options.write('#\n' + key + " " + str(cfg.topt[key]) + '\n\n')
            f_options.close()

            Win.quit(self)

    def quit(self):
        self.my_exit(0)

    def draw(self, event):
        cfg.cx = event.x
        cfg.cy = event.y
        self.drawing = True

    def choose_start(self, event):
        widget = self.frame_main.winfo_children()[0]
        w = self.fi.width()
        h = self.fi.height()
        dx = int((widget.winfo_width() - w)/2)
        dy = int((widget.winfo_height() - h) / 2)
        if event.x - dx == cfg.rx1 and event.y - dy == cfg.ry1:
            self.choosing = False

        if (dx < event.x < dx + w) and (dy < event.y < dy + h):
            cfg.rx0 = event.x - dx
            cfg.ry0 = event.y - dy
            cfg.rx1, cfg.ry1 = 0,0

    def choose(self, event):
        widget = self.frame_main.winfo_children()[0]
        w = self.fi.width()
        h = self.fi.height()
        dx = int((widget.winfo_width() - w)/2)
        dy = int((widget.winfo_height() - h) / 2)
        if (dx < event.x < dx + w) and (dy < event.y < dy + h):
            cfg.rx1 = event.x - dx
            cfg.ry1 = event.y - dy
        self.choosing = True

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

            if self.choosing:
                x0, x1 = min(cfg.rx0, cfg.rx1), max(cfg.rx1, cfg.rx0)
                y0, y1 = min(cfg.ry0, cfg.ry1), max(cfg.ry1, cfg.ry0)
                if x1-x0 > 0 and y1-y0 > 0:
                    cv2.rectangle(frame1, (x0, y0), (x1, y1), (0, 255, 0), 2)

            frame2 = imgF.img_filter(frame2)
            self.fi = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame2))
            self.canvas_filtered.create_image(int(self.vid.width/2), int(self.vid.height/2), image=self.fi, anchor=tk.CENTER)

            cfg.last = {MyVideo.counter: [cfg.cx, cfg.cy]}
            cfg.cx, cfg.cy, area, cnt = imgF.find_center(frame2)

            if self.drawing:
                cv2.circle(frame1, (cfg.cx, cfg.cy), 7, (0, 0, 255), -1)

            cv2.line(frame1, (int(self.fi.width() / 2), 0), (int(self.fi.width() / 2), int(self.vid.height)), (0, 255, 0), 2)
            self.si = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame1))
            self.canvas_source.create_image(int(self.vid.width/2), int(self.vid.height/2), image=self.si, anchor=tk.CENTER)

            # TODO отображение времени
            if self.ti[0] is not None:
                self.ti[1] = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(MyVideo.frame.copy())
                                                    .crop(tuple(self.tr[0:4]))
                                                    .resize(tuple(self.tr[4:])))
                for i in [0,1]:
                    self.frame_time.winfo_children()[i*2].create_image(0, 0, image=self.ti[i], anchor=tk.NW)

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
    def action_start(self, var):
        i = int(var.get())

        if not self.tr[4]*self.tr[5] == 0 and 0 <= i < len(cfg.actions):
            print("Actions: " + cfg.actions[i])

            self.ti[0] = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(MyVideo.frame.copy())
                                                .crop(tuple(self.tr[0:4]))
                                                .resize(tuple(self.tr[4:])))
        elif self.tr[4]*self.tr[5] == 0:
            var.set(-1)
            tk.messagebox.showwarning(cs.DIALOG_TITLE_WARNING, cs.DIALOG_TEXT_WARNING_TIME_AREA)

    def action_write(self, var):

        i = int(var.get())

        if 0 <= i < len(cfg.actions):
            widgets = self.frame_time.winfo_children()

            if not os.path.exists(cfg.results_dir):
                os.makedirs(cfg.results_dir)

            results = cfg.results_dir + '/results_' + cfg.video_name[cfg.video_name.rfind('/') + 1:-4] + '.csv'

            if os.path.isfile(results):
                f_options = open(results, 'a')
            else:
                f_options = open(results, 'w')
                f_options.write('Время начала; Время конца; Движение;\n')

            for entry in [widgets[1], widgets[3]]:
                t = entry.get()
                t = t.replace(',', ' ')
                t = t.replace(':', ' ')
                words = t.split(' ')
                print(words)
                if not len(words) == 3 or not words[0].isnumeric() or not words[1].isnumeric or not words[2].isnumeric:
                    tk.messagebox.showwarning(cs.DIALOG_TITLE_WARNING, cs.DIALOG_TEXT_WARNING_TIME)
                    f_options.close()
                    return

                if not 0 <= all(words) <= 59:
                    tk.messagebox.showwarning(cs.DIALOG_TITLE_WARNING, cs.DIALOG_TEXT_WARNING_TIME)
                    f_options.close()
                    return

                f_options.write(words[0]+':'+words[1]+':'+words[2]+';')

            f_options.write(cfg.actions[i]+';\n')
            f_options.close()
            widgets[1].delete(0, tk.END)
            widgets[3].delete(0, tk.END)
            var.set(-1)
            self.window.focus()

        else:
            tk.messagebox.showwarning(cs.DIALOG_TITLE_WARNING, cs.DIALOG_TEXT_WARNING_ACTION)

    def action_stop(self, var):
        if not int(var.get()) == -1:
            self.paused = not self.paused
            self.frame_time.winfo_children()[1].focus()

    def action_init(self, i):
        tk.Radiobutton(self.lines[i], text='Start', font="Helvetica 14", variable=self.ca, value=i, indicatoron=0)\
            .pack(side=tk.LEFT, padx=3, pady=3)

        MyEntry(self.lines[i], cfg.actions, self.new_gen_settings, i, tk.LEFT)

    def action_create(self):
        i = len(cfg.actions)
        cfg.actions[i] = ''
        self.lines[i] = tk.Frame(self.frame_actions)
        self.lines[i].pack()
        self.action_init(i)


# Старт программы
MainWindow()
