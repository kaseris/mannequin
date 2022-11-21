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

        self.build()

    def build(self):
        self.root = customtkinter.CTk()
        self.root.title(self.title)
        self.root.geometry(self.geometry)
        self.root.minsize(width=1500, height=700)

        self.sidebar = Sidebar(master=self.root, width=200, corner_radius=9)
        self.frame_espa = FrameESPA(master=self.root, corner_radius=9, height=80, fg_color='#ffffff')
        self.frame_watermark = FrameWatermark(master=self.root, corner_radius=9)
        self.sidebar.build()
        self.frame_watermark.build()
        self.frame_espa.build()

    def run(self):
        self.root.mainloop()


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
    def __init__(self, master, corner_radius):
        super(FrameWatermark, self).__init__(master=master, corner_radius=corner_radius)
        self.img = ImageTk.PhotoImage(Image.open('test_images/imannequin.png').convert('RGBA'))
        self.label = customtkinter.CTkLabel(master=self, image=self.img)
        # self.canvas = tkinter.Canvas(master=self)

    def build(self):
        self.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True, pady=(0, 5))
        self.pack_propagate(False)
        self.label.place(x=5, y=5, relwidth=1, relheight=1)


class FrameQueryImagePlaceholder(customtkinter.CTkFrame):
    def __init__(self, master, width, height):
        super(FrameQueryImagePlaceholder, self).__init__(master=master, width=1000, height=900)

    def build(self):
        self.grid(row=0, column=0)


if __name__ == '__main__':
    layout = Layout(title='i-Mannequin')
    layout.run()
