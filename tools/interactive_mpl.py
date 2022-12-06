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

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

from mannequin.fileio import read_coords_from_txt
from individual_pattern import IndividualPattern
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
                    # interactive_frame.bind('<Enter>', on_enter)
                    # interactive_frame.bind('<Leave>', on_leave)
                    # interactive_frame.bind_all('<Button-1>', on_frame_click)
                    interactive_frame.render()
                    self.mpl_frames.append(interactive_frame)

    def set_selected(self, idx):
        self.selected[idx] = int(1)

    def get_curve(self):
        return self.data_list[np.where(self.selected == 1)[0][0]]


class InteractiveMplFrame(customtkinter.CTkFrame):

    COLORS = {'unselected':     (57/255, 139/255, 227/255),
              'hover':          (230/255, 67/255, 67/255),
              'selected':       (255/255, 190/255, 59/255)}

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
        self.__alternative_exists = False
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
        if not self.__alternative_exists:
            self.__data = []
            self.__data = copy.deepcopy(self.__copy)
            if len(curve) == 4:
                for i in range(len(curve) - 2):
                    pair = [curve[i], curve[i + 2]]
                    uid = str(uuid.uuid4())
                    line = InteractiveLine(pair, id=uid)
                    self.__data.append(line)
            else:
                for c in curve:
                    uid = str(uuid.uuid4())
                    line = InteractiveLine([c], id=uid)
                    self.__data.append(line)
            self.__alternative_exists = True
            self.draw()
        else:
            # Clear the plot
            self.__data = []
            self.__data = copy.deepcopy(self.__copy)
            self.__alternative_exists = False
            self.clear()
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

    def get_data_from_path(self, path: Union[str, PathLike]):
        """Ayth h methodos xrhsimopoieitai gia na enimerwsei to pattern preview plot otan kanw klik se ena rouxol.
        Se aythn thn periptwsh, dinetai ena path pou deixnei sta individual patterns tou epilegmenou retrieved rouxou.
        Auth h methodos loipon, anoigei ola ta individual patterns tou rouxou, enhmerwnei ta dedomena tou instance ths
        klashs kai ksanazwgrafizei to preview."""
        # A workaround to clear the class' data
        if len(self.__data) > 0:
            self.__data = []
        self.__alternative_exists = False
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

    def get_data_from_individual_pattern(self, ind_pat: IndividualPattern):
        self.__data = []
        self.__alternative_exists = False

        self.coords_list = []
        self.included = dict()
        self.__copy = None
        for region in ind_pat.patterns.keys():
            points = ind_pat[region]
            uid = str(uuid.uuid4())
            self.included[uid] = osp.join(ind_pat.garment_dir, region)
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

        for collection in self.__data:
            ax.add_collection(collection.line)

        annot = ax.annotate("", (0, 0), (10, 10), xycoords='figure pixels', bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        x_min = min([l.min_x for l in self.__data])
        y_min = min([l.min_y for l in self.__data])

        x_max = max([l.max_x for l in self.__data])
        y_max = max([l.max_y for l in self.__data])

        ax.set_xlim([x_min - InteractivePatternPreview.MIN_Y, x_max + InteractivePatternPreview.MAX_X])
        ax.set_ylim([y_min - InteractivePatternPreview.MIN_Y, y_max + InteractivePatternPreview.MAX_Y])

        def on_pick(event):
            ind = event.artist.ID
            for il in self.__data:
                id = il.id
                if ind != id:
                    il.set_state(0)
                    il.line.set_color(InteractiveLine.normal_selected_color[0])
                else:
                    il.set_state(1)
                    il.line.set_color(InteractiveLine.normal_selected_color[1])
                    try:
                        pattern_files = ['front', 'back', 'skirt back', 'skirt front', 'sleever',
                                         'sleevel', 'cuffl', 'cuffr', 'collar']
                        for p in pattern_files:
                            if p in self.included[ind]:
                                pattern = p
                        self.editor.on_click_ok(pattern)
                    except KeyError:
                        pass
            self.f.canvas.draw_idle()

        def on_hover(event):
            if event.inaxes == ax:
                annot.set_visible(False)
                for il in self.__data:
                    cont, ind = il.line.contains(event)
                    if il.state == 1:
                        continue

                    if cont:
                        il.set_state(2)
                        il.line.set_color(InteractiveLine.normal_selected_color[2])

                        x, y = event.x, event.y
                        annot.xy = (x, y)
                        annot.xyann = (x + 20, y + 20)
                        pattern_files = ['front', 'back', 'skirt back', 'skirt front', 'sleever',
                                         'sleevel', 'cuffl', 'cuffr', 'collar']
                        ind = il.id
                        for p in pattern_files:
                            if p in self.included[ind]:
                                pattern = p

                        annot.set_text(pattern)
                        annot.get_bbox_patch().set_facecolor('#5577ad')
                        annot.get_bbox_patch().set_alpha(0.8)
                        annot.set_visible(True)
                        self.f.canvas.draw_idle()
                    else:
                        il.set_state(0)
                        il.line.set_color(InteractiveLine.normal_selected_color[0])
                        self.f.canvas.draw_idle()

        def on_key_press(event):
            if event.key == 'z':
                for il in self.__data:
                    if il.state == 1:
                        ax.set_xlim([il.min_x - 20., il.max_x + 20.0])
                        ax.set_ylim([il.min_y - 20., il.max_y + 20.0])
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

    @property
    def alternative_exists(self):
        return self.__alternative_exists

    def get_region(self):
        for il in self.__data:
            if il.state == 1:
                return il
        return None

    def get_state(self, id):
        for il in self.__data:
            if id == il.id:
                return il.state


class InteractiveLine:

    normal_selected_color = np.array([[57 / 255, 139 / 255, 227 / 255, 1.0],
                                      [230 / 255, 67 / 255, 67 / 255, 1.0],
                                      [255 / 255, 190 / 255, 59 / 255, 1.0]])

    def __init__(self, data, id, label):
        self.data = data
        # In order to perform a proper curve replacement, we need the alternative curve pairs to be stored in arrays of
        # shape [num_regions x num_points_per_region x 2]. Otherwise, the replacement will be wrong, especially in the
        # case of the armholes where the curve starts from the beginning of the 1st armhole and ends at the end of the
        # second without a separation.
        self.__data_array = np.vstack(data)
        self.__data_array_np = np.vstack([np.expand_dims(d__, axis=0) for d__ in self.data])
        self.__line = self.build()
        self.__selected = False
        self.__line.set_picker(True)
        self.__id = id
        self.__label = label
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
    def id(self):
        return self.__id

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

    @property
    def data_array(self):
        return self.__data_array_np

    @property
    def label(self):
        return self.__label


if __name__ == '__main__':
    pass
