import copy
import os
import os.path as osp

from os import PathLike
from pathlib import Path
# from functools import partial
from typing import List, Union

import customtkinter
import tkinter
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
        # De doulevei akoma
        event.widget.master.parent.master.update_curves()
        event.widget.master.parent.master.destroy()
    except AttributeError:
        print("E OXI RE POUSTI MOU")


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

    def __init__(self,
                 master: Union[customtkinter.CTkFrame, customtkinter.CTkToplevel],
                 figsize=(9, 5),
                 editor=None,
                 **grid_params):
        self.f = Figure(figsize=figsize)
        self.f.patch.set_facecolor('#343638')
        self.pattern_preview = FigureCanvasTkAgg(self.f, master=master)
        # self._set_callback(self, event, func)

        self.editor = None
        if editor is not None:
            self.editor = editor

        # Instance's data
        self.__data = []
        self.__selected = None

        # Layout setup
        self.pattern_preview.get_tk_widget().grid(**grid_params) # Poly pithano edw na einai TO lathos

    def set_callback(self, event, func):
        self.f.canvas.mpl_connect(event, func)

    def set_editor(self, editor):
        self.editor = editor

    def update(self):
        pass

    def add_curve(self, curve):
        if len(self.__data) > 0:
            __data_copy = copy.deepcopy(self.__data)
            self.__data = []
            self.__data = __data_copy + [curve]

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
        '''Ayth h methodos xrhsimopoieitai gia na enimerwsei to pattern preview plot otan kanw klik se ena rouxol.
        Se aythn thn periptwsh, dinetai ena path pou deixnei sta individual patterns tou epilegmenou retrieved rouxou.
        Auth h methodos loipon, anoigei ola ta individual patterns tou rouxou, enhmerwnei ta dedomena tou instance ths
        klashs kai ksanazwgrafizei to preview.'''
        # A workaround to clear the class' data
        if len(self.__data) > 0:
            self.__data = []

        ind_patterns = os.path.join(Path(path).parent, 'individual patterns')
        pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                         'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']

        self.coords_list = []
        self.included = []
        for f in pattern_files:
            if f in os.listdir(ind_patterns):
                self.coords_list.append(read_coords_from_txt(os.path.join(ind_patterns, f), delimiter=','))
                points = read_coords_from_txt(osp.join(ind_patterns, f), ',')
                curve = []
                self.included.append(f)
                for p in points:
                    curve.append(tuple(p))
                self.__data.append(curve)

    def draw(self):
        self.f.clear()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        ax = self.f.add_subplot(autoscale_on=False)

        temp = np.vstack(self.__data)
        ax.set_facecolor('#343638')
        ax.axis('off')
        ax.set_xlim([temp.min(axis=0)[0] - 20.0, temp.max(axis=0)[0] + 20.0])
        ax.set_ylim([temp.min(axis=0)[1] - 20.0, temp.max(axis=0)[1] + 20.0])
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])

        self.__selected = np.zeros(len(self.__data), dtype=int)
        colors = InteractivePatternPreview.normal_selected_color[self.__selected]
        lines = LineCollection(self.__data, pickradius=10, colors=colors)
        lines.set_picker(True)
        ax.add_collection(lines)
        self.pattern_preview.draw_idle()

        def on_pick(event):
            if event.artist is lines:
                ind = event.ind[0]
                self.__selected[:] = 0
                self.__selected[ind] = 1
                lines.set_color(InteractivePatternPreview.normal_selected_color[self.__selected])
                self.f.canvas.draw_idle()
                self.editor.on_click_ok(self.included[np.where(self.__selected == 1)[0][0]].replace('.xyz', ''))

        def on_plot_hover(event):
            cp = copy.deepcopy(self.__selected)
            if event.inaxes == ax:
                cont, ind = lines.contains(event)
                if cont:
                    cp[np.where(cp == 2)] = 0
                    cp[ind['ind'][0]] = 2

                    lines.set_color(InteractivePatternPreview.normal_selected_color[cp])
                    self.f.canvas.draw_idle()
                else:
                    cp[np.where(cp == 2)] = 0
                    lines.set_color(InteractivePatternPreview.normal_selected_color[cp])
                    self.f.canvas.draw_idle()

        def zoom_fun(event):
            # get the current x and y limits
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            cur_xrange = (cur_xlim[1] - cur_xlim[0]) * .5
            cur_yrange = (cur_ylim[1] - cur_ylim[0]) * .5
            xdata = event.xdata  # get event x location
            ydata = event.ydata  # get event y location
            if event.button == 'up':
                # deal with zoom in
                scale_factor = 1. / 1.15
            elif event.button == 'down':
                # deal with zoom out
                scale_factor = 1.5
            else:
                # deal with something that should never happen
                scale_factor = 1
            # set new limits
            ax.set_xlim([xdata - cur_xrange * scale_factor,
                         xdata + cur_xrange * scale_factor])
            ax.set_ylim([ydata - cur_yrange * scale_factor,
                         ydata + cur_yrange * scale_factor])
            self.f.draw_idle()


        self.f.canvas.mpl_connect('scroll_event', zoom_fun)
        self.f.canvas.mpl_connect("pick_event", on_pick)
        self.f.canvas.mpl_connect("motion_notify_event", on_plot_hover)


if __name__ == '__main__':
    pass
