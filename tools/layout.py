import copy
import os.path as osp
import threading
import time

from functools import partial
from pathlib import Path
from typing import Union

import tkinter
import vispy
import vispy.scene as scene
from vispy.io import imread

import customtkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton
from matplotlib.path import Path as MPLPath
import numpy as np

from PIL import Image, ImageTk, ImageOps

import instructions
from interactive_mpl import MplFrameGrid
from query_mvc import Mesh
from scrollview import VerticalScrolledFrame

from matplotlib.patches import PathPatch as MPLPathPatch


vispy.use(app='tkinter')


def disable_event():
    pass


class Layout:
    VISPY_CANVAS_BG_COLOR_DARK = '#4a4949'
    MAIN_WIN_WIDTH = 1920
    MAIN_WIN_HEIGHT = 1080

    def __init__(self,
                 title='i-Mannequin',
                 geometry=f'{MAIN_WIN_WIDTH}x{MAIN_WIN_HEIGHT}'):
        self.root = None
        self.title = title
        self.geometry = geometry

        self.sidebar = None
        self.frame_espa = None
        self.frame_watermark = None
        self.query_image_placeholder = None
        self.frame_retrieved = None
        self.frame_information = None
        self.frame_pattern_preview = None
        self.frame_pattern_editor = None
        self.shape_similarity_window = None

        self.build()

        self.shown = False

    def build(self):
        self.root = customtkinter.CTk()
        self.root.title(self.title)
        self.root.geometry(self.geometry)
        self.root.minsize(width=1500, height=700)

        self.sidebar = Sidebar(master=self.root, width=200, corner_radius=9)
        self.frame_espa = FrameESPA(master=self.root, corner_radius=9, height=80, fg_color='#ffffff')
        self.frame_watermark = FrameWatermark(master=self.root, corner_radius=9, width=1650, height=930)
        self.sidebar.build()
        self.frame_watermark.build()
        self.frame_espa.build()

    def show(self):
        if not self.shown:
            self.frame_retrieved = FrameRetrievedPlaceholder(master=self.frame_watermark, width=1290, height=355)
            self.frame_retrieved.build()
            for i in range(4):
                setattr(self, f'retrieved_viewport_{i+1}', RetrievedViewportPlaceholder(i, '260x260',
                                                                                        master=self.root))
            self.query_image_placeholder = QueryImagePlaceholder(master=self.root)
            self.root.bind('<Configure>', self.query_image_placeholder.dragging)
            self.frame_information = FrameGarmentInformation(master=self.frame_watermark, corner_radius=9,
                                                             width=327, height=553)
            self.frame_information.build()

            self.frame_pattern_preview = FramePatternPreview(master=self.frame_watermark, corner_radius=9,
                                                             width=1290, height=553)
            self.frame_pattern_preview.build()
            self.frame_pattern_editor = FrameEditorView(master=self.frame_pattern_preview,
                                                        fg_color='#343638', width=300, height=500,
                                                        bg_color='#343638')
            self.frame_pattern_editor.build()

            self.shown = True
        else:
            print('shown')


class RetrievedViewportPlaceholder(customtkinter.CTkToplevel):
    OFFSETS = [(680, 115), (980, 115), (1280, 115), (1580, 115)]

    def __init__(self, offset_index, geometry, **kwargs):
        super(RetrievedViewportPlaceholder, self).__init__(**kwargs)
        self.geometry(geometry+f'+{RetrievedViewportPlaceholder.OFFSETS[offset_index][0]}'
                               f'+{RetrievedViewportPlaceholder.OFFSETS[offset_index][1]}')
        self.__idx = offset_index + 1

        self.title(f'Retrieved Garment: {offset_index + 1}')
        self.wm_transient(self.master)
        self.drag_id = ''
        self.vispy_canvas = scene.SceneCanvas(keys='interactive',
                                              show=True,
                                              parent=self)
        self.vispy_canvas.native.pack(side=tkinter.TOP, fill=tkinter.BOTH,
                                      expand=True)
        self.vispy_view = self.vispy_canvas.central_widget.add_view(bgcolor=Layout.VISPY_CANVAS_BG_COLOR_DARK)
        self.text = customtkinter.CTkLabel(master=self, text='Please wait...')
        self.wm_protocol('WM_DELETE_WINDOW', disable_event)

    def draw(self, kind, fname):
        self.clear()
        if kind == 'image':
            im = imread(fname)
            im_obj = vispy.scene.visuals.Image(im, parent=self.vispy_view)
            self.vispy_view.add(im_obj)
            self.vispy_view.camera = vispy.scene.PanZoomCamera(aspect=1)
            self.vispy_view.camera.flip = (0, 1, 0)
            self.vispy_view.camera.set_range()
            self.vispy_view.camera.zoom(1., (250, 250))
        else:

            # self.text.pack()
            vertices, faces, _, _ = vispy.io.read_mesh(fname)
            m = Mesh(vertices=vertices, faces=faces)
            mesh = vispy.scene.visuals.Mesh(vertices=m.vertices,
                                            shading='smooth',
                                            faces=m.faces)
            self.vispy_view.add(mesh)
            self.vispy_view.camera = vispy.scene.TurntableCamera(elevation=90, azimuth=0, roll=90)
            self.text.pack_forget()

    def clear(self):
        self.vispy_view.parent = None
        self.vispy_view = self.vispy_canvas.central_widget.add_view(bgcolor=Layout.VISPY_CANVAS_BG_COLOR_DARK)

    def dragging(self, event):
        if event.widget is self.master:
            if self.drag_id == '':
                pass
            else:
                self.master.after_cancel(self.drag_id)
                x = self.master.winfo_x()
                y = self.master.winfo_y()
                self.geometry(f'400x300+{x + QueryImagePlaceholder.TOP_LEVEL_OFFSET_X}+'
                              f'{y + QueryImagePlaceholder.TOP_LEVEL_OFFSET_Y}')
            self.drag_id = self.master.after(1000, self.stop_drag)

    def stop_drag(self):
        self.drag_id = ''

    @property
    def idx(self):
        return self.__idx


class Sidebar(customtkinter.CTkFrame):
    def __init__(self,
                 master,
                 width,
                 corner_radius):
        super(Sidebar, self).__init__(master=master, width=width, corner_radius=corner_radius)

        self.img = ImageTk.PhotoImage(Image.open('test_images/6a.png').resize((100, 100)))
        self.label_1 = customtkinter.CTkLabel(master=self, image=self.img)
        self.button_upload = customtkinter.CTkButton(master=self,
                                                     text="Upload a Garment",
                                                     command=None,
                                                     cursor='hand2')
        self.button_clear_all = customtkinter.CTkButton(master=self,
                                                        text='Clear All',
                                                        cursor='hand2')
        self.button_save = customtkinter.CTkButton(master=self, text='Save',
                                                   cursor='hand2')
        self.instructions_title = customtkinter.CTkLabel(self, text="Instructions",
                                                         text_font=("Roboto", "14"))
        self.instructions = customtkinter.CTkLabel(self,
                                                   text=instructions.INSTRUCTIONS_UPLOAD,
                                                   justify='left',
                                                   wraplength=200)
        self.label_mode = customtkinter.CTkLabel(master=self, text="Appearance Mode:")
        self.optionmenu = customtkinter.CTkOptionMenu(master=self,
                                                      values=["Light", "Dark", "System"],
                                                      command=self.change_appearance_mode,
                                                      cursor='hand2')
        customtkinter.set_appearance_mode("Dark")
        self.optionmenu.set("Dark")

    def build(self):
        self.pack(fill=tkinter.Y, side=tkinter.LEFT, expand=False, padx=(0, 5))
        self.pack_propagate(False)

        self.label_1.pack(pady=(30, 0))
        self.button_upload.pack(pady=(30, 0))
        self.button_clear_all.pack(pady=(5, 0))
        self.button_save.pack(pady=(5, 0))
        self.instructions_title.pack(pady=(220, 0))
        self.instructions.pack(pady=(20, 0))
        self.label_mode.pack(pady=(300, 0))
        self.optionmenu.pack(pady=(15, 0))

    def change_appearance_mode(self, new_appearance):
        customtkinter.set_appearance_mode(new_appearance)
        #TODO: Also change the pattern editor's frame color
        #TODO: Set the pattern preview's facecolor


class FrameESPA(customtkinter.CTkFrame):
    def __init__(self, master, height, corner_radius, fg_color):
        super(FrameESPA, self).__init__(master=master, height=height, corner_radius=corner_radius,
                                        fg_color=fg_color)
        img = Image.open('test_images/banner.png')
        img = ImageOps.contain(img, (1800, 70))
        self.img = ImageTk.PhotoImage(img)
        self.label = customtkinter.CTkLabel(master=self, image=self.img)

    def build(self):
        self.pack(side=tkinter.TOP, expand=False, fill=tkinter.BOTH)
        self.label.pack()


class FrameWatermark(customtkinter.CTkFrame):
    def __init__(self,
                 master,
                 corner_radius,
                 width,
                 height):
        super(FrameWatermark, self).__init__(master=master,
                                             corner_radius=corner_radius,
                                             width=width,
                                             height=height)
        self.img = ImageTk.PhotoImage(Image.open('test_images/imannequin.png').convert('RGBA'))
        self.label = customtkinter.CTkLabel(master=self, image=self.img)

    def build(self):
        self.pack(side=tkinter.TOP, pady=(0, 5))
        self.pack_propagate(False)
        self.label.place(x=5, y=5, relwidth=1, relheight=1)


class FrameQueryImagePlaceholder(customtkinter.CTkFrame):
    def __init__(self, master, width, height):
        super(FrameQueryImagePlaceholder, self).__init__(master=master, width=1000, height=900)

    def build(self):
        self.grid(row=0, column=0)


class FrameRetrievedPlaceholder(customtkinter.CTkFrame):
    def __init__(self, master, width, height):
        super(FrameRetrievedPlaceholder, self).__init__(master=master, width=width, height=height)
        self.label = customtkinter.CTkLabel(master=self, text='Retrieved Garments',
                                            text_font=('Roboto', 16))

    def build(self):
        self.pack(side=tkinter.RIGHT, anchor=tkinter.N, pady=(7, 0), padx=(0, 10))
        self.pack_propagate(False)
        self.label.pack(anchor=tkinter.CENTER, side=tkinter.TOP, pady=(7, 0))


class QueryImagePlaceholder(customtkinter.CTkToplevel):
    TOP_LEVEL_OFFSET_X = 285
    TOP_LEVEL_OFFSET_Y = 70

    def __init__(self, master):
        super(QueryImagePlaceholder, self).__init__(master=master)
        self.master = master
        self.geometry(f"325x318+{QueryImagePlaceholder.TOP_LEVEL_OFFSET_X}+{QueryImagePlaceholder.TOP_LEVEL_OFFSET_Y}")
        self.title('Query Image')
        self.wm_transient(master=master)
        self.drag_id = ''

        self.update_idletasks()

        self.frame = customtkinter.CTkFrame(master=self)
        self.frame.pack(side=tkinter.TOP, anchor=tkinter.CENTER)
        self.button_apply = customtkinter.CTkButton(master=self.frame, text='Apply', cursor='hand2')
        self.button_apply.pack()

        self.vispy_canvas = scene.SceneCanvas(keys='interactive',
                                              show=True,
                                              parent=self)
        self.vispy_canvas.native.pack(side=tkinter.TOP, fill=tkinter.BOTH,
                                      expand=True)
        self.vispy_view = self.vispy_canvas.central_widget.add_view(bgcolor=Layout.VISPY_CANVAS_BG_COLOR_DARK)
        self.text = None

        self.wm_protocol('WM_DELETE_WINDOW', disable_event)

    def dragging(self, event):
        if event.widget is self.master:
            if self.drag_id == '':
                pass
            else:
                self.master.after_cancel(self.drag_id)
                x = self.master.winfo_x()
                y = self.master.winfo_y()
                self.geometry(f'400x300+{x + QueryImagePlaceholder.TOP_LEVEL_OFFSET_X}+'
                              f'{y + QueryImagePlaceholder.TOP_LEVEL_OFFSET_Y}')
            self.drag_id = self.master.after(1000, self.stop_drag)

    def stop_drag(self):
        self.drag_id = ''

    def draw(self, kind, fname):
        self.clear()
        if kind == 'image':
            im = imread(fname)
            im_obj = vispy.scene.visuals.Image(im, parent=self.vispy_view)
            self.vispy_view.add(im_obj)
            self.vispy_view.camera = vispy.scene.PanZoomCamera(aspect=1)
            self.vispy_view.camera.flip = (0, 1, 0)
            self.vispy_view.camera.set_range()
            self.vispy_view.camera.zoom(1., (250, 250))
        else:
            self.text = customtkinter.CTkLabel(master=self, text='Please wait...')
            self.text.pack()
            vertices, faces, _, _ = vispy.io.read_mesh(fname)
            m = Mesh(vertices=vertices, faces=faces)
            mesh = vispy.scene.visuals.Mesh(vertices=m.vertices,
                                            shading='smooth',
                                            faces=m.faces)
            self.vispy_view.add(mesh)
            self.vispy_view.camera = vispy.scene.TurntableCamera(elevation=90, azimuth=0, roll=90)

    def clear(self):
        self.vispy_view.parent = None
        self.vispy_view = self.vispy_canvas.central_widget.add_view(bgcolor=Layout.VISPY_CANVAS_BG_COLOR_DARK)


class FrameGarmentInformation(customtkinter.CTkFrame):
    def __init__(self,
                 **kwargs):
        super(FrameGarmentInformation, self).__init__(**kwargs)
        self.label = customtkinter.CTkLabel(master=self, text='Information',
                                            text_font=('Roboto', 16))
        self.frame_text_placeholder = customtkinter.CTkFrame(master=self)

        self.text_name = customtkinter.CTkLabel(master=self.frame_text_placeholder,
                                                text='Name',
                                                text_font=('Roboto', 8),
                                                justify=tkinter.LEFT)
        self.text_category = customtkinter.CTkLabel(master=self.frame_text_placeholder,
                                                    text='Pattern Category',
                                                    text_font=('Roboto', 8),
                                                    justify=tkinter.LEFT)
        self.text_n_patterns = customtkinter.CTkLabel(master=self.frame_text_placeholder,
                                                      text='Number of Patterns',
                                                      text_font=('Roboto', 8),
                                                      justify=tkinter.LEFT)
        self.text_pattern_path = customtkinter.CTkLabel(master=self.frame_text_placeholder,
                                                        text='Pattern Path',
                                                        text_font=('Roboto', 8),
                                                        justify=tkinter.LEFT)
        for i in range(4):
            setattr(self, f'text_dummy_{i}', customtkinter.CTkEntry(master=self.frame_text_placeholder,
                                                                    justify=tkinter.RIGHT,
                                                                    text_font=('Roboto', 8),
                                                                    placeholder_text=f''))
        self.img_resized = None
        self.frame_image_preview = customtkinter.CTkFrame(master=self, width=115, height=115)
        self.default_img = Image.open('test_images/8.jpg')

        self.image_garment_preview = customtkinter.CTkLabel(master=self.frame_image_preview,
                                                            text='',
                                                            width=110,
                                                            height=110)
        self.frame_holder = customtkinter.CTkFrame(master=self, width=200, height=90)

        self.label_picked_texture = customtkinter.CTkLabel(master=self.frame_holder,
                                                           text_font=('Roboto', 8),
                                                           text='Selected Texture:')
        self.label_picked_texture_preview = customtkinter.CTkLabel(master=self.frame_holder,
                                                                   justify=tkinter.RIGHT,
                                                                   text_font=('Roboto', 8),
                                                                   text='',
                                                                   width=0, height=0)
        self.frame_mannequin_size = customtkinter.CTkFrame(master=self, width=200, height=100)
        self.size_var = tkinter.IntVar()
        self.label_mannequin_size = customtkinter.CTkLabel(master=self.frame_mannequin_size,
                                                           text='Choose a mannequin size',
                                                           text_font=('Roboto', 8),
                                                           justify=tkinter.CENTER)
        self.rb1 = customtkinter.CTkRadioButton(master=self.frame_mannequin_size, value=0, variable=self.size_var,
                                                text='Size 1', width=10, height=10)
        self.rb2 = customtkinter.CTkRadioButton(master=self.frame_mannequin_size, value=1, variable=self.size_var,
                                                text='Size 2', width=10, height=10)
        self.rb3 = customtkinter.CTkRadioButton(master=self.frame_mannequin_size, value=2, variable=self.size_var,
                                                text='Size 3', width=10, height=10)
        self.rb4 = customtkinter.CTkRadioButton(master=self.frame_mannequin_size, value=3, variable=self.size_var,
                                                text='Size 4', width=10, height=10)
        self.rb1.select()
        self.button_launch_editor = customtkinter.CTkButton(master=self, text='Launch 3D Editor', cursor='hand2')

        self.texture_setting = customtkinter.CTkButton(master=self, text='Select a Texture', cursor='hand2')

    def build(self):
        self.pack(side=tkinter.LEFT, anchor=tkinter.SW, pady=(7, 7), padx=(7, 0))
        self.pack_propagate(False)
        self.label.pack(anchor=tkinter.CENTER, pady=(5, 0))

        self.frame_text_placeholder.pack(pady=(10, 0))
        self.frame_text_placeholder.grid_columnconfigure(0, weight=1)
        self.frame_text_placeholder.grid_columnconfigure(1, weight=3)
        self.text_name.grid(row=0, column=0, sticky=tkinter.W)
        self.text_category.grid(row=1, column=0, sticky=tkinter.W)
        self.text_n_patterns.grid(row=2, column=0, sticky=tkinter.W)
        self.text_pattern_path.grid(row=3, column=0, sticky=tkinter.W)
        for i in range(4):
            getattr(self, f'text_dummy_{i}').grid(row=i, column=1, sticky=tkinter.E)

        self.frame_image_preview.pack(pady=(10, 0))
        self.frame_image_preview.pack_propagate(False)
        self.image_garment_preview.pack(anchor=tkinter.CENTER)
        self.frame_holder.pack(pady=(5, 5))
        self.label_picked_texture.grid(row=0, column=0)
        self.label_picked_texture_preview.grid(row=0, column=1)
        self.texture_setting.pack(pady=(0, 0))
        # self.button_select_mannequin.pack(pady=(5, 0))
        self.frame_mannequin_size.pack(pady=(20, 0))
        self.label_mannequin_size.grid(row=0, column=0, columnspan=2)
        self.rb1.grid(row=1, column=0, padx=(25, 5))
        self.rb2.grid(row=1, column=1, padx=(5, 25))
        self.rb3.grid(row=2, column=0, padx=(25, 5))
        self.rb4.grid(row=2, column=1, padx=(5, 25))
        self.button_launch_editor.pack(pady=(40, 0))

    def update_thumbnail(self, path):
        image_path = osp.join(path, str(Path(path).name)) + '.jpg'
        img_obj = Image.open(image_path)
        self.img_resized = ImageTk.PhotoImage(ImageOps.contain(img_obj, (100, 100)))
        self.image_garment_preview.configure(image=self.img_resized)
        self.image_garment_preview.pack()


class FramePatternPreview(customtkinter.CTkFrame):
    def __init__(self,
                 master,
                 width,
                 height,
                 corner_radius):
        super(FramePatternPreview, self).__init__(master=master,
                                                  width=width,
                                                  height=height,
                                                  corner_radius=corner_radius)
        self.label_title = customtkinter.CTkLabel(master=self, text='Pattern Preview',
                                                  text_font=('Roboto', 16))
        self.frame = customtkinter.CTkFrame(master=self, fg_color='#454545', corner_radius=0)
        self.label_instruction = customtkinter.CTkLabel(master=self.frame, text_font=('Roboto', 10),
                                                        text=instructions.INSTRUCTIONS_PATTERN_PREVIEW_SIMILAR,
                                                        wraplength=120,
                                                        justify=tkinter.LEFT)
        self.label_instruction_focus = customtkinter.CTkLabel(master=self.frame, text_font=('Roboto', 10),
                                                              text=instructions.INSTRUCTIONS_PATTERN_PREVIEW_FOCUS,
                                                              wraplength=120,
                                                              justify=tkinter.LEFT)
        self.label_instruction_zoom = customtkinter.CTkLabel(master=self.frame, text_font=('Roboto', 10),
                                                             text=instructions.INSTRUCTIONS_PATTERN_PREVIEW_ZOOM,
                                                             wraplength=120,
                                                             justify=tkinter.LEFT)
        self.label_instruction_escape = customtkinter.CTkLabel(master=self.frame, text_font=('Roboto', 10),
                                                               text=instructions.INSTRUCTIONS_PATTERN_PREVIEW_ESCAPE,
                                                               wraplength=120,
                                                               justify=tkinter.LEFT)
        self.interactive_preview = InteractivePatternViewer(master=self, figsize=(7.8, 5))

    def build(self):
        self.place(x=345, y=370)
        self.pack_propagate(False)
        self.label_title.pack(pady=(7, 0), padx=(0, 200))
        self.frame.pack(side=tkinter.LEFT, padx=(20, 0), anchor=tkinter.NW, pady=(9, 0))
        self.label_instruction.pack(pady=(20, 10))
        self.label_instruction_focus.pack(pady=(0, 10))
        self.label_instruction_zoom.pack(pady=(0, 10))
        self.label_instruction_escape.pack(pady=(0, 136))
        self.interactive_preview.widget.pack(side=tkinter.LEFT, padx=(0, 0))
        self.interactive_preview.draw()

    def draw_pattern(self, data):
        self.interactive_preview.draw(data)

    def bind_event(self, event_type, callback_fn):
        self.interactive_preview.f.canvas.mpl_connect(event_type, callback_fn)

    def clear(self):
        self.interactive_preview.clear()


class InteractivePatternViewer:
    MIN_X = 20.0
    MIN_Y = 20.0
    MAX_X = 20.0
    MAX_Y = 20.0

    def __init__(self,
                 master: Union[customtkinter.CTkFrame, customtkinter.CTkToplevel],
                 figsize=(9, 5)):
        self.f = Figure(figsize=figsize)
        self.f.patch.set_facecolor('#525252')

        self.pattern_preview = FigureCanvasTkAgg(self.f, master=master)
        self.ax = None
        self.annot = None
        # Maybe lines and line dict can be sampled from a Pattern model interface (?)
        # Will leave it blank for now and test it from a model class

        # Figure out; Is an editor required? YES

        # NOTE: An Editor class should contain the selected pattern's data and manage their contents from there.
        # The InteractivePatternViewer is merely an user interface to render the results and listen to events.
        # A PatternController will listen to these events and subsequently issue a command to the model interface
        # to manipulate its data.

    @property
    def widget(self):
        return self.pattern_preview.get_tk_widget()

    def draw(self,
             data=None,
             controller_fn=None):
        # Need to fill in the method that takes the data from the Model interface and then draws it.
        if data is not None:
            self.f.clear()
            self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            self.f.tight_layout()
            self.ax = self.f.add_subplot(autoscale_on=False)
            # For now, use a hand-picked value
            self.ax.set_facecolor('#343638')
            self.ax.axis('off')
            self.ax.set_aspect('equal')
            self.ax.set_xticks([])
            self.ax.set_yticks([])

            self.annot = self.ax.annotate("", (0, 0), (10, 10), xycoords='figure pixels',
                                          bbox=dict(boxstyle="round", fc="w"),
                                          arrowprops=dict(arrowstyle="->"))
            self.annot.set_visible(False)

            for collection in data:
                self.ax.add_collection(collection.line)

            x_min = min([l.min_x for l in data])
            y_min = min([l.min_y for l in data])

            x_max = max([l.max_x for l in data])
            y_max = max([l.max_y for l in data])

            self.ax.set_xlim([x_min - InteractivePatternViewer.MIN_Y, x_max + InteractivePatternViewer.MAX_X])
            self.ax.set_ylim([y_min - InteractivePatternViewer.MIN_Y, y_max + InteractivePatternViewer.MAX_Y])
            self.f.canvas.draw_idle()
        else:
            self.clear()

    def clear(self):
        self.f.clf()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        self.ax = self.f.add_subplot(autoscale_on=False, xlim=(0, 0), ylim=(0, 0))
        self.ax.set_facecolor('#343638')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.axis('tight')
        self.ax.axis('off')
        self.ax.set_aspect('equal')
        self.f.canvas.draw_idle()


'''Pattern editor states are defined below.'''

EDITOR_FONT_NORMAL = ('Roboto', 11)
EDITOR_FONT_BOLD = ('Roboto', 11, 'bold')
EDITOR_FONT_BOLD_WARNING = {'text_font': ('Roboto', 11, 'bold'),
                            'text_color': '#dbb240'}
EDITOR_FONT_BOLD_NOT_AVAILABLE = {'text_font': ('Roboto', 11, 'bold'),
                                  'text_color': '#cf1d11'}


class EditorStateNoPatternSelected:
    def __init__(self, master):
        self.master = master

    def build(self):
        pass

    def destroy(self):
        pass


class EditorStateGarmentBlouseSelected:
    def __init__(self, master):
        self.master = master
        self.label = None
        self.choices = None

    def build(self):
        self.label = customtkinter.CTkLabel(master=self.master, text='Click on the pattern\nyou want to change',
                                            text_font=EDITOR_FONT_BOLD)
        self.choices = customtkinter.CTkLabel(master=self.master, text='\u2022 Front\n\u2022 Back',
                                              text_font=EDITOR_FONT_NORMAL)
        self.label.pack(pady=(10, 0))
        self.choices.pack(pady=(10, 0))

    def destroy(self):
        self.label.pack_forget()
        self.choices.pack_forget()
        self.label = None
        self.choices = None
        self.master = None


class EditorStateGarmentDressSelected:
    def __init__(self, master):
        self.master = master
        self.label = None
        self.choices = None

    def build(self):
        self.label = customtkinter.CTkLabel(master=self.master,
                                            text='Click on the pattern\nyou want to change',
                                            text_font=EDITOR_FONT_BOLD)
        self.choices = customtkinter.CTkLabel(master=self.master,
                                              text='\u2022 Front\n\u2022 Back\n\u2022 Skirt Front\n\u2022'
                                                   ' Skirt Back',
                                              text_font=EDITOR_FONT_NORMAL)
        self.label.pack(pady=(10, 0))
        self.choices.pack(pady=(10, 0))

    def destroy(self):
        self.label.pack_forget()
        self.choices.pack_forget()
        self.label = None
        self.choices = None
        self.master = None


class EditorStateGarmentSkirtSelected:
    def __init__(self, master):
        self.master = master
        self.label = None
        self.choices = None

    def build(self):
        self.label = customtkinter.CTkLabel(master=self.master,
                                            text='Click on the pattern\nyou want to change',
                                            text_font=EDITOR_FONT_BOLD)
        self.choices = customtkinter.CTkLabel(master=self.master,
                                              text='\u2022 Skirt Front\n\u2022 Skirt Back',
                                              text_font=EDITOR_FONT_NORMAL)
        self.label.pack(pady=(10, 0))
        self.choices.pack(pady=(10, 0))

    def destroy(self):
        self.label.pack_forget()
        self.choices.pack_forget()
        self.label = None
        self.choices = None
        self.master = None


class ArmholeCollarOptions:
    def __init__(self, master):
        self.master = master
        self.select_message = None
        self.rb1 = None
        self.rb2 = None
        self.button_search = None
        self.button_replace = None

        self.choice_var = None
        self.last_choice = None

        self.pocket_select = None

    def build(self):
        self.choice_var = tkinter.IntVar()
        self.rb1 = customtkinter.CTkRadioButton(master=self.master, text='Armhole', text_font=EDITOR_FONT_NORMAL,
                                                variable=self.choice_var, value=0, width=15, height=15)
        self.rb2 = customtkinter.CTkRadioButton(master=self.master, text='Collar', text_font=EDITOR_FONT_NORMAL,
                                                variable=self.choice_var, value=1, width=15, height=15)

        self.pocket_select = customtkinter.CTkButton(master=self.master, text='Add accessories',
                                                     text_font=EDITOR_FONT_NORMAL,
                                                     cursor='hand2')
        self.select_message = customtkinter.CTkLabel(master=self.master,
                                                     text='Please select the region\n you want to change:',
                                                     text_font=EDITOR_FONT_BOLD)

        self.button_search = customtkinter.CTkButton(master=self.master, text='Search Alternative Curves',
                                                     text_font=EDITOR_FONT_NORMAL,
                                                     cursor='hand2')
        self.button_replace = customtkinter.CTkButton(master=self.master, text='Replace Curve',
                                                      text_font=EDITOR_FONT_NORMAL,
                                                      cursor='hand2')

        if self.last_choice is None:
            self.rb1.select()
        else:
            getattr(self, f'rb{self.last_choice+1}').select()
        self.select_message.pack(pady=(55, 0))
        self.rb1.pack(pady=(10, 0))
        self.rb2.pack()
        self.button_search.pack(pady=(50, 0))
        self.button_replace.pack(pady=(10, 0))
        self.pocket_select.pack(pady=(10, 0))

    def destroy(self):
        self.select_message.pack_forget()
        self.rb1.pack_forget()
        self.rb2.pack_forget()
        self.pocket_select.pack_forget()
        self.button_search.pack_forget()
        self.button_replace.pack_forget()
        self.select_message = None
        self.rb1 = None
        self.rb2 = None
        self.button_search = None
        self.button_replace = None
        self.master = None


class SkirtOptions:
    def __init__(self, master):
        self.master = master
        self.label = None

    def build(self):
        self.label = customtkinter.CTkLabel(master=self.master, text='The sides region will\n'
                                                                     'automatically be changed!',
                                            **EDITOR_FONT_BOLD_WARNING)
        self.label.pack(pady=(50, 0))

    def destroy(self):
        self.label.pack_forget()
        self.label = None


class NotAvailableOptions:
    def __init__(self, master):
        self.master = master
        self.label = None

    def build(self):
        self.label = customtkinter.CTkLabel(master=self.master, text='You cannot change\nthis pattern!',
                                            **EDITOR_FONT_BOLD_NOT_AVAILABLE)
        self.label.pack(pady=(50, 0))

    def destroy(self):
        self.label.pack_forget()
        self.label = None


class FrameEditorView(customtkinter.CTkFrame):
    """Code related to the pattern editor"""
    __STATES_ENUM = {'NO_GARMENT_SELECTED':         EditorStateNoPatternSelected,
                     'GARMENT_BLOUSE_SELECTED':     EditorStateGarmentBlouseSelected,
                     'GARMENT_DRESS_SELECTED':      EditorStateGarmentDressSelected,
                     'GARMENT_SKIRT_SELECTED':      EditorStateGarmentSkirtSelected}

    __OPTIONS_ENUM = {'front': ArmholeCollarOptions,
                      'back': ArmholeCollarOptions,
                      'skirt front': NotAvailableOptions,
                      'skirt back': NotAvailableOptions,
                      'collar': NotAvailableOptions,
                      'sleevel': NotAvailableOptions,
                      'sleever': NotAvailableOptions,
                      'cuffl': NotAvailableOptions,
                      'cuffr': NotAvailableOptions}

    def __init__(self, master, **kwargs):
        super(FrameEditorView, self).__init__(**kwargs)
        self.__state = None
        self.__widget = None
        self.__options_widget = None
        self.initialize_view_state()
        self.__build_layout_from_state()

    def initialize_view_state(self):
        self.__state = 'NO_GARMENT_SELECTED'

    def __build_layout_from_state(self):
        self.__widget = FrameEditorView.__STATES_ENUM[self.__state](master=self)
        self.__widget.build()

    def __update(self, state):
        self.__state = state
        self.__clear()
        self.__widget = FrameEditorView.__STATES_ENUM[self.__state](master=self)
        self.__widget.build()

    def __clear(self):
        self.__widget.destroy()

    def build(self):
        self.place(x=1500, y=415)
        self.pack_propagate(False)
        self.__widget.build()
        if self.__options_widget is not None:
            self.__options_widget.build()

    def update_state(self, state):
        self.__update(state)

    def reset(self):
        self.__update('NO_GARMENT_SELECTED')
        if self.__options_widget is not None:
            self.__options_widget.destroy()
            self.__options_widget = None

    def update_option(self, option):
        if self.__options_widget is not None:
            self.__options_widget.destroy()

        if self.__state != 'NO_GARMENT_SELECTED':
            self.__options_widget = FrameEditorView.__OPTIONS_ENUM[option](master=self)
            self.__options_widget.build()

    @property
    def options_widget(self):
        if self.__options_widget is not None:
            return self.__options_widget
        return None


class ShapeSimilarityWindow(customtkinter.CTkToplevel):
    def __init__(self,
                 relevant):
        super(ShapeSimilarityWindow, self).__init__()
        self.title('Relevant Patterns')
        self.geometry('1290x315+620+72')
        self.frame = None
        self.__relevant = relevant

    def build(self):
        self.frame = customtkinter.CTkFrame(master=self, width=1280, height=305, corner_radius=9)
        self.frame.pack(anchor=tkinter.CENTER)
        for i in range(4):
            setattr(self, f'frame_info_{i + 1}', customtkinter.CTkFrame(master=self.frame))
            getattr(self, f'frame_info_{i + 1}').grid(row=5, column=i, pady=10, padx=10)
            pth = self.__relevant.suggested[i]
            img_path = osp.join(pth, Path(pth).name) + '.jpg'
            img_obj = ImageOps.contain(Image.open(img_path), (250, 250))
            setattr(self, f'img_out_{i + 1}', ImageTk.PhotoImage(img_obj))
            setattr(self, f'out_img_{i + 1}', customtkinter.CTkButton(getattr(self, f'frame_info_{i + 1}'),
                                                                      image=getattr(self, f'img_out_{i + 1}'),
                                                                      text="",
                                                                      corner_radius=5, width=265, height=265,
                                                                      fg_color="#2b2b2b",
                                                                      hover_color="#757272"))
            getattr(self, f'out_img_{i + 1}').grid(row=5, column=0, pady=10, padx=10)

    def run(self):
        self.mainloop()


class WindowAlternativeCurves(customtkinter.CTkToplevel):

    GEOMETRY = (1218, 497)
    OFFSET = (636, 445)

    def __init__(self, master):
        super(WindowAlternativeCurves, self).__init__(master=master)
        self.geometry(f'{WindowAlternativeCurves.GEOMETRY[0]}x{WindowAlternativeCurves.GEOMETRY[1]}+'
                      f'{WindowAlternativeCurves.OFFSET[0]}+{WindowAlternativeCurves.OFFSET[1]}')
        self.title('Curve Editor')

        self.grid = None
        self.__selected_alt_curve = None

    def build(self, data):
        self.grid = MplFrameGrid(master=self, data_list=data,
                                 mpl_width=60, mpl_height=64, column_size=5)
        self.grid.build_grid()


class WindowTextureChoose(customtkinter.CTkToplevel):
    def __init__(self, master):
        super(WindowTextureChoose, self).__init__(master=master)
        self.title('Texture Picker')
        self.geometry('1218x497+636+445')
        self.button_add = customtkinter.CTkButton(master=self, text='Choose a different texture from your files',
                                                  cursor='hand2')
        self.button_add.pack()
        self.vs_frame = VerticalScrolledFrame(self)
        self.vs_frame.pack(side=tkinter.BOTTOM, fill=tkinter.BOTH, expand=tkinter.TRUE)

    def build(self, data, callback_fn):

        columns = len(data) if len(data) < 6 else 6
        rows = (len(data) // 6) + 1

        for i in range(rows):
            for j in range(columns):
                try:
                    img = Image.open(data[i * 6 + j])
                    img_obj = ImageTk.PhotoImage(ImageOps.contain(img, (150, 150)))
                    button = customtkinter.CTkButton(master=self.vs_frame.interior,
                                                     text='',
                                                     cursor='hand2',
                                                     image=img_obj,
                                                     width=160,
                                                     height=160,
                                                     command=partial(callback_fn, data[i * 6 + j]))
                    button.grid(row=i, column=j, padx=(60 if j == 0 else 10, 10), pady=(10, 10))
                except IndexError:
                    continue


class WindowAccessoryEditor(customtkinter.CTkToplevel):
    def __init__(self, master, width, height):
        super(WindowAccessoryEditor, self).__init__(master=master)
        self.title('Accessory Editor')
        self.geometry(f'{width}x{height}')
        self.f = None
        self.pattern_preview = None
        self.ax = None
        self.model = None
        self.canvas = None
        self.accessory = None
        self.patch = None
        self.markers = None
        self._ind = None
        self.background = None
        self.epsilon = 20
        self.max_dist = 300.0
        self.pocketlabel = None
        self.accessory_optionmenu = None
        self.scale_slider = None

    def build(self, figsize, model, accessory):
        # self.place(x=150, y=150)
        self.pocketlabel = customtkinter.CTkLabel(self, text="Pockets")
        self.pocketlabel.pack(padx=20, pady=0)
        self.accessory_optionmenu = customtkinter.CTkOptionMenu(self,
                                                                values=accessory.available_accessories)
        self.accessory_optionmenu.pack(padx=20, pady=0, side=tkinter.LEFT)

        self.scale_slider = customtkinter.CTkSlider(master=self, from_=4.0, to=150., number_of_steps=200)
        self.scale_slider.pack(side=tkinter.LEFT)
        self.scale_slider.focus()
        self.model = model
        self.accessory = accessory
        self.f = Figure(figsize=(6, 6))
        self.f.set_facecolor('#525252')
        self.ax = self.f.add_subplot(111)
        self.ax.set_facecolor('#525252')
        self.ax.axis('off')
        self.ax.axis('tight')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas = FigureCanvasTkAgg(self.f, master=self)
        self.canvas.get_tk_widget().pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=1)
        self.scatter = None
        codes, self.verts = zip(*self.accessory.path_data)

        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.draw()

    def draw(self):
        self.ax.clear()
        self.ax.set_aspect('equal')
        m = self.model.ind_pat.patterns[self.model.selected_region]
        self.ax.plot(m[:, 0], m[:, 1])
        self.markers = self.ax.scatter(np.array(self.verts)[:, 0], np.array(self.verts)[:, 1], color='r')
        self.lines = self.ax.plot(np.array(self.verts)[:-1, 0], np.array(self.verts)[:-1, 1])
        self.ax.axis('off')
        # self.ax.axis('tight')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()

    def update_background(self):
        self.background = self.f.canvas.copy_from_bbox(self.ax.bbox)

    def on_update(self):
        codes, self.verts = zip(*self.accessory.path_data)
        self.verts = list(self.verts)
        self.draw()

    def on_button_press(self, event):
        """Callback for mouse button presses."""
        if (event.inaxes is None
                or event.button != MouseButton.LEFT):
            return
        self._ind = self.get_ind_under_point(event)

    def get_ind_under_point(self, event):
        """
        Return the index of the point closest to the event position or *None*
        if no point is within ``self.epsilon`` to the event position.
        """
        # display coords
        xy = np.asarray(self.verts)
        # xyt = self.pathpatch.get_transform().transform(xy)
        xt, yt = xy[:, 0], xy[:, 1]
        d = np.sqrt((xt - event.xdata)**2 + (yt - event.ydata)**2)
        ind = d.argmin()

        if d[ind] >= self.epsilon:
            ind = None

        return ind

    def on_button_release(self, event):
        """Callback for mouse button releases."""
        if event.button != MouseButton.LEFT:
            return
        self._ind = None

    def on_mouse_move(self, event):
        """Callback for mouse movements."""
        if (self._ind is None
                or event.inaxes is None
                or event.button != MouseButton.LEFT):
            return

        vertices = list(self.verts)
        if self._ind == len(vertices) - 1:
            last_x, last_y = vertices[self._ind]
            dx, dy = event.xdata - last_x, event.ydata - last_y
            # distance_accessory_garment
            m = self.model.ind_pat.patterns[self.model.selected_region]
            center_garment = np.mean(m, axis=0)
            center_accessory = vertices[-1]
            distance = np.sqrt(
                (center_garment[0] - (center_accessory[0] + dx)) ** 2 + (
                            center_garment[1] - (center_accessory[1] + dy)) ** 2)
            if distance > self.max_dist:
                return

            for idx, v in enumerate(vertices):
                vx, vy = v
                vertices[idx] = vx + dx, vy + dy
            self.accessory.translate(dx, dy)
        self.verts = vertices
        self.draw()


class UI:
    """The main user interface. All layout components will be created here."""
    def __init__(self, test_shown=False):
        self.layout = Layout(title='i-Mannequin')

        if test_shown:
            self.__test()

    def run(self):
        self.layout.root.mainloop()

    def button_press(self):
        self.layout.show()

    def __test(self):
        self.layout.show()
        self.layout.frame_pattern_editor.update_state('NO_GARMENT_SELECTED')


if __name__ == '__main__':
    ui = UI(test_shown=False)
    ui.run()
