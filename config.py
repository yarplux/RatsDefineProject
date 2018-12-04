import cv2
from enum import Enum
import numpy as np
import os

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import constants as cs

# Глобальные переменные (инициализация)
# ---------------------------------------------------------------------------------------------------------------
class WE(Enum):
    # TODO добавить plot - для построения графика
    source, resImg, set, track = range(4)


tk.Tk().withdraw()


cx = 0                      # global mouse/track x position
cxd = 0                     # global track x position change by trackbar
cy = 0                      # global mouse/track x position
cyd = 0                     # global track x position change by trackbar
delay = 0
drawing = False             # true if mouse is pressed
waiting = False             # true if waitKey()

counter = 0                 # number of current frame

h = 0                       # global height of input img
w = 0                       # global width of input img

results = [np.zeros((h, w, 3), np.uint8) for i in WE]
cap = cv2.VideoCapture()
trace = np.zeros((h, w, 3), np.uint8)

last = {}
opt = {}                    # list of input options
actions = list()            # list of default actions of rats

# Инициализация опций программы (подгрузка из файла)
# ---------------------------------------------------------------------------------------------------------------
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

options_dir = video_name[:video_name.rfind('/')] + cs.DIR_OPTIONS[1:]
track_dir = video_name[:video_name.rfind('/')] + cs.DIR_TRACKS

options_name = options_dir + '/options_' + video_name[video_name.rfind('/')+1:-4] + '.txt'
if not (os.path.exists(options_dir) and os.path.isfile(options_name)):
        options_name = cs.FILE_OPTIONS_DEFAULT


fOptions = open(options_name, 'r')
line = fOptions.readline()
while line:
    if line[0] != '#' and line != "\n":
        line = line.replace('\n', '')
        words = line.split(' ')
        # words[1] = words[1].replace('\n', '')
        if words[0] == "action":
            actions.append(line[7:])
        elif words[1].isnumeric():
            opt[words[0]] = int(words[1])
    line = fOptions.readline()
fOptions.close()