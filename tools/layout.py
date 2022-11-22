import tkinter

import customtkinter
from PIL import Image, ImageTk


class Layout:
    def __init__(self,
                 title='i-Mannequin',
                 geometry='1920x1080',
                 ):
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
        self.optionmenu.set('Dark')

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

    def build(self):
        self.pack(side=tkinter.LEFT, anchor=tkinter.SW, pady=(7, 7), padx=(7, 0))


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

    def build(self):
        self.place(x=345, y=370)


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
