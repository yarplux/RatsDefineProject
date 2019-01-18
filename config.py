import cv2
from enum import Enum
import numpy as np
import os

from tkinter import filedialog
from tkinter import messagebox

import constants as cs


# Глобальные переменные (инициализация)
# ---------------------------------------------------------------------------------------------------------------

cx = 0                      # global mouse/track x position
cy = 0                      # global mouse/track x position
rx0 = 0
ry0 = 0
rx1 = -1
ry1 = -1

last = {}
opt = {}                    # dictionary of input options
opt_filters = {}            # dict of filter options
opt_size = {}              # dict of window size options
opt_process = {}               # video play options

actions = {}                # list of default actions of rats
exclude = list()            # list of unchangeable from program interface options
labels = {}                 # dictionary of labels to sliders for options
topt = {}
video_name = ''
options_name = ''
options_dir = ''
track_dir = ''
results_dir = ''


# Инициализация опций программы (подгрузка из файла)
# ---------------------------------------------------------------------------------------------------------------
def init_gen_options():
    global opt_process, actions, labels, topt

    file_options = open(cs.FILE_OPTIONS_FOLDER, 'r')
    line = file_options.readline()
    while line:
        if line[0] != '#' and line != "\n":
            line = line.replace('\n', '')
            words = line.split(' ')
            if words[0] == 'action':
                actions[len(actions)] = line[len('action')+1:]
            elif words[0] == 'process':
                opt_process[words[1]] = int(words[2])
                if len(words) > 3:
                    labels[words[1]] = line[len(words[1]) + len(words[2]) + len('process')+3:]
            else:
                topt[words[0]] = line[len(words[0])+1:]
        line = file_options.readline()
    file_options.close()


def init_options():
    global opt, opt_filters, opt_size, opt_process, actions, exclude, labels, topt, \
        video_name, options_name, options_dir, track_dir, results_dir

    print('Last video folder:', topt['last_video'])
    video_name = filedialog.askopenfilename(initialdir=topt['last_video'],
                                            title=cs.DIALOG_TITLE_OPEN_VIDEO,
                                            filetypes=(("video files", "*.avi *.mp4"), ("all files", "*.*")))

    topt['last_video'] = video_name[:video_name.rfind('/')]

    if video_name == '':
        messagebox.showinfo(cs.DIALOG_TITLE_GENERAL, cs.DIALOG_TEXT_ERROR_OPEN_FILE)
        return False

    options_dir = video_name[:video_name.rfind('/')] + cs.DIR_OPTIONS[1:]
    track_dir = video_name[:video_name.rfind('/')] + cs.DIR_TRACKS[1:]
    results_dir = video_name[:video_name.rfind('/')] + cs.DIR_RESULTS[1:]

    options_name = options_dir + '/options_' + video_name[video_name.rfind('/') + 1:-4] + '.txt'
    if not (os.path.exists(options_dir) and os.path.isfile(options_name)):
        options_name = cs.FILE_OPTIONS_DEFAULT

    file_options = open(options_name, 'r')
    line = file_options.readline()
    while line:
        if line[0] != '#' and line != "\n":
            line = line.replace('\n', '')
            words = line.split(' ')
            if words[0] == "exclude":
                for i in range(1, len(words)):
                    exclude.append(words[i])
            elif words[0] == "filter":
                opt_filters[words[1]] = int(words[2])
                if len(words) > 3:
                    labels[words[1]] = line[len(words[1]) + len(words[2]) + 9:]
            elif words[0] == "size":
                opt_size[words[1]] = int(words[2])
                if len(words) > 3:
                    labels[words[1]] = line[len(words[1])+len(words[2])+7:]
            elif words[1].isnumeric():
                opt[words[0]] = int(words[1])
                if len(words) > 2:
                    labels[words[0]] = line[len(words[0])+len(words[1])+2:]
        line = file_options.readline()
    file_options.close()

    # print("Labels:", labels)
    # print("Filters:", opt_filters)
    # print("Process:", opt_process)
    # print("WinSize:", opt_size)
    # print("Actions:", actions)
    # print("Excluded options: ", exclude)
    # print("Other options: ", opt, topt)

    return True