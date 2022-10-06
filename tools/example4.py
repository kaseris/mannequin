import logging
import os
import os.path as osp
from functools import partial

import tkinter
import tkinter.messagebox
import customtkinter
from tkinter import filedialog
import tkinter.ttk as ttk
import tkinter.font as tkfont

from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from mannequin.retrieval2d.retrieval_dimis import *
from mannequin.fileio.fileio import read_coords_from_txt
from PIL import Image, ImageTk

import vispy
import vispy.scene
from vispy.io import imread

from infer_retrieval import infer
from utils import get_model_name
# import vispy.visuals
vispy.use(app='tkinter')

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATH = '/home/kaseris/Documents/dev/mannequin/tools'
DATABASE_PATH = '/home/kaseris/Documents/GANAS_GUI/database'
IMAGES_PATH = '/home/kaseris/Documents/fir/DIMIS'


def similarity(query, retrieved, ss_mat):
    if ss_mat[retrieved, query] <= 0.0:
        return ss_mat[query, retrieved]
    return ss_mat[retrieved, query]


def create_ss_matrix(path):
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            l = line.strip().split(',')
            if idx == 0:
                ss = np.zeros((len(l) + 1, len(l) + 1))
            ss[idx, idx + 1:] = [float(el) for el in l]

    return ss


ss_dict_name_to_idx = {'dress': {'DD0332': 0,
                                 'GNSS': 1,
                                 'Q5751Á': 2,
                                 'Q6089': 3,
                                 'Q6109': 4,
                                 'Q6117': 5,
                                 'Q6362': 6,
                                 'Q6435': 7,
                                 'Q6446': 8,
                                 'Q6856': 9},
                       'blouse': {'CJ12566': 0,
                                  'LAURIE': 1,
                                  'Q5134': 2,
                                  'Q6431': 3,
                                  'Q7180': 4,
                                  'Q8634': 5,
                                  'Q9383': 6,
                                  'Q9393': 7,
                                  'Q9398': 8,
                                  'Q9407': 9,
                                  'Q9410': 10,
                                  'Q9414': 11,
                                  'Q9416': 12,
                                  'Q9432': 13,
                                  'Q9434': 14,
                                  'Q9435': 15,
                                  'Q9437': 16,
                                  'Q9409': 17,
                                  'Q9020': 18},
                       'skirt': {'Q7276': 0,
                                 'Q6281': 1,
                                 'Q6549': 2,
                                 'Q6797': 3,
                                 'Q7062': 4,
                                 'Q7063': 5,
                                 'Q7082': 6,
                                 'Q7092': 7,
                                 'Q7127': 8,
                                 'Q7343': 9,
                                 'Q7398': 10,
                                 'a3600': 11,
                                 'Q7064': 12,
                                 'Q7835': 13}}

ss_dict_idx_to_name = {'dress': {0: 'DD0332',
                                 1: 'GNSS',
                                 2: 'Q5751',
                                 3: 'Q6089',
                                 4: 'Q6109',
                                 5: 'Q6117',
                                 6: 'Q6362',
                                 7: 'Q6435',
                                 8: 'Q6446',
                                 9: 'Q6856'},
                       'blouse': {0: 'CJ12566',
                                  1: 'LAURIE',
                                  2: 'Q5134',
                                  3: 'Q6431',
                                  4: 'Q7180',
                                  5: 'Q8634',
                                  6: 'Q9383',
                                  7: 'Q9393',
                                  8: 'Q9398',
                                  9: 'Q9407',
                                  10: 'Q9410',
                                  11: 'Q9414',
                                  12: 'Q9416',
                                  13: 'Q9432',
                                  14: 'Q9434',
                                  15: 'Q9435',
                                  16: 'Q9437',
                                  17: 'Q9409',
                                  18: 'Q9020'},
                       'skirt': {0: 'Q7276',
                                 1: 'Q6281',
                                 2: 'Q6549',
                                 3: 'Q6797',
                                 4: 'Q7062',
                                 5: 'Q7063',
                                 6: 'Q7082',
                                 7: 'Q7092',
                                 8: 'Q7127',
                                 9: 'Q7343',
                                 10: 'Q7398',
                                 11: 'a3600',
                                 12: 'Q7064',
                                 13: 'Q7835'}}


class Model:

    def __init__(self, file_name=None):

        self.data = []
        self.object_type = None
        if file_name is None:
            # Define unit cube.

            self.data = []
        else:
            self.load_file(file_name)

    def clear(self):
        self.data = []

    def load_file(self, file_name, object_type='mesh'):
        '''Load mesh from file
        '''
        if object_type == 'mesh':
            vertices, faces, _, _ = vispy.io.read_mesh(file_name)
            self.data.append(Mesh(vertices, faces))
            self.object_type = 'mesh'
        elif object_type == 'image':
            img_data = imread(file_name)
            self.data.append(img_data)
            self.object_type = 'image'

    def get_bounding_box(self):
        bbox = self.data[0].bounding_box
        for mesh in self.data[1:]:
            for i in range(len(bbox)):
                x_i = mesh.bounding_box[i]
                bbox[i][0] = min([bbox[i][0], min(x_i)])
                bbox[i][1] = max([bbox[i][1], max(x_i)])

        return bbox


class Mesh:

    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces
        self.bounding_box = self.get_bounding_box()

    def get_vertices(self):
        vertices = []
        for face in self.faces:
            vertices.append([self.vertices[ivt] for ivt in face])

        return vertices

    def get_line_segments(self):
        line_segments = set()
        for face in self.faces:
            for i in range(len(face)):
                iv = face[i]
                jv = face[(i+1)%len(face)]
                if jv > iv:
                    edge = (iv, jv)
                else:
                    edge = (jv, iv)

                line_segments.add(edge)

        return [[self.vertices[edge[0]-1], self.vertices[edge[1]-1]] for edge in line_segments]

    def get_bounding_box(self):
        v = [vti for face in self.get_vertices() for vti in face]
        bbox = []
        for i in range(len(self.vertices[0])):
            x_i = [p[i] for p in v]
            bbox.append([min(x_i), max(x_i)])

        return bbox


class View:

    def __init__(self, model=None):

        if model is None:
            model = Model()
        self.model = model
        self.canvas = None
        self.vpview = None

    def clear(self):
        if self.vpview is not None:
            self.vpview.parent = None

        self.vpview = self.canvas.central_widget.add_view(bgcolor='#4a4949')
        # vispy.scene.visuals.XYZAxis(parent=self.vpview.scene)

    def plot(self, types="solid"):
        self.clear()
        # if isinstance(types, (str,)):
        #     types = [s.strip() for s in types.split('+')]
        if self.model.object_type == 'mesh':
            for mesh in self.model.data:
                msh = vispy.scene.visuals.Mesh(vertices=mesh.vertices,
                                               shading='smooth',
                                               faces=mesh.faces)
                self.vpview.add(msh)
            self.vpview.camera = vispy.scene.TurntableCamera(parent=self.vpview.scene)
        else:
            for im_data in self.model.data:
                image = vispy.scene.visuals.Image(im_data,
                                                  parent=self.vpview)
                self.vpview.add(image)
            self.vpview.camera = vispy.scene.PanZoomCamera(aspect=1)
            self.vpview.camera.flip = (0, 1, 0)
            self.vpview.camera.set_range()
            self.vpview.camera.zoom(1.0, (250, 200))


class Controller:
    TOP_LEVEL_OFFSET_X = 297
    TOP_LEVEL_OFFSET_Y = 70

    def __init__(self, view=None, parent=None):

        root = customtkinter.CTkToplevel(parent)
        root.geometry(f"325x370+{Controller.TOP_LEVEL_OFFSET_X}+{Controller.TOP_LEVEL_OFFSET_Y}" )
        root.title("Query Garment")

        if view is None:
            view = View()

        f1 = customtkinter.CTkFrame(root)
        f1.pack(side=tkinter.TOP, anchor=tkinter.CENTER)
        f3 = customtkinter.CTkFrame(f1)
        f3.pack(side=tkinter.TOP, anchor=tkinter.CENTER, padx=(0, 0))
        self.file_name = None
        button_apply = customtkinter.CTkButton(f3, text="apply", command=self.apply)
        button_apply.pack()
        canvas = vispy.scene.SceneCanvas(
            keys='interactive', show=True, parent=root)
        canvas.native.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        view.canvas = canvas
        root.update_idletasks()

        self.parent = parent
        self.root = root
        self.view = view
        self.model = view.model
        self.drag_id = ''
        self.root.protocol('WM_DELETE_WINDOW', self.disable_event)
        self.root.wm_transient(self.parent)

        view.plot()

    def dragging(self, event):
        if event.widget is self.parent:
            if self.drag_id == '':
                logging.info(f'gamas?')
            else:
                self.parent.after_cancel(self.drag_id)
                x = self.parent.winfo_x()
                y = self.parent.winfo_y()
                logging.info(f"Window position({x}, {y})")
                self.root.geometry(f'400x300+{x + Controller.TOP_LEVEL_OFFSET_X}+{y + Controller.TOP_LEVEL_OFFSET_Y}')
            self.drag_id = self.parent.after(1000, self.stop_drag)

    def stop_drag(self):
        self.drag_id = ''

    def render(self):
        self.root.mainloop()

    def disable_event(self):
        pass

    def open(self):
        file_name = tkinter.filedialog.askopenfilename(title="Select file to open",
                                                       filetypes=(("OBJ files", "*.obj"),
                                                                  ("STL Files", "*.stl"),
                                                                  ("JPEG Image", "*.jpg"),
                                                                  ("JPEG Image", "*.jpeg"),
                                                                  ("all files", "*.*")))
        logging.info(f'file_name: {file_name}')
        if Path(file_name).suffix == '.obj' or Path(file_name).suffix == '.stl':
            object_type = 'mesh'
        else:
            object_type = 'image'
        logging.info(f'object_type: {object_type}')
        self.parent.modify_scanned_file(file_name)
        self.model.clear()
        self.model.load_file(file_name, object_type=object_type)
        self.view.plot()
        self.parent.clear_images()
        self.parent._scanned_file = file_name

    def exit(self):
        self.model.clear()
        self.root.model = None
        self.view.clear()
        self.root.view = None
        self.root.destroy()

    def modifyFileName(self, filename):
        self.file_name = filename

    def apply(self):
        self.parent.retrieve()


def setMaxWidth(stringList, element):
    try:
        f = tkfont.nametofont(element.cget("font"))
        zerowidth = f.measure("0")
    except:
        f = tkfont.nametofont(ttk.Style().lookup("TButton", "font"))
        zerowidth = f.measure("0") - 0.8

    w = max([f.measure(i) for i in stringList])/zerowidth
    element.config(width=int(w))


class App(customtkinter.CTk):

    WIDTH = 1845
    HEIGHT = 1060

    def __init__(self, model=None, view=None, controller=None):
        super().__init__()
        self.extractor = load_test_model()
        self.deep_feats, self.color_feats, self.labels = load_feat_db()
        self.clf = load_kmeans_model()

        self.title("i-Mannequin")
        self.attributes('-zoomed', True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        self._retrieved         = None
        self._selected_image    = None
        self._index             = None
        self._retrieved_3d      = None

        # ============ create two frames ============
        # configure grid layout (2x1)
        self.grid_columnconfigure(2, weight=1) # apo 1 -> 2
        self.grid_rowconfigure(1, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, rowspan=2, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self, width=5, corner_radius=4)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=(25, 0), pady=(0,18))

        self.frame_right_right = customtkinter.CTkFrame(master=self,
                                                        width=180,
                                                        corner_radius=4)
        self.frame_right_right.grid(row=0, column=2, sticky="nswe", pady=(0,18), padx=25)

        self.frame_lower_right = customtkinter.CTkFrame(master=self, corner_radius=4)
        self.frame_lower_right.grid(row=1, column=1, sticky="nswe", padx=(25, 0), pady=(0, 18))

        self.frame_lower_right_right = customtkinter.CTkFrame(master=self,
                                                              width=80,
                                                              corner_radius=4)
        self.frame_lower_right_right.grid(row=1, column=2, sticky="nswe", pady=(0, 18), padx=25)

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_rowconfigure(0, minsize=10)   # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)    # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing
        self.img = ImageTk.PhotoImage(Image.open("test_images/6a.png").resize((100, 100)))
        self.label_1 = customtkinter.CTkLabel(self.frame_left, image=self.img)
        self.label_1.grid(row=1, column=0, pady=(10, 0), padx=10)

        self.instructions_title = customtkinter.CTkLabel(self.frame_left, text="Instructions",
                                                         text_font=("Roboto", "14"))
        self.instructions_title.grid(row=5, column=0, pady=(140, 0))
        self.instructions = customtkinter.CTkLabel(self.frame_left,
                                                   text="\u2022 Left Click on"
                                                        " a retrieved image\n to view garmen"
                                                        "t's infomation\n and its respective patterns.\n\n"
                                                        "\u2022 Click 'Enlarge' to enlarge\n the selected garment.\n\n"
                                                        "\u2022 Double-click on the pattern\n preview panel to view"
                                                        " similar\n garments.",
                                                   justify='left')
        self.instructions.grid(row=6, column=0, pady=(15, 0))

        self.label_mode = customtkinter.CTkLabel(master=self.frame_left, text="Appearance Mode:")
        self.label_mode.grid(row=9, column=0, pady=(310,0), padx=20)

        self.optionmenu_1 = customtkinter.CTkOptionMenu(master=self.frame_left,
                                                        values=["Light", "Dark", "System"],
                                                        command=self.change_appearance_mode)
        self.optionmenu_1.grid(row=10, column=0, pady=10, padx=20)

        # ============ frame_right ============
        def on_click(path, btn_idx, event=None):
            print(path)
            getattr(self, f'out_img{str(btn_idx)}').configure(fg_color="green")
        # configure grid layout (4x4)
        self.frame_right.rowconfigure((0, 1, 2), weight=0)
        self.frame_right.columnconfigure((0, 1, 2, 3), weight=0)

        self.query_img_info = customtkinter.CTkLabel(master=self.frame_right,
                                                     text="Query image",
                                                     text_font=("Roboto", 16))
        self.query_img_info.grid(row=0, column=0, columnspan=4, pady=10)
        self.query_img_info.custom_bind('<Double-Button-1>', lambda: print('Double Click'))
        self.frame_info = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_info.grid(row=1, column=0, columnspan=4, pady=10, padx=10)
        self.img_query = ImageTk.PhotoImage(Image.open("test_images/bg_image.png").resize((300, 300)))
        self.query_img = customtkinter.CTkLabel(self.frame_info, image=self.img_query)
        self.query_img.grid(row=1, column=0, pady=(10, 40), padx=10)

        self.retrieved_label = customtkinter.CTkLabel(master=self.frame_right_right, text="Retrieved garments",
                                                      text_font=('Roboto', 16)).grid(columnspan=4, pady=10)

        for i in range(4):
            setattr(self, f'frame_info_{i + 1}', customtkinter.CTkFrame(master=self.frame_right_right))
            getattr(self, f'frame_info_{i + 1}').grid(row=5, column=i, pady=10, padx=10)
            setattr(self, f'img_out_{i + 1}',
                    ImageTk.PhotoImage(Image.open("test_images/bg_image.png").resize((250, 250))))
            setattr(self, f'out_img_{i + 1}', customtkinter.CTkButton(getattr(self, f'frame_info_{i + 1}'),
                                                                      image=getattr(self, f'img_out_{i + 1}'), text="",
                                                                      corner_radius=5, width=265, height=265,
                                                                      fg_color="#6687d9",
                                                                      hover_color="#1751e3",
                                                                      command=partial(self.onClickGarmentButton, i+1)))
            getattr(self, f'out_img_{i + 1}').grid(row=5, column=0, pady=10, padx=10)

        self.enlarge_button = customtkinter.CTkButton(master=self.frame_right_right, text="Enlarge")
        self.enlarge_button.grid(row=6, column=0, pady=(10, 0), columnspan=4)

        self.optionmenu_1.set("Dark")

        # Frame lower right

        self.box_name = customtkinter.CTkLabel(master=self.frame_lower_right, text="Information",
                                               text_font=('Roboto', 16))
        self.box_name.grid(columnspan=2, pady=10)

        self.pattern_name_title = customtkinter.CTkLabel(master=self.frame_lower_right, text="Name: ",
                                                         width=12)
        self.pattern_name_title.grid(row=2, column=0, sticky='e', padx=7)

        self.pattern_category_title = customtkinter.CTkLabel(master=self.frame_lower_right, text="Pattern Category: ",
                                                             width=12)
        self.pattern_category_title.grid(row=3, column=0, sticky='e', padx=7)

        self.pattern_number_title = customtkinter.CTkLabel(master=self.frame_lower_right, text="Number of patterns: ",
                                                           width=12)
        self.pattern_number_title.grid(row=4, column=0, sticky='e', padx=7)

        self.pattern_path_title = customtkinter.CTkLabel(master=self.frame_lower_right, text="Pattern Path: ",
                                                         width=12)
        self.pattern_path_title.grid(row=5, column=0, sticky='e', padx=7)

        self.pattern_name = customtkinter.CTkLabel(master=self.frame_lower_right, text="")
        self.pattern_name.grid(row=2, column=1)

        self.pattern_category = customtkinter.CTkLabel(master=self.frame_lower_right, text="")
        self.pattern_category.grid(row=3, column=1)

        self.pattern_number = customtkinter.CTkLabel(master=self.frame_lower_right, text="")
        self.pattern_number.grid(row=4, column=1)

        self.pattern_path = customtkinter.CTkLabel(master=self.frame_lower_right, text="", wraplength=200,
                                                   justify='left')
        self.pattern_path.grid(row=5, column=1)

        self.selected_image_preview_obj = ImageTk.PhotoImage(Image.open('test_images/bg_image.png').resize((180, 180)))
        self.selected_image_preview = customtkinter.CTkLabel(master=self.frame_lower_right,
                                                             text="",
                                                             justify='right',
                                                             image=self.selected_image_preview_obj)
        self.selected_image_preview.grid(row=6, column=0, columnspan=3, pady=(40, 0))

        self.finalize_button = customtkinter.CTkButton(master=self.frame_lower_right, text="Finalize")
        self.finalize_button.grid(row=7, column=0, pady=(20, 0), columnspan=4)

        # Frame lower right right
        self.pattern_preview_title = customtkinter.CTkLabel(master=self.frame_lower_right_right, text="Patterns",
                                                            text_font=('Roboto', 16)).grid(column=1, sticky='n',
                                                                                           pady=10)

        self.f = Figure(figsize=(5, 5))
        self.f.canvas.mpl_connect('button_press_event', self.onDoubleClickCanvas)
        self.f.patch.set_facecolor('#343638')
        self.pattern_preview = FigureCanvasTkAgg(self.f, master=self.frame_lower_right_right)
        self.pattern_preview.get_tk_widget().grid(sticky='n', padx=(370), column=1)

        self._scanned_file = None

        self.model = None
        self.view = None
        self.controller = Controller(view=self.view, parent=self)
        self.resizable(False, False)
        self.bind('<Configure>', self.controller.dragging)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Upload a Garment",
                                                command=self.controller.open)
        self.button_1.grid(row=2, column=0, pady=(50, 10), padx=20)

    def modify_scanned_file(self, filename):
        self._scanned_file = filename

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def on_closing(self, event=0):
        self.destroy()

    def load_image(self, path, image_size):
        return ImageTk.PhotoImage(Image.open(path).resize((image_size, image_size)))

    def onClickEnlarge(self, path):
        enlarged_image_window = customtkinter.CTkToplevel(self)
        enlarged_image_window.title('Enlarged Image')
        enlarged_image_window.geometry("700x700")
        img = ImageTk.PhotoImage(Image.open(path).resize((700, 700)))
        label = tkinter.Label(master=enlarged_image_window, image=img)
        label.pack()
        enlarged_image_window.mainloop()

    def onClickDetails(self, idx):
        logging.info(f'self._retrieved[idx-1]: {self._retrieved[idx - 1]}')
        if not isinstance(self._retrieved[idx - 1], str):
            self.pattern_path.configure(text=self._retrieved[idx - 1][0])
            self.pattern_name.configure(text=osp.basename(self._retrieved[idx - 1][0]).split('.')[0])
            _selected = self._retrieved[idx - 1][0]
        else:
            self.pattern_path.configure(text=self._retrieved[idx - 1])
            self.pattern_name.configure(text=osp.basename(self._retrieved[idx - 1]).split('.')[0])
            _selected = self._retrieved[idx - 1]
        logging.info(f'_selected: {_selected}')
        database = '/home/kaseris/Documents/GANAS_GUI/database'
        filenames = []
        for root, dirs, files in os.walk(database):
            for name in files:
                filenames.append(os.path.join(root, name))

        found = [a for a in filenames if os.path.basename(_selected) in a]
        p = Path(found[0]).parent
        for cat in ['dress', 'skirt', 'blouse']:
            if cat in str(p):
                self.pattern_category.configure(text=cat)
        # Read the individual patterns
        ind_patterns = os.path.join(p, 'individual patterns')
        pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                         'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']
        coords_list = []
        for f in pattern_files:
            if f in os.listdir(ind_patterns):
                coords_list.append(read_coords_from_txt(os.path.join(ind_patterns, f), delimiter=','))
        self.pattern_number.configure(text=str(len(coords_list)))
        self.f.clf()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        ax = self.f.add_subplot(autoscale_on=False, xlim=(0, 0), ylim=(0, 0))
        for pattern in coords_list:
            ax.plot(pattern[:, 0], pattern[:, 1], c='tab:blue')

        ax.set_facecolor('#343638')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('tight')
        ax.axis('off')
        ax.set_aspect('equal')
        self.pattern_preview.draw()

    def onClickGarmentButton(self, index):
        print(f'You clicked button number: {index}')
        self._index = index
        if not isinstance(self._retrieved[index - 1], str):
            self.enlarge_button.configure(command=partial(self.onClickEnlarge, self._retrieved[index - 1][0]))
            img_path = self._retrieved[index - 1][0]
        else:
            self.enlarge_button.configure(command=partial(self.onClickEnlarge, self._retrieved[index - 1]))
            img_path = self._retrieved[index - 1]
            img_path = get_model_name(img_path)
            img_path = osp.join(IMAGES_PATH, img_path) + '.jpg'
        logging.info(f'img_path: {img_path}')
        self.onClickDetails(index)
        img_obj = Image.open(img_path).resize((180, 180))
        photo_img = ImageTk.PhotoImage(img_obj)
        self.selected_image_preview_obj = photo_img
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

    def onClickRelevantGarmentButton(self, index):
        print(f'You clicked button number: {index}')
        self._index = index
        print(self.filenames)
        found = [a for a in self.filenames if os.path.basename(self._suggested[index]) in a]
        self.onClickDetails(index)
        img_path = osp.join(str(Path(found[0]).parent), self._suggested[index]) + '.jpg'
        img_obj = Image.open(img_path).resize((180, 180))
        photo_img = ImageTk.PhotoImage(img_obj)
        self.selected_image_preview_obj = photo_img
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

        p = Path(found[0]).parent
        for cat in ['dress', 'skirt', 'blouse']:
            if cat in str(p):
                self.pattern_category.configure(text=cat)
        # Read the individual patterns
        ind_patterns = os.path.join(p, 'individual patterns')
        pattern_files = ['front.xyz', 'back.xyz', 'skirt back.xyz', 'skirt front.xyz', 'sleever.xyz', 'sleevel.xyz',
                         'cuffl.xyz', 'cuffr.xyz', 'collar.xyz']
        coords_list = []
        for f in pattern_files:
            if f in os.listdir(ind_patterns):
                coords_list.append(read_coords_from_txt(os.path.join(ind_patterns, f), delimiter=','))
        self.pattern_number.configure(text=str(len(coords_list)))
        self.f.clf()
        self.f.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        self.f.tight_layout()
        ax = self.f.add_subplot(autoscale_on=False, xlim=(0, 0), ylim=(0, 0))
        for pattern in coords_list:
            ax.plot(pattern[:, 0], pattern[:, 1], c='tab:blue')

        ax.set_facecolor('#343638')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('tight')
        ax.axis('off')
        ax.set_aspect('equal')
        self.pattern_preview.draw()

    def clear_images(self):
        if not not self._retrieved:
            for i in range(4):
                getattr(self, f'out_img_{str(i+1)}').configure(image=None)

    def update_images(self):
        results = []
        for idx, item in enumerate(self._retrieved):
            if not isinstance(item, tuple):
                retrieved_path = item
                for name in os.listdir(IMAGES_PATH):
                    if get_model_name(retrieved_path) in name:
                        logging.info(f'{osp.join(IMAGES_PATH, name)}')
                        results.append(osp.join(IMAGES_PATH, name))
            else:
                retrieved_path, _ = item
                results.append(retrieved_path)
        logging.info(f'retrieved_path: {results}')
        for idx, retrieved_path in enumerate(results):
            retrieved_img = ImageTk.PhotoImage(Image.open(retrieved_path).resize((250, 250)))
            getattr(self, f'out_img_{str(idx+1)}').configure(image=retrieved_img)

    def retrieve(self):
        self.clear_images()

        self._retrieved = infer(self._scanned_file, k=4, object_type=self.controller.model.object_type)

        self.update_images()

    def onDoubleClickCanvas(self, event):
        if event.dblclick:
            child = customtkinter.CTkToplevel()
            child.title('Relevant Patterns')
            child.geometry('1220x380+670+65')

            #child.finalize_button = customtkinter.CTkButton(master=child, text="Finalize")
            #child.finalize_button.grid(row=6, column=0, pady=(10, 0), columnspan=4)

            for i in range(4):
                setattr(child, f'frame_info_{i + 1}', customtkinter.CTkFrame(master=child))
                getattr(child, f'frame_info_{i + 1}').grid(row=5, column=i, pady=10, padx=10)
                setattr(child, f'img_out_{i + 1}',
                        ImageTk.PhotoImage(Image.open("test_images/bg_image.png").resize((250, 250))))
                setattr(child, f'out_img_{i + 1}', customtkinter.CTkButton(getattr(child, f'frame_info_{i + 1}'),
                                                                           image=getattr(child, f'img_out_{i + 1}'),
                                                                           text="",
                                                                           corner_radius=5, width=265, height=265,
                                                                           fg_color="#6687d9",
                                                                           hover_color="#1751e3",
                                                                           command=partial(self.onClickRelevantGarmentButton, i)))
                getattr(child, f'out_img_{i + 1}').grid(row=5, column=0, pady=10, padx=10)

            path_to_ss = osp.join(DATABASE_PATH, self.pattern_category.text, f'ss_{self.pattern_category.text}.txt')
            selected_idx = ss_dict_name_to_idx[self.pattern_category.text][osp.basename(self._retrieved[self._index-1][0]).split('.')[0]]
            ss_mat = create_ss_matrix(path_to_ss)

            list_similarities = []
            for i in range(len(ss_mat)):
                list_similarities.append(similarity(selected_idx, i, ss_mat))
            arr = np.asarray(list_similarities)
            suggested = arr.argsort()[-4:]
            self._suggested = [ss_dict_idx_to_name[self.pattern_category.text][idx] for idx in suggested]
            database = '/home/kaseris/Documents/GANAS_GUI/database'
            self._suggested[0] = self.pattern_name.text
            self.filenames = []
            for root, dirs, files in os.walk(database):
                for name in files:
                    self.filenames.append(os.path.join(root, name))
            paths = []
            for idx, _ in enumerate(self._suggested):
                found = [a for a in self.filenames if os.path.basename(self._suggested[idx]) in a]
                photo_img = ImageTk.PhotoImage(Image.open(str(Path(found[0]).parent) + f'/{self._suggested[idx]}.jpg').resize((250, 250)))
                if idx == 0:
                    getattr(child, f'out_img_{idx + 1}').configure(image=self.selected_image_preview_obj)
                else:
                    getattr(child, f'out_img_{idx + 1}').configure(image=photo_img)

            child.mainloop()

    def start(self):
        self.mainloop()
        self.controller.render()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = App()
    app.start()
