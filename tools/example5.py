import copy
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

from mannequin.retrieval2d.retrieval_dimis import *
from PIL import Image, ImageTk

import vispy
import vispy.scene
from vispy.io import imread

import fusion
from infer_retrieval import infer
from interactive_mpl import InteractivePatternPreview
from editor import EditorApp
from query_mvc import Mesh, Controller
from shape_similarities_idx import ss_dict_name_to_idx, ss_dict_idx_to_name
from utils import similarity, create_ss_matrix

# import vispy.visuals
vispy.use(app='tkinter')

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATH = '/home/kaseris/Documents/dev/mannequin/tools'
DATABASE_PATH = '/home/kaseris/Documents/database/'
IMAGES_PATH = '/home/kaseris/Documents/fir/DIMIS'
NEW_DATABASE_PATH = '/home/kaseris/Documents/database/'


def handle_focus(event):
    return


def setMaxWidth(stringList, element):
    try:
        f = tkfont.nametofont(element.cget("font"))
        zerowidth = f.measure("0")
    except:
        f = tkfont.nametofont(ttk.Style().lookup("TButton", "font"))
        zerowidth = f.measure("0") - 0.8

    w = max([f.measure(i) for i in stringList]) / zerowidth
    element.config(width=int(w))


class App(customtkinter.CTk):
    WIDTH = 1845
    HEIGHT = 1060

    def __init__(self, model=None, view=None, controller=None):
        super().__init__()

        self.garment_paths = {'image_path': [],
                              'obj_path': [],
                              'category': [],
                              'name': []}
        with open(osp.join(NEW_DATABASE_PATH, 'paths/garment_paths.txt'), 'r') as f:
            for idx, line in enumerate(f):
                l = line.strip().split(', ')
                self.garment_paths['image_path'].append(osp.join(NEW_DATABASE_PATH, l[0][2:]))
                self.garment_paths['obj_path'].append(osp.join(NEW_DATABASE_PATH, l[1][2:]))
                self.garment_paths['category'].append(l[2])
                self.garment_paths['name'].append(l[3])

        self.title("i-Mannequin")
        self.attributes('-zoomed', True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        self._retrieved = None
        self._selected_image = None
        self._index = None
        self._retrieved_3d = None

        offsets = [(665, 124), (970, 124), (1275, 124), (1580, 124)]
        for i in range(4):
            setattr(self, f'retrieved_viewport{i + 1}', customtkinter.CTkToplevel(master=self))
            getattr(self, f'retrieved_viewport{i + 1}').geometry(f'282x314+{offsets[i][0]}+{offsets[i][1]}')
            getattr(self, f'retrieved_viewport{i + 1}').title(f'Garment {i + 1}')
            setattr(self, f'canvas{i + 1}', vispy.scene.SceneCanvas(keys='interactive',
                                                                    show=True,
                                                                    parent=getattr(self, f'retrieved_viewport{i + 1}')))
            getattr(self, f'canvas{i + 1}').native.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
            setattr(self, f'view{i + 1}', getattr(self, f'canvas{i + 1}').central_widget.add_view(bgcolor='#4a4949'))
            getattr(self, f'retrieved_viewport{i + 1}').update_idletasks()
            getattr(self, f'retrieved_viewport{i + 1}').wm_transient(self)
            getattr(self, f'view{i + 1}').camera = vispy.scene.cameras.PanZoomCamera(aspect=1)
            getattr(self, f'view{i + 1}').camera.flip = (0, 1, 0)
            getattr(self, f'view{i + 1}').camera.set_range()
            getattr(self, f'view{i + 1}').camera.zoom(1.0, (250, 200))

        # ============ create two frames ============
        # configure grid layout (2x1)
        self.grid_columnconfigure(2, weight=1)  # apo 1 -> 2
        self.grid_rowconfigure(1, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)
        self.frame_left.grid(row=0, column=0, rowspan=2, sticky="nswe")

        self.frame_right = customtkinter.CTkFrame(master=self, width=5, corner_radius=4)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=(25, 0), pady=(0, 18))

        self.frame_right_right = customtkinter.CTkFrame(master=self,
                                                        width=180,
                                                        corner_radius=4)
        self.frame_right_right.grid(row=0, column=2, sticky="nswe", pady=(0, 18), padx=25)

        self.frame_lower_right = customtkinter.CTkFrame(master=self, corner_radius=4)
        self.frame_lower_right.grid(row=1, column=1, sticky="nswe", padx=(25, 0), pady=(0, 18))

        self.frame_lower_right_right = customtkinter.CTkFrame(master=self,
                                                              width=80,
                                                              corner_radius=4)
        self.frame_lower_right_right.grid(row=1, column=2, sticky="nswe", pady=(0, 18), padx=25)

        # ============ frame_left ============

        # configure grid layout (1x11)
        self.frame_left.grid_rowconfigure(0, minsize=10)  # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)  # empty row with minsize as spacing
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
                                                        "\u2022 Double-click on the pattern\n preview panel to view"
                                                        " similar\n garments.",
                                                   justify='left')
        self.instructions.grid(row=6, column=0, pady=(15, 0))

        self.label_mode = customtkinter.CTkLabel(master=self.frame_left, text="Appearance Mode:")
        self.label_mode.grid(row=9, column=0, pady=(370, 0), padx=20)

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
        # self.query_img_info.custom_bind('<Double-Button-1>', lambda: print('Double Click'))
        self.frame_info = customtkinter.CTkFrame(master=self.frame_right)
        self.frame_info.grid(row=1, column=0, columnspan=4, pady=10, padx=10)
        self.img_query = ImageTk.PhotoImage(Image.open("test_images/bg_image.png").resize((300, 300)))
        self.query_img = customtkinter.CTkLabel(self.frame_info, image=self.img_query)
        self.query_img.grid(row=1, column=0, pady=(10, 40), padx=10)

        self.retrieved_label = customtkinter.CTkLabel(master=self.frame_right_right, text="Retrieved garments",
                                                      text_font=('Roboto', 16)).grid(ipadx=528, pady=15, column=1,
                                                                                     sticky='e')

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

        self.finalize_button = customtkinter.CTkButton(master=self.frame_lower_right, text="Finalize",
                                                       command=self.on_finalize)
        self.finalize_button.grid(row=7, column=0, pady=(20, 0), columnspan=4)

        # Frame lower right right
        self.pattern_preview_title = customtkinter.CTkLabel(master=self.frame_lower_right_right, text="Patterns",
                                                            text_font=('Roboto', 16)).grid(column=0, sticky='n',
                                                                                           pady=10)
        self.pattern_preview = InteractivePatternPreview(master=self.frame_lower_right_right,
                                                         callbacks=None,
                                                         editor=None,
                                                         sticky='n',
                                                         padx=(15),
                                                         column=0,
                                                         row=1)
        self.pattern_preview.set_callback('button_press_event', self.onDoubleClickCanvas)

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
        self.object_type = None

    def modify_object_type(self, object_type):
        self.object_type = object_type

    def modify_scanned_file(self, filename):
        self._scanned_file = filename

    def change_appearance_mode(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def on_closing(self, event=0):
        self.destroy()

    def load_image(self, path, image_size):
        return ImageTk.PhotoImage(Image.open(path).resize((image_size, image_size)))

    def onClickDetails(self, idx):
        if not isinstance(self._retrieved[idx - 1], str):
            self.pattern_path.configure(text=Path(self._retrieved[idx - 1][0]).parent)
            self.pattern_name.configure(text=osp.basename(self._retrieved[idx - 1][0]).split('.')[0])
            _selected = self._retrieved[idx - 1][0]
        else:
            self.pattern_path.configure(text=Path(self._retrieved[idx - 1]).parent)
            self.pattern_name.configure(text=osp.basename(self._retrieved[idx - 1]).split('.')[0])
            _selected = self._retrieved[idx - 1]
        _categories = [self.garment_paths['category'][i] for i in self.ind]
        _names = [self.garment_paths['name'][i] for i in self.ind]
        self.editor = EditorApp(master=self.frame_lower_right_right, width=300,
                                category=self.pattern_category.text)
        self.editor.set_path_to_garment(_selected)
        self.editor.set_ind_pat(Path(_selected).parent)
        self.editor.set_seam(Path(_selected).parent)
        self.editor.set_subpath(Path(_selected).parent)

        self.pattern_category.configure(text=_categories[idx - 1])
        self.pattern_name.configure(text=_names[idx - 1])

        self.pattern_preview.set_editor(self.editor)
        self.pattern_preview.get_data_from_path(_selected)
        self.pattern_number.configure(text=str(len(self.pattern_preview.coords_list)))
        self.pattern_preview.draw()

    def clear_info(self):
        self.pattern_name.configure(text="")
        self.pattern_category.configure(text="")
        self.pattern_path.configure(text="")
        self.pattern_number.configure(text="")
        self.selected_image_preview_obj = ImageTk.PhotoImage(Image.open('test_images/bg_image.png').resize((180, 180)))
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

    def onClickGarmentButton(self, index, img_path, event):
        self._index = index
        self.onClickDetails(index)
        img_obj = Image.open(img_path).resize((180, 180))
        photo_img = ImageTk.PhotoImage(img_obj)
        self.selected_image_preview_obj = photo_img
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

    def onClickRelevantGarmentButton(self, index):
        self._index = index
        found = [a for a in self.filenames if os.path.basename(self._suggested[index]) in a]
        img_path = osp.join(str(Path(found[0]).parent), self._suggested[index]) + '.jpg'
        img_obj = Image.open(img_path).resize((180, 180))
        photo_img = ImageTk.PhotoImage(img_obj)
        self.selected_image_preview_obj = photo_img
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

        p = Path(found[0])
        self.update_details(p)

        self.pattern_preview.get_data_from_path(p)
        self.pattern_number.configure(text=str(len(self.pattern_preview.coords_list)))
        self.pattern_preview.draw()

    def clear_images(self):
        for i in range(4):
            getattr(self, f'view{i + 1}').parent = None
            setattr(self, f'view{i + 1}', getattr(self, f'canvas{i + 1}').central_widget.add_view(bgcolor='#4a4949'))
        self.pattern_preview.clear()

    def update_images(self):
        for idx, retrieved_path in enumerate(self._retrieved):
            retrieved_img = ImageTk.PhotoImage(Image.open(retrieved_path).resize((250, 250)))
            getattr(self, f'out_img_{str(idx + 1)}').configure(image=retrieved_img)

    def retrieve(self):
        self._retrieved, self.ind = infer(self._scanned_file, k=4, object_type=self.controller.model.object_type,
                                          gallery_paths=self.garment_paths['image_path'])
        self.clear_images()

        if self.object_type == 'image':
            im1 = imread(self._retrieved[0][0])
            im2 = imread(self._retrieved[1][0])
            im3 = imread(self._retrieved[2][0])
            im4 = imread(self._retrieved[3][0])

            image1 = vispy.scene.visuals.Image(im1, parent=self.view1)
            image2 = vispy.scene.visuals.Image(im2, parent=self.view2)
            image3 = vispy.scene.visuals.Image(im3, parent=self.view3)
            image4 = vispy.scene.visuals.Image(im4, parent=self.view4)

            self.view1.add(image1)
            self.view2.add(image2)
            self.view3.add(image3)
            self.view4.add(image4)

            self.retrieved_viewport1.bind('<FocusIn>', partial(self.onClickGarmentButton, 1, self._retrieved[0][0]))
            self.retrieved_viewport2.bind('<FocusIn>', partial(self.onClickGarmentButton, 2, self._retrieved[1][0]))
            self.retrieved_viewport3.bind('<FocusIn>', partial(self.onClickGarmentButton, 3, self._retrieved[2][0]))
            self.retrieved_viewport4.bind('<FocusIn>', partial(self.onClickGarmentButton, 4, self._retrieved[3][0]))

            for i in range(4):
                getattr(self, f'view{i + 1}').camera = vispy.scene.PanZoomCamera(aspect=1)
                getattr(self, f'view{i + 1}').camera.flip = (0, 1, 0)
                getattr(self, f'view{i + 1}').camera.set_range()
                getattr(self, f'view{i + 1}').camera.zoom(1.0, (250, 200))
        else:
            for idx, obj_file in enumerate(self._retrieved):
                vertices, faces, _, _ = vispy.io.read_mesh(obj_file)
                m = Mesh(vertices, faces)
                mesh = vispy.scene.visuals.Mesh(vertices=m.vertices,
                                                shading='smooth',
                                                faces=m.faces)
                getattr(self, f'view{idx + 1}').add(mesh)
                getattr(self, f'view{idx + 1}').camera = vispy.scene.TurntableCamera(elevation=90, azimuth=0, roll=90)

            self.retrieved_viewport1.bind('<FocusIn>', partial(self.onClickGarmentButton, 1,
                                                               self._retrieved[0].replace('.obj', '.jpg')))
            self.retrieved_viewport2.bind('<FocusIn>', partial(self.onClickGarmentButton, 2,
                                                               self._retrieved[1].replace('.obj', '.jpg')))
            self.retrieved_viewport3.bind('<FocusIn>', partial(self.onClickGarmentButton, 3,
                                                               self._retrieved[2].replace('.obj', '.jpg')))
            self.retrieved_viewport4.bind('<FocusIn>', partial(self.onClickGarmentButton, 4,
                                                               self._retrieved[3].replace('.obj', '.jpg')))

    def onDoubleClickCanvas(self, event):
        if event.dblclick:
            child = customtkinter.CTkToplevel()
            child.title('Relevant Patterns')
            child.geometry('1220x380+670+65')
            child.wm_transient(master=self)

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
                                                                           command=partial(
                                                                               self.onClickRelevantGarmentButton, i)))
                getattr(child, f'out_img_{i + 1}').grid(row=5, column=0, pady=10, padx=10)

            path_to_ss = osp.join(DATABASE_PATH, self.pattern_category.text, f'ss_{self.pattern_category.text}.txt')
            try:
                selected_idx = ss_dict_name_to_idx[self.pattern_category.text][
                    osp.basename(self._retrieved[self._index - 1][0]).split('.')[0]]
            except KeyError:
                selected_idx = ss_dict_name_to_idx[self.pattern_category.text][
                    osp.basename(self._retrieved[self._index - 1]).split('.')[0]]
            ss_mat = create_ss_matrix(path_to_ss)

            list_similarities = []
            for i in range(len(ss_mat)):
                list_similarities.append(similarity(selected_idx, i, ss_mat))
            arr = np.asarray(list_similarities)
            suggested = arr.argsort()[-4:]
            self._suggested = [ss_dict_idx_to_name[self.pattern_category.text][idx] for idx in suggested]
            database = '/home/kaseris/Documents/database'
            self._suggested[0] = self.pattern_name.text
            self.filenames = []
            for root, dirs, files in os.walk(database):
                for name in files:
                    self.filenames.append(os.path.join(root, name))
            paths = []
            for idx, _ in enumerate(self._suggested):
                found = [a for a in self.filenames if os.path.basename(self._suggested[idx]) in a]
                photo_img = ImageTk.PhotoImage(
                    Image.open(str(Path(found[0]).parent) + f'/{self._suggested[idx]}.jpg').resize((250, 250)))
                if idx == 0:
                    getattr(child, f'out_img_{idx + 1}').configure(image=self.selected_image_preview_obj)
                else:
                    getattr(child, f'out_img_{idx + 1}').configure(image=photo_img)

            child.mainloop()

    def update_details(self, path):
        self.pattern_name.configure(text=str(path.parent.name))
        for cat in ['blouse', 'dress', 'skirt']:
            if cat in str(path):
                self.pattern_category.configure(text=cat)
        self.pattern_path.configure(text=str(path.parent))

    def on_finalize(self):
        import subprocess
        import shutil
        import errno

        if self.pattern_path.text != '':
            old_dir = os.getcwd()

            split_path = str(Path(self.editor.path_to_garment).parent).split(osp.sep)
            subcategory, model = split_path[-2], split_path[-1]

            if osp.exists(osp.join(DATABASE_PATH, '.temp')):
                shutil.rmtree(osp.join(DATABASE_PATH, '.temp'))
                # os.mkdir(osp.join(DATABASE_PATH, '.temp'))
                # os.mkdir(osp.join(DATABASE_PATH, '.temp', subcategory))

                # os.mkdir(osp.join(DATABASE_PATH, '.temp'))
                # os.mkdir(osp.join(DATABASE_PATH, '.temp', subcategory, model))

            shutil.copytree(Path(self.editor.path_to_garment).parent,
                            osp.join(DATABASE_PATH, '.temp', subcategory, model))
            self.editor.export(osp.join(DATABASE_PATH, '.temp', subcategory, model))

            os.chdir('/home/kaseris/Documents/iMannequin_3D_Tool_v11_venia/')
            subprocess.run([f'{osp.join(os.getcwd(), "main.out")}',
                            osp.join(DATABASE_PATH, '.temp', subcategory, model)])
            os.chdir(old_dir)
        else:
            pass

    def start(self):
        self.controller.render()
        self.mainloop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = App()
    app.start()
