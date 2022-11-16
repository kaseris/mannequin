from pathlib import Path

import tkinter
import customtkinter

from altcurves import AltCurvesApp
from individual_pattern import IndividualPattern
from seam import Seam
from subpath import SubPath
from utils import ErrorPopup


class EditorApp(customtkinter.CTkFrame):
    FONT_SIZE = 11
    GEOMETRY = (250, 200)

    choices = ['front', 'back', 'skirt front', 'skirt back']
    regions = ['armhole', 'collar', 'all', 'sides']

    def __init__(self,
                 master: customtkinter.CTkFrame,
                 width,
                 category):
        super(EditorApp, self).__init__(master=master, width=width, corner_radius=25,
                                        fg_color='#2a2d2e')

        self.radio_var = tkinter.IntVar()
        self.pattern_choice_var = tkinter.IntVar()
        self.category = category
        self._path_to_garment = None
        self._ind_pattern = None
        self._seam, self._subpath = None, None

        self.choice_rb1 = None
        self.choice_rb2 = None
        self.choice_label = None
        self.choice_button = None
        self.replace_button = None

        self.not_available_info = None

        # Define the layout
        if category == 'blouse':
            self.title = customtkinter.CTkLabel(self, text="Click on the pattern\n you want to change:",
                                                text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'))
            self.choices = customtkinter.CTkLabel(self, text="\u2022 Front\n\u2022 Back",
                                                  text_font=('Roboto', EditorApp.FONT_SIZE))
        elif category == 'dress':
            self.title = customtkinter.CTkLabel(self, text="Click on the pattern\n you want to change:",
                                                text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'))
            self.choices = customtkinter.CTkLabel(self, text="\u2022 Front\n\u2022 Back\n\u2022"
                                                             " Skirt Front\n\u2022 Skirt"
                                                             " Back",
                                                  text_font=('Roboto', EditorApp.FONT_SIZE))
        elif category == 'skirt':
            self.title = customtkinter.CTkLabel(master=self, text='Information',
                                                text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'))
            self.message = customtkinter.CTkLabel(self,
                                                  text_font=('Roboto', EditorApp.FONT_SIZE),
                                                  text='The \"side\" regions of the front and the\n back pattern'
                                                       ' will be'
                                                       ' replaced!')
        self.grid(row=1, sticky='nswe', padx=(60, 0), column=1)

        if category == 'blouse':
            self.title.grid(row=0, pady=10)
            self.choices.grid(row=1)
        elif category == 'dress':
            self.title.grid(row=0, pady=10)
            self.choices.grid(row=1)
        elif category == 'skirt':
            self.title.grid(row=0, pady=10)
            self.message.grid(row=1)

    def on_click_ok(self, choice):

        self.choice = choice

        self.clear()

        if ((choice == 'front') or (choice == 'back')) and ((self.category == 'blouse') or (self.category == 'dress')):
            self.choice_label = customtkinter.CTkLabel(master=self,
                                                       text="Please choose the\npattern region you\nwant to "
                                                            "replace",
                                                       text_font=('Roboto', 11, 'bold'))
            self.choice_rb1 = customtkinter.CTkRadioButton(master=self, text='Armhole', text_font=('Roboto', 11),
                                                           variable=self.pattern_choice_var, value=0, width=15,
                                                           height=15)
            self.choice_rb2 = customtkinter.CTkRadioButton(master=self, text='Collar', text_font=('Roboto', 11),
                                                           variable=self.pattern_choice_var, value=1, width=15,
                                                           height=15)

            self.choice_label.grid(row=3, pady=(35, 10))
            self.choice_rb1.grid(row=4)
            self.choice_rb2.grid(row=5)
            self.choice_rb1.select()

            self.choice_button = customtkinter.CTkButton(master=self, text='OK', text_font=('Roboto', 11),
                                                         command=self.on_select)
            self.replace_button = customtkinter.CTkButton(master=self, text='Replace Curve', text_font=('Roboto', 11),
                                                          command=self.on_replace)
            self.choice_button.grid(row=12, pady=(100, 0))
            self.replace_button.grid(row=13, pady=(10, 0))

        elif (choice == 'skirt front') or (choice == 'skirt back'):
            self.not_available_info = customtkinter.CTkLabel(master=self, text="The sides region will\n"
                                                                               "automatically be changed!",
                                                             text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'),
                                                             text_color='#dbb240')
            self.not_available_info.grid(row=3, pady=50)

            self.choice_button = customtkinter.CTkButton(master=self, text='OK', text_font=('Roboto', 11),
                                                         command=self.on_select)
            self.replace_button = customtkinter.CTkButton(master=self, text='Replace Curve', text_font=('Roboto', 11),
                                                          command=self.on_replace)
            self.choice_button.grid(row=12, pady=(100, 0))
            self.replace_button.grid(row=13, pady=(10, 0))
        else:
            self.not_available_info = customtkinter.CTkLabel(master=self, text="You cannot change\nthis pattern!",
                                                             text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'),
                                                             text_color='#cf1d11')
            self.not_available_info.grid(row=3, pady=50)

    def clear(self):
        if (self.choice_label is not None) or (self.not_available_info is not None):
            try:
                if self.choice_label.winfo_exists():
                    self.choice_rb1.grid_forget()
                    self.choice_rb2.grid_forget()
                    self.choice_label.grid_forget()
                    self.choice_button.grid_forget()
                    self.replace_button.grid_forget()

                    if self.not_available_info is not None:
                        self.not_available_info.grid_forget()

                    self.choice_rb1 = None
                    self.choice_rb2 = None
                    self.choice_label = None
                    self.choice_button = None
                    self.replace_button = None
                    self.not_available_info = None
            except AttributeError:
                if self.not_available_info.winfo_exists():
                    self.not_available_info.grid_forget()
                    self.not_available_info = None

    def clear_all(self):
        self.title.grid_forget()
        self.choices.grid_forget()
        try:
            self.message.grid_forget()
        except AttributeError:
            pass
        self.clear()

    def on_replace(self):
        __path = Path(self.path_to_garment).parent
        line = self.master.master.pattern_preview.get_region()
        if self.master.master.pattern_preview.alternative_exists and line is not None:
            # Region must be a [num_regions x num_points x 2] array in order to work properly.
            # In this case, the region is [100x2] i.e. two regions packed together.
            # This is not correct, because it replaces the whole collar region automatically.
            region = line.data_array
            for _region in region:
                self._ind_pattern.replace(_region, self.choice)
                # if self._ind_pattern.get_flag(EditorApp.regions[self.pattern_choice_var.get()]):
                #     print('I Will use seams')
                # else:
                #     print('I will use subpath')
                # self._subpath.replace(_region)
                # self._subpath.export_to_file('___subpath.txt')
            self.master.master.pattern_preview.get_data_from_individual_pattern(self._ind_pattern)
            self.master.master.pattern_preview.draw()
        else:
            error = ErrorPopup(master=self.master.master,
                               message='You have not chosen a curve to replace the selected pattern.',
                               geometry='450x80+890+700')
            error.run()

    def on_select(self):
        app = AltCurvesApp(master=self,
                           category=self.category,
                           choice=EditorApp.regions[self.pattern_choice_var.get()],
                           pattern_selection=self.choice)
        app.render()

    def set_path_to_garment(self, path):
        self._path_to_garment = path

    @property
    def path_to_garment(self):
        return self._path_to_garment

    def set_ind_pat(self, path):
        self._ind_pattern = IndividualPattern(path)

    def set_seam(self, path):
        self._seam = Seam(path)

    def set_subpath(self, path):
        self._subpath = SubPath(path)


if __name__ == '__main__':
    pass
