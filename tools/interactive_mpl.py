from functools import partial
from typing import List

import customtkinter
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection


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

        self.grid = None

        self.selected = np.zeros(self.number_of_plots, dtype=np.int)

        self.mpl_frames = []

    def build_grid(self):
        for i in range(self.rows):
            for j in range(self.columns):
                if i * self.rows + j >= self.number_of_plots:
                    break
                else:
                    interactive_frame = InteractiveMplFrame(master=self.master,
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
        ax.set_xlim([self.data.min(axis=0)[0] - 20.0, self.data.max(axis=0)[0] + 20.0])
        ax.set_ylim([self.data.min(axis=0)[1] - 20.0, self.data.max(axis=0)[1] + 20.0])
        ax.axis('tight')
        ax.axis('off')
        ax.set_aspect('equal')

        self.preview.draw()

    def prepare_data(self):
        curve = []
        for point in self.data:
            curve.append(tuple(point))
        return LineCollection([curve], pickradius=10, colors=InteractiveMplFrame.COLORS['unselected'])

    @property
    def index(self):
        return self.__index

    @property
    def parent(self):
        return self.__parent


if __name__ == '__main__':
    # root = customtkinter.CTk()
    # root.geometry('800x700')
    #
    # impl = InteractiveMplFrame(master=root, width=500, height=500,
    #                            bg_color='#ff0000',
    #                            figsize=(3, 3),
    #                            corner_radius=4,
    #                            data=read_bezier_points_from_txt('/home/kaseris/Documents/database/dress/d1/DD032/data/txt/front/bezier_front_3.txt'))
    # impl.grid(row=0, column=0)
    #
    # impl.render()
    # root.mainloop()
    # grid = MplFrameGrid(data_list=[i for i in range(17)])
    # print(grid.rows)
    # print(grid.columns)
    # print(grid.selected)
    pass
