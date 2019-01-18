import tkinter as tk


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

        self.scroll = tk.Scrollbar(window)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.T = tk.Text(self.window, width=120, height=30, yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.T.yview)
        self.T.pack()

        f = open('./README.txt', 'r')
        line = f.readline()

        while line:
            self.T.insert(tk.END, line)
            line = f.readline()

        f.close()
        self.window.mainloop()

    def quit(self):
        self.widget.config(state='active')
        Win.quit(self)
