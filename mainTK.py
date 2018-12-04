import tkinter as tk
import config as cfg

# tkinter Functions
# ---------------------------------------------------------------------------------------------------------------
def start(index):
    print("Start: "+entries[index].get())


def stop(index):
    print("Stop: "+entries[index].get())


def init(i):
    entries[i] = tk.Entry()
    entries[i].grid(row=i, column=2, padx=5, pady=5)

    if i <= len(cfg.actions):
        entries[i].insert(i, cfg.actions[i])
    else:
        cfg.actions.append('')

    start_button = tk.Button(text="Start", command=lambda j=i: start(j))
    start_button.grid(row=i, column=0, padx=5, pady=5, sticky="e")

    stop_button = tk.Button(text="Stop", command=lambda j=i: stop(j))
    stop_button.grid(row=i, column=1, padx=5, pady=5, sticky="e")


def create():
    global cb
    c = len(cfg.actions)+1
    cb.grid(row=c+1, column=2)
    init(c)


root = tk.Tk()
root.title("GUI на Python")
root.withdraw()

entries = {}
c = len(cfg.actions)
for i in range (0, c):
    init(i)

cb = tk.Button(text="Новое действие", command=create)
cb.grid(row=c+1, column=2, padx=5, pady=5, sticky="e")

root.mainloop()
