import customtkinter
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

from fusion import read_bezier_points_from_txt


class InteractiveMplFrame(customtkinter.CTkFrame):

    COLORS = {'unselected': (57/255, 139/255, 227/255),
              'hover': (230/255, 67/255, 67/255),
              'selected': (255/255, 190/255, 59/255)}
    
    def __init__(self,
                 master,
                 width,
                 height,
                 bg_color,
                 data: np.ndarray):
        super(InteractiveMplFrame, self).__init__(master=master, width=width, height=height, bg_color=bg_color)
        self.data = data
        self.curves = self.prepare_data()

        self.f = Figure(figsize=(1, 1))
        self.preview = FigureCanvasTkAgg(self.f, master=self)
        self.preview.get_tk_widget().grid()

        self.render()

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


if __name__ == '__main__':
    root = customtkinter.CTk()
    root.geometry('800x700')

    impl = InteractiveMplFrame(master=root, width=500, height=500,
                               bg_color='#ff0000',
                               data=read_bezier_points_from_txt('/home/kaseris/Documents/database/dress/d1/DD032/data/txt/front/bezier_front_3.txt'))
    impl.grid(row=0, column=0)
    root.mainloop()

