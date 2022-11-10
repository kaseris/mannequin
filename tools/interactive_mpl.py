import copy
import os
import os.path as osp
import uuid

from os import PathLike
from pathlib import Path
# from functools import partial
from typing import List, Union

import customtkinter
import tkinter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

from mannequin.fileio import read_coords_from_txt
from scrollview import VerticalScrolledFrame


def on_enter(event):
    event.widget.f.patch.set_facecolor('#64676b')
    event.widget.preview.draw()


def on_leave(event):
    event.widget.f.patch.set_facecolor('#343638')
    event.widget.preview.draw()


def on_frame_click(event):
    try:
        # Need to set a method to communicate between parents and children
        event.widget.master.parent.set_selected(event.widget.master.index)
        event.widget.master.parent.master.set_curve_to_replace(event.widget.master.parent.get_curve())
        event.widget.master.parent.master.update_curves()
        event.widget.master.parent.master.destroy()
    except AttributeError:
        pass


class MplFrameGrid:
    def __init__(self,
                 master,
                 data_list: List[np.ndarray],
                 mpl_width,
                 mpl_height,
                 column_size: int = 5):

        self.master = master
        self.mpl_width = mpl_width
        self.mpl_height = mpl_height
        self.number_of_plots = len(data_list)
        self.data_list = data_list

        self.columns = len(data_list) if len(data_list) < column_size else column_size
        self.rows = (self.number_of_plots // column_size) + 1 if (self.number_of_plots % column_size) else 0

        self.selected = np.zeros(self.number_of_plots, dtype=np.int)

        self.mpl_frames = []

        # Setup Layout
        self.holder_frame = customtkinter.CTkFrame(master=master)
        self.holder_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=tkinter.TRUE)

        self.vs_frame = VerticalScrolledFrame(self.holder_frame)
        self.vs_frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=tkinter.TRUE)

    def build_grid(self):
        for i in range(self.rows):
            for j in range(self.columns):
                if i * self.rows + j >= self.number_of_plots:
                    break
                else:
                    interactive_frame = InteractiveMplFrame(master=self.vs_frame.interior,
                                                            height=self.mpl_height,
                                                            width=self.mpl_width,
                                                            bg_color='#343638',
                                                            figsize=(2, 2),
                                                            data=self.data_list[i * self.rows + j],
                                                            index=i * self.rows + j,
                                                            parent=self)
                    interactive_frame.grid(row=i, column=j, padx=(20, 20), pady=(20, 20))
                    interactive_frame.bind('<Enter>', on_enter)
                    interactive_frame.bind('<Leave>', on_leave)
                    interactive_frame.bind_all('<Button-1>', on_frame_click)
                    interactive_frame.render()
                    self.mpl_frames.append(interactive_frame)

    def set_selected(self, idx):
        self.selected[idx] = int(1)

    def get_curve(self):
        return self.data_list[np.where(self.selected == 1)[0][0]]


class InteractiveMplFrame(customtkinter.CTkFrame):

    COLORS = {'unselected': (57/255, 139/255, 227/255),
              'hover': (230/255, 67/255, 67/255),
              'selected': (255/255, 190/255, 59/255)}
    
    def __init__(self,
                 master,
                 parent,
                 width,
                 height,
                 bg_color,
                 figsize,
                 index,
                 data: np.ndarray):

        assert isinstance(figsize, tuple), '`figsize` must be a tuple'

        super(InteractiveMplFrame, self).__init__(master=master, width=width, height=height, bg_color=bg_color)
        self.data = data
        self.__index = index
        self.__parent = parent
        self.curves = self.prepare_data()

        self.f = Figure(figsize=figsize)
        self.preview = FigureCanvasTkAgg(self.f, master=self)
        self.preview.get_tk_widget().grid()

    def render(self):
        self.f.clf()
        # Background color
        self.f.patch.set_facecolor('#343638')
        ax = self.f.add_subplot()
        self.curves.set_picker(True)

        ax.add_collection(self.curves)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim([np.vstack(self.data).min(axis=0)[0] - 1.0, np.vstack(self.data).max(axis=0)[0] + 1.0])
        ax.set_ylim([np.vstack(self.data).min(axis=0)[1] - 1.0, np.vstack(self.data).max(axis=0)[1] + 1.0])
        ax.axis('tight')
        ax.axis('off')
        ax.set_aspect('equal')

        self.preview.draw()

    def prepare_data(self):
        curve_set = []
        for c in self.data:
            curve = []
            for point in c:
                curve.append(tuple(point))
            curve_set.append(curve)
        return LineCollection(curve_set, pickradius=10, colors=InteractiveMplFrame.COLORS['unselected'])

    @property
    def index(self):
        return self.__index

    @property
    def parent(self):
        return self.__parent


class InteractivePatternPreview:

    normal_selected_color = np.array([[57 / 255, 139 / 255, 227 / 255, 1.0],
                                      [230 / 255, 67 / 255, 67 / 255, 1.0],
                                      [255 / 255, 190 / 255, 59 / 255, 1.0]])

    MIN_X = 20.0
    MIN_Y = 20.0
    MAX_X = 20.0
    MAX_Y = 20.0

    def __init__(self,
                 master: Union[customtkinter.CTkFrame, customtkinter.CTkToplevel],
                 figsize=(9, 5),
                 editor=None,
                 **grid_params):
        self.f = Figure(figsize=figsize)
        self.f.patch.set_facecolor('#343638')
        self.pattern_preview = FigureCanvasTkAgg(self.f, master=master)
        self.alternative_exists = False
        self.line_dict = dict()

        self.editor = None
        if editor is not None:
            self.editor = editor

        # Instance's data
        self.__data = []
        self.__copy = None
        self.__selected = None

        # Layout setup
        self.pattern_preview.get_tk_widget().grid(**grid_params)

    def set_callback(self, event, func):
        self.f.canvas.mpl_connect(event, func)

    def set_editor(self, editor):
        self.editor = editor

    def update(self):
        pass

    def add_curve(self, curve):
        if not self.alternative_exists:
            self.__data = []
            self.__data += self.__copy
            for c in curve:
                self.__data += [c]
            self.alternative_exists = True
            return
        else:
            # Clear the plot
            self.__data = []
            self.__data = self.__copy
            self.alternative_exists = False
            self.add_curve(curve)

    def clear(self):
        self.f.clf()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        ax = self.f.add_subplot(autoscale_on=False, xlim=(0, 0), ylim=(0, 0))
        ax.set_facecolor('#343638')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('tight')
        ax.axis('off')
        ax.set_aspect('equal')
        self.pattern_preview.draw()

    def get_data_from_path(self, path: Union[str, PathLike]):
        """Ayth h methodos xrhsimopoieitai gia na enimerwsei to pattern preview plot otan kanw klik se ena rouxol.
        Se aythn thn periptwsh, dinetai ena path pou deixnei sta individual patterns tou epilegmenou retrieved rouxou.
        Auth h methodos loipon, anoigei ola ta individual patterns tou rouxou, enhmerwnei ta dedomena tou instance ths
        klashs kai ksanazwgrafizei to preview."""
        # A workaround to clear the class' data
        if len(self.__data) > 0:
            self.__data = []

        ind_patterns = os.path.join(Path(path).parent, 'individual patterns')
        pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                         'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']

        self.coords_list = []
        self.included = dict()
        for f in pattern_files:
            if f in os.listdir(ind_patterns):
                self.coords_list.append(read_coords_from_txt(os.path.join(ind_patterns, f), delimiter=','))
                points = read_coords_from_txt(osp.join(ind_patterns, f), ',')
                # Assign a universal unique identifier (UUID) to every curve in the pattern preview
                uid = str(uuid.uuid4())
                self.included[uid] = f
                line = InteractiveLine([points], id=uid)
                self.line_dict[uid] = line
                self.__data.append(line)
        self.__copy = copy.deepcopy(self.__data)

    def draw(self):
        self.f.clear()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        ax = self.f.add_subplot(autoscale_on=False)

        ax.set_facecolor('#343638')
        ax.axis('off')
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])

        self.__selected = np.zeros(len(self.__data), dtype=int)
        for collection in self.__data:
            ax.add_collection(collection.line)

        x_min = min([l.min_x for l in self.__data])
        y_min = min([l.min_y for l in self.__data])

        x_max = max([l.max_x for l in self.__data])
        y_max = max([l.max_y for l in self.__data])

        ax.set_xlim([x_min - InteractivePatternPreview.MIN_Y, x_max + InteractivePatternPreview.MAX_X])
        ax.set_ylim([y_min - InteractivePatternPreview.MIN_Y, y_max + InteractivePatternPreview.MAX_Y])

        def on_pick(event):
            ind = event.artist.ID
            for id in self.line_dict.keys():
                if ind != id:
                    self.line_dict[id].set_state(0)
                    self.line_dict[id].line.set_color(InteractiveLine.normal_selected_color[0])
                else:
                    self.line_dict[id].set_state(1)
                    self.line_dict[id].line.set_color(InteractiveLine.normal_selected_color[1])
                    self.editor.on_click_ok(self.included[ind].replace('.xyz', ''))
            self.f.canvas.draw_idle()

        def on_hover(event):
            if event.inaxes == ax:
                for il in self.__data:
                    cont, ind = il.line.contains(event)

                    if il.state == 1:
                        continue

                    if cont:
                        il.set_state(2)
                        il.line.set_color(InteractiveLine.normal_selected_color[2])
                        self.f.canvas.draw_idle()
                    else:
                        il.set_state(0)
                        il.line.set_color(InteractiveLine.normal_selected_color[0])
                        self.f.canvas.draw_idle()

        def on_key_press(event):
            if event.key == 'z':
                for il in self.__data:
                    if il.state == 1:
                        ax.set_xlim([il.min_x - 100., il.max_x + 100.0])
                        ax.set_ylim([il.min_y - 100., il.max_y + 100.0])
                        self.f.canvas.draw_idle()
                        break
            elif event.key == 'escape':
                min_x = min([l.min_x for l in self.__data])
                min_y = min([l.min_y for l in self.__data])
                max_x = max([l.max_x for l in self.__data])
                max_y = max([l.max_y for l in self.__data])
                ax.set_xlim([min_x - 20.0, max_x + 20.0])
                ax.set_ylim([min_y - 20.0, max_y + 20.0])
                self.f.canvas.draw_idle()

        self.f.canvas.mpl_connect('key_press_event', on_key_press)
        self.f.canvas.mpl_connect("motion_notify_event", on_hover)
        self.f.canvas.mpl_connect('pick_event', on_pick)
        self.f.canvas.draw_idle()


class InteractiveLine:

    normal_selected_color = np.array([[57 / 255, 139 / 255, 227 / 255, 1.0],
                                      [230 / 255, 67 / 255, 67 / 255, 1.0],
                                      [255 / 255, 190 / 255, 59 / 255, 1.0]])

    def __init__(self, data, id):
        self.data = data
        self.__data_array = np.vstack(data)
        self.__line = self.build()
        self.__selected = False
        self.__line.set_picker(True)
        self.__id = id
        setattr(self.__line, 'ID', self.__id)

        '''States:
        0: unselected
        1: selected
        2: hovered
        '''
        self.__state = 0

    def build(self):
        curve_set = []
        for c in self.data:
            curve = []
            for point in c:
                curve.append(tuple(point))
            curve_set.append(curve)
        return LineCollection(curve_set, pickradius=10, colors=InteractiveMplFrame.COLORS['unselected'])

    def set_state(self, state):
        self.__state = state

    @property
    def state(self):
        return self.__state

    @property
    def line(self):
        return self.__line

    @property
    def min_x(self):
        return self.__data_array.min(axis=0)[0]

    @property
    def min_y(self):
        return self.__data_array.min(axis=0)[1]

    @property
    def max_x(self):
        return self.__data_array.max(axis=0)[0]

    @property
    def max_y(self):
        return self.__data_array.max(axis=0)[1]


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    armhole1 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/DD032/data/txt/front/bezier_front_1.txt',
                                    delimiter=',')
    armhole2 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/DD032/data/txt/front/bezier_front_5.txt',
                                    delimiter=',')

    armhole3 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/Q5751/data/txt/front/bezier_front_1.txt',
                                    delimiter=',')
    armhole4 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/Q5751/data/txt/front/bezier_front_5.txt',
                                    delimiter=',')

    armhole5 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/Q6089/data/txt/front/bezier_front_1.txt',
                                    delimiter=',')
    armhole6 = read_coords_from_txt('/home/kaseris/Documents/database/dress/d1/Q6089/data/txt/front/bezier_front_3.txt',
                                    delimiter=',')

    root = customtkinter.CTk()
    root.title('Test')
    root.geometry('500x500')

    line = InteractiveLine([armhole1, armhole2], id=0)
    line2 = InteractiveLine([armhole3, armhole4], id=1)
    line3 = InteractiveLine([armhole5, armhole6], id=2)

    f = Figure(figsize=(3, 3))
    preview = FigureCanvasTkAgg(f, master=root)
    preview.get_tk_widget().pack()
    ax = f.add_subplot()

    ax.add_collection(line.line)
    ax.add_collection(line2.line)
    ax.add_collection(line3.line)

    lns = [line, line2, line3]

    x_min = min([l.min_x for l in lns])
    y_min = min([l.min_y for l in lns])

    x_max = max([l.max_x for l in lns])
    y_max = max([l.max_y for l in lns])

    ax.set_xlim([x_min, x_max])
    ax.set_ylim([y_min, y_max])
    ax.set_aspect('equal')

    def on_pick(event):
        for i in range(len(lns)):
            if i != event.artist.ID:
                lns[i].set_state(0)
                lns[i].line.set_color(InteractiveLine.normal_selected_color[0])
        lns[event.artist.ID].set_state(1)
        lns[event.artist.ID].line.set_color(InteractiveLine.normal_selected_color[1])

        f.canvas.draw()

    f.canvas.mpl_connect("pick_event", on_pick)
    f.canvas.draw()
    root.mainloop()
