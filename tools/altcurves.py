import os
import os.path as osp

from pathlib import Path
import customtkinter

from fusion import get_keypoint_count, get_filename_for_bezier_points, read_bezier_points_from_txt, align_regions
from interactive_mpl import MplFrameGrid
from rules import rules_blouse


DATABASE = '/home/kaseris/Documents/database'


class AltCurvesApp(customtkinter.CTkToplevel):

    GEOMETRY = (1220, 500)
    OFFSET = (660, 510)

    def __init__(self,
                 master,
                 choice='collar',
                 category='dress',
                 pattern_selection='front'):
        super(AltCurvesApp, self).__init__(master=master)
        self.choice = choice
        self.category = category
        self.pattern_selection = pattern_selection
        self.alt_garments = self.find_garments_based_on_choice()
        self.curves = []
        self.get_corresponding_pattern_part()

        self.curve_to_replace = None

        # Define the layout
        self.geometry(f'{AltCurvesApp.GEOMETRY[0]}x{AltCurvesApp.GEOMETRY[1]}+'
                      f'{AltCurvesApp.OFFSET[0]}+{AltCurvesApp.OFFSET[1]}')
        self.title('Curve Editor')

        self.frame_grid = MplFrameGrid(master=self, data_list=self.curves,
                                       mpl_width=60, mpl_height=60, column_size=5)
        self.frame_grid.build_grid()

        self.wm_transient(master=master)

    def render(self):
        self.mainloop()

    def find_garments_based_on_choice(self):
        category_path = osp.join(DATABASE, self.category)
        list_subfolders_with_paths = [f.path for f in os.scandir(category_path) if f.is_dir()]
        l = []
        for subfolder in list_subfolders_with_paths:
            for s in os.listdir(subfolder):
                l.append(osp.join(subfolder, s))
        return l

    def get_corresponding_pattern_part(self):
        for g in self.alt_garments:
            try:
                which1 = rules_blouse[self.choice][get_keypoint_count(g, pattern=self.pattern_selection)]
                fnames1 = [get_filename_for_bezier_points(g, self.pattern_selection, n=n) for n in which1]
                # TODO: na diorthwthei gia na fainontai toso ta collar oso kai ta armholes se ena tile
                curve = []
                for fname in fnames1:
                    curve.append(read_bezier_points_from_txt(fname))
                    # self.curves.append(read_bezier_points_from_txt(fname))
                self.curves.append(curve)
            except FileNotFoundError:
                continue

    def set_curve_to_replace(self, data):
        self.curve_to_replace = data
        print(f'data updated with: {self.curve_to_replace}')

    def update_curves(self):
        path_to_garment1 = Path(self.master.path_to_garment).parent
        aligned_alt_curve = align_regions(path_to_garment1, self.curve_to_replace,
                                          pattern=self.pattern_selection,
                                          selection=self.choice)
        self.master.master.master.pattern_preview.add_curve(aligned_alt_curve)
        self.master.master.master.pattern_preview.draw()


if __name__ == '__main__':
    pass
