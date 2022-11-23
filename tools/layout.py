from typing import Union

import tkinter

import customtkinter

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

from PIL import Image, ImageTk, ImageOps


class Layout:
    def __init__(self,
                 title='i-Mannequin',
                 geometry='1920x1080'):
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
            offsets = [(680, 115), (980, 115), (1280, 115), (1580, 115)]
            for i in range(4):
                setattr(self, f'win_{i}', customtkinter.CTkToplevel(master=self.root))
                getattr(self, f'win_{i}').geometry(f'260x260+{offsets[i][0]}+{offsets[i][1]}')
                getattr(self, f'win_{i}').wm_transient(master=self.root)
                getattr(self, f'win_{i}').title(f'Retrieved Garment {i + 1}')
            self.query_image_placeholder = QueryImagePlaceholder(master=self.root)
            self.root.bind('<Configure>', self.query_image_placeholder.dragging)
            self.frame_information = FrameGarmentInformation(master=self.frame_watermark, corner_radius=9,
                                                             width=327, height=553)
            self.frame_information.build()

            self.frame_pattern_preview = FramePatternPreview(master=self.frame_watermark, corner_radius=9,
                                                             width=1290, height=553)
            self.frame_pattern_preview.build()
            self.shown = True
        else:
            print('shown')


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
                                                     command=None)
        self.instructions_title = customtkinter.CTkLabel(self, text="Instructions",
                                                         text_font=("Roboto", "14"))
        self.instructions = customtkinter.CTkLabel(self,
                                                   text="\u2022 Left Click on"
                                                        " a retrieved image\n to view garmen"
                                                        "t's infomation\n and its respective patterns.\n\n"
                                                        "\u2022 Double-click on the pattern\n preview panel to view"
                                                        " similar\n garments.",
                                                   justify='left',
                                                   width=10)
        self.label_mode = customtkinter.CTkLabel(master=self, text="Appearance Mode:")
        self.optionmenu = customtkinter.CTkOptionMenu(master=self,
                                                      values=["Light", "Dark", "System"],
                                                      command=self.change_appearance_mode)
        customtkinter.set_appearance_mode("Dark")
        self.optionmenu.set("Dark")

    def build(self):
        self.pack(fill=tkinter.Y, side=tkinter.LEFT, expand=False, padx=(0, 5))
        self.pack_propagate(False)

        self.label_1.pack(pady=(30, 0))
        self.button_upload.pack(pady=(30, 0))
        self.instructions_title.pack(pady=(220, 0))
        self.instructions.pack(pady=(20, 0))
        self.label_mode.pack(pady=(300, 0))
        self.optionmenu.pack(pady=(15, 0))

    def change_appearance_mode(self, new_appearance):
        customtkinter.set_appearance_mode(new_appearance)


class FrameESPA(customtkinter.CTkFrame):
    def __init__(self, master, height, corner_radius, fg_color):
        super(FrameESPA, self).__init__(master=master, height=height, corner_radius=corner_radius,
                                        fg_color=fg_color)
        self.img = ImageTk.PhotoImage(Image.open('test_images/espa-eng-768x152.png').resize((768//2, 152//2)))
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
                                                                    placeholder_text=f'dummy_{str(i)}'))

        self.frame_image_preview = customtkinter.CTkFrame(master=self, width=200, height=200)
        img = Image.open('test_images/8.jpg')
        img_resized = ImageOps.contain(img, (190, 190))
        self.image_garment_preview = customtkinter.CTkButton(master=self.frame_image_preview,
                                                             image=ImageTk.PhotoImage(img_resized),
                                                             text='')

    def build(self):
        self.pack(side=tkinter.LEFT, anchor=tkinter.SW, pady=(7, 7), padx=(7, 0))
        self.pack_propagate(False)
        self.label.pack(anchor=tkinter.CENTER, pady=(5, 0))

        self.frame_text_placeholder.pack()
        self.frame_text_placeholder.grid_columnconfigure(0, weight=1)
        self.frame_text_placeholder.grid_columnconfigure(1, weight=3)
        self.text_name.grid(row=0, column=0, sticky=tkinter.W)
        self.text_category.grid(row=1, column=0, sticky=tkinter.W)
        self.text_n_patterns.grid(row=2, column=0, sticky=tkinter.W)
        self.text_pattern_path.grid(row=3, column=0, sticky=tkinter.W)
        for i in range(4):
            getattr(self, f'text_dummy_{i}').grid(row=i, column=1, sticky=tkinter.E)

        self.frame_image_preview.pack(pady=(10, 0))
        self.frame_image_preview.pack_propagate(0)
        self.image_garment_preview.pack(anchor=tkinter.CENTER)


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
        self.interactive_preview = InteractivePatternViewer(master=self, figsize=(9, 5))

    def build(self):
        self.place(x=345, y=370)
        self.pack_propagate(False)
        self.label_title.pack(pady=(7, 0))
        self.interactive_preview.widget.pack(side=tkinter.LEFT, padx=(20, 0))
        self.interactive_preview.draw()


class InteractivePatternViewer:
    MIN_X = 20.0
    MIN_Y = 20.0
    MAX_X = 20.0
    MAX_Y = 20.0

    def __init__(self,
                 master: Union[customtkinter.CTkFrame, customtkinter.CTkToplevel],
                 figsize=(9, 5),
                 **grid_params):
        self.f = Figure(figsize=figsize)
        self.f.patch.set_facecolor('#525252')

        self.pattern_preview = FigureCanvasTkAgg(self.f, master=master)

        # Maybe lines and line dict can be sampled from a Pattern model interface (?)
        # Will leave it blank for now and test it from a model class

        # TODO: Figure out; Is an editor required?

        # NOTE: An Editor class should contain the selected pattern's data and manage their contents from there.
        # The interactivePatternViewer is merely an user interface to render the results and listen to events.
        # A PatternController will listen to these events and subsequently issue a command to the model interface
        # to manipulate its data.

    @property
    def widget(self):
        return self.pattern_preview.get_tk_widget()

    def draw(self):
        self.f.canvas.draw_idle()


class UI:
    def __init__(self, test_shown=False):
        self.layout = Layout(title='i-Mannequin')
        self.layout.sidebar.button_upload.configure(command=self.button_press)

        if test_shown:
            self.__test()

    def run(self):
        self.layout.root.mainloop()

    def button_press(self):
        self.layout.show()

    def __test(self):
        self.layout.show()


if __name__ == '__main__':
    ui = UI(test_shown=False)
    ui.run()
