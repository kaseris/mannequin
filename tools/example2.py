import os
import os.path as osp
from functools import partial

import tkinter
import tkinter.messagebox
import customtkinter
from tkinter import filedialog

from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from mannequin.retrieval2d.retrieval_dimis import *
from mannequin.fileio.fileio import read_coords_from_txt
from PIL import Image, ImageTk

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

PATH = '/home/kaseris/Documents/dev/mannequin/tools'


def similarity(query, retrieved, ss_mat):
    if ss_mat[retrieved, query] <= 0.0:
        return ss_mat[query, retrieved]
    return ss_mat[retrieved, query]


def create_ss_matrix():
    with open('/home/kaseris/Documents/ss_dress.txt', 'r') as f:
        for idx, line in enumerate(f):
            l = line.strip().split(',\t')
            if idx == 0:
                ss = np.zeros((len(l) + 1, len(l) + 1))
            ss[idx, idx + 1:] = [float(el) for el in l]

    return ss


ss_dict_name_to_idx = {'DD0332': 0,
                       'GNSS': 1,
                       'Q5751Á': 2,
                       'Q6089': 3,
                       'Q6109': 4,
                       'Q6117': 5,
                       'Q6362': 6,
                       'Q6435': 7,
                       'Q6446': 8,
                       'Q6856': 9}

ss_dict_idx_to_name = {0: 'DD0332',
                       1: 'GNSS',
                       2: 'Q5751',
                       3: 'Q6089',
                       4: 'Q6109',
                       5: 'Q6117',
                       6: 'Q6362',
                       7: 'Q6435',
                       8: 'Q6446',
                       9: 'Q6856'}


class App(customtkinter.CTk):

    WIDTH = 1900
    HEIGHT = 1060

    def __init__(self):
        super().__init__()
        self.extractor = load_test_model()
        self.deep_feats, self.color_feats, self.labels = load_feat_db()
        self.clf = load_kmeans_model()

        self.title("i-Mannequin")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        self._retrieved         = None
        self._selected_image    = None
        self._index             = None

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
        #self.frame_left.grid_rowconfigure(5, weight=1)  # empty row as spacing
        self.frame_left.grid_rowconfigure(8, minsize=20)    # empty row with minsize as spacing
        self.frame_left.grid_rowconfigure(11, minsize=10)  # empty row with minsize as spacing
        self.img = ImageTk.PhotoImage(Image.open("test_images/6a.png").resize((100, 100)))
        self.label_1 = customtkinter.CTkLabel(self.frame_left, image=self.img)
        self.label_1.grid(row=1, column=0, pady=(10, 0), padx=10)

        self.instructions_title = customtkinter.CTkLabel(self.frame_left, text="Instructions",
                                                         text_font=("Roboto", "14"))
        self.instructions_title.grid(row=5, column=0, pady=(140, 0))
        self.instructions = customtkinter.CTkLabel(self.frame_left,
                                                   text="\u2022Left Click on"
                                                        " a retrieved image\n to view garmen"
                                                        "t's infomation\n and its respective patterns.\n\n"
                                                        "\u2022 Click 'Enlarge' to enlarge\n the selected garment.\n\n"
                                                        "\u2022 Double-click on the pattern\n preview panel to view"
                                                        " similar\n garments.",
                                                   justify='left')
        self.instructions.grid(row=6, column=0, pady=(15, 0))

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Upload an Image",
                                                command=self.upload_image)
        self.button_1.grid(row=2, column=0, pady=(50, 10), padx=20)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Upload a scanned Garment",
                                                command=self.upload_3d)
        self.button_2.grid(row=3, column=0, pady=0, padx=20)

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
        self.retrieved_label = customtkinter.CTkLabel(master=self.frame_right_right, text="Retrieved garments", text_font=('Roboto', 16)).grid(columnspan=4, pady=10)

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

        # self.details_button = customtkinter.CTkButton(master=self.frame_right_right, text="Details")
        # self.details_button.grid(row=6, column=0, columnspan=4, pady=(10, 0))
        self.enlarge_button = customtkinter.CTkButton(master=self.frame_right_right, text="Enlarge")
        self.enlarge_button.grid(row=6, column=0, pady=(10, 0), columnspan=4)
        # self.select_button = customtkinter.CTkButton(master=self.frame_right_right, text="Select")
        # self.select_button.grid(row=6, column=2, pady=(10, 0), padx=(7, 0), sticky='w')

        self.optionmenu_1.set("Dark")

        # Frame lower right

        self.box_name = customtkinter.CTkLabel(master=self.frame_lower_right, text="Information",
                                               text_font=('Roboto', 16))
        self.box_name.grid(columnspan=2, pady=10)
        # self.box_name.place(x=160, y=150, anchor="center")

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

        # Frame lower right right
        self.pattern_preview_title = customtkinter.CTkLabel(master=self.frame_lower_right_right, text="Patterns",
                                                            text_font=('Roboto', 16)).grid(column=1, sticky='n',
                                                                                           pady=10)

        self.f = Figure(figsize=(5, 5))
        self.f.canvas.mpl_connect('button_press_event', self.onDoubleClickCanvas)
        self.f.patch.set_facecolor('#343638')
        self.pattern_preview = FigureCanvasTkAgg(self.f, master=self.frame_lower_right_right)
        self.pattern_preview.get_tk_widget().grid(sticky='n', padx=(370), column=1)

    def upload_image(self):
        query_img = filedialog.askopenfilename(filetypes=[("JPEG Images", "*.jpg"), ("PNG Images", "*.png")],
                                               initialdir='/home/kaseris/Documents/fir')
        try:
            img = Image.open(query_img)
        except AttributeError:
            print("den epelekses tipota")
            return
        self.img_query = ImageTk.PhotoImage(Image.open(query_img).resize((300, 300)))
        self.query_img.configure(image=self.img_query)

        if not not self._retrieved:
            for i in range(4):
                getattr(self, f'out_img_{str(i+1)}').configure(image=None)

        # ====
        # TODO: Threading
        f = dump_single_feature(query_img, self.extractor)

        # number 4 in the args possibly refers to the number of imgs to retrieve
        result = naive_query(f, self.deep_feats, self.color_feats, self.labels, 4)
        result_kmeans = kmeans_query(self.clf, f, self.deep_feats, self.color_feats, self.labels, 4)
        self._retrieved = result_kmeans
        # ====
        for idx, item in enumerate(result_kmeans):
            retrieved_path, _ = item
            retrieved_img = ImageTk.PhotoImage(Image.open(retrieved_path).resize((250, 250)))
            getattr(self, f'out_img_{str(idx+1)}').configure(image=retrieved_img)
            # getattr(self, f'out_img_{str(idx + 1)}').configure(command=partial(enlarge_image, retrieved_path))

    def upload_3d(self):
        pass

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
        self.pattern_path.configure(text=self._retrieved[idx - 1][0])
        self.pattern_name.configure(text=osp.basename(self._retrieved[idx - 1][0]).split('.')[0])
        _selected = self._retrieved[idx - 1][0]
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
        self.enlarge_button.configure(command=partial(self.onClickEnlarge, self._retrieved[index - 1][0]))
        self.onClickDetails(index)
        # self.details_button.configure(command=partial(self.onClickDetails, index - 1))
        img_path = self._retrieved[index-1][0]
        img_obj = Image.open(img_path).resize((180, 180))
        photo_img = ImageTk.PhotoImage(img_obj)
        self.selected_image_preview_obj = photo_img
        self.selected_image_preview.configure(image=self.selected_image_preview_obj)

    def onDoubleClickCanvas(self, event):
        if event.dblclick:
            child = customtkinter.CTkToplevel()
            child.title('Relevant Patterns')
            child.geometry('1220x380+670+65')

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
                                                                           command=None))
                getattr(child, f'out_img_{i + 1}').grid(row=5, column=0, pady=10, padx=10)

            selected_idx = ss_dict_name_to_idx[osp.basename(self._retrieved[self._index-1][0]).split('.')[0]]
            ss_mat = create_ss_matrix()

            list_similarities = []
            for i in range(10):
                list_similarities.append(similarity(selected_idx, i, ss_mat))
            arr = np.asarray(list_similarities)
            suggested = arr.argsort()[-4:]
            s = [ss_dict_idx_to_name[idx] for idx in suggested]
            #========================
            database = '/home/kaseris/Documents/GANAS_GUI/database'
            filenames = []
            for root, dirs, files in os.walk(database):
                for name in files:
                    filenames.append(os.path.join(root, name))
            print(s)
            paths = []
            for idx, _ in enumerate(s):
                found = [a for a in filenames if os.path.basename(s[idx]) in a]
                # paths.append(str(Path(found[0]).parent))
                # setattr(child,
                #         f'img_out_{idx + 1}',
                #         ImageTk.PhotoImage(Image.open(str(Path(found[0]).parent)
                #                                       + f'/{s[idx]}.jpg').resize((250, 250))))
                photo_img = ImageTk.PhotoImage(Image.open(str(Path(found[0]).parent) + f'/{s[idx]}.jpg').resize((250, 250)))
                getattr(child, f'out_img_{idx + 1}').configure(image=photo_img)

            # ========================
            child.mainloop()


if __name__ == "__main__":
    app = App()
    app.mainloop()
