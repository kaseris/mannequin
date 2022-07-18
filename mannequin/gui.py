import json

from tkinter import *
from tkinter import constants, filedialog
from tkinter import messagebox
import tkinter as tk
import tkinter.font as TkFont

from edit_pattern import infer_pattern_category, get_available_choices, select_region
from popup import PopupWindow

with open('conf.json', 'r') as f:
    data = json.load(f)

DATABASE_DIR = data['pattern_db']

map_available_patterns_to_pretty = {
    'front': 'Front',
    'back': 'Back',
    'skirt_front': 'Skirt Front',
    'skirt_back': 'Skirt Back'
}


class ApplicationWindow:
    def __init__(self, title="Hi", width=500, height=500, start_x=50, start_y=50):
        self.window = Tk()
        self.window.title(title)
        self.window.geometry(f'{str(width)}x{str(height)}+{start_x}+{start_y}')
        self.open_button = Button(self.window,
                                  text="Open File",
                                  command=self._onOpenClick)
        self.specified_dir = Label(self.window, text="Selected path: ")

        self.edit_button = Button(self.window,
                                  text="Edit Pattern",
                                  command=self._onEditClick)
        self.quit_button = Button(self.window,
                                  text="Quit",
                                  command=self._onQuitClick)
        self.pattern_type = Label(self.window,
                                  text="Selected pattern")

        self.open_button.pack(ipadx=5, ipady=5, expand=True)
        self.specified_dir.pack(ipadx=10, ipady=10, expand=True)
        self.edit_button.pack(ipadx=5, ipady=5, expand=True)
        self.pattern_type.pack(ipadx=5, ipady=5, expand=True)
        self.quit_button.pack(ipady=5, ipadx=5, expand=True)
        self._pattern_directory = None
        self._pattern_selection = None

        self._pattern_selection = None

    def _onOpenClick(self):
        p = filedialog.askdirectory(initialdir=DATABASE_DIR)
        self._set_pattern_directory(p)
        p_ = '/'.join(p.split('/')[-3:])
        self.specified_dir.config(text=f"Selected path: {p_}")

    def _set_pattern_directory(self, path):
        self._pattern_directory = path

    def _onEditClick(self):

        def _onSelect():
            # self._pattern_selection = self.var.get()
            selection = "You selected the option " + str(self.var.get())
            label.config(text=selection)

        def quit_window():
            _slave_window.destroy()

        _slave_window = Toplevel(self.window)
        _slave_window.geometry("243x130+800+500")
        self.var = IntVar()

        l1 = Label(_slave_window, text="Please select the pattern\n you want to change:") # .grid(sticky="W")
        l1.pack()

        cat = infer_pattern_category(self._pattern_directory)

        pattern_choices = get_available_choices(cat)

        for choice_idx, pattern_type in enumerate(pattern_choices):
            # print(choice_idx)
            setattr(self, f'r{choice_idx}', Radiobutton(_slave_window,
                                                        text=map_available_patterns_to_pretty[pattern_type],
                                                        variable=self.var,
                                                        value=choice_idx,
                                                        command=_onSelect))
            getattr(self, f'r{choice_idx}').pack(anchor=W)
        label = Label(_slave_window, text="asd")
        label.pack(anchor=W)
        b = Button(_slave_window, text="OK", command=quit_window)
        b.pack(anchor=W)

    def _onQuitClick(self):
        self.window.destroy()


    def start(self):
        self.window.mainloop()


if __name__ == '__main__':
    app = ApplicationWindow()
    app.start()