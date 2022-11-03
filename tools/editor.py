import tkinter
import customtkinter

from altcurves import AltCurvesApp


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

        self.choice_rb1 = None
        self.choice_rb2 = None
        self.choice_label = None
        self.choice_button = None

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

        if self.choice_label is not None:
            if self.choice_label.winfo_exists():
                self.choice_rb1.destroy()
                self.choice_rb2.destroy()
                self.choice_label.destroy()
                self.choice_button.destroy()

                self.choice_rb1 = None
                self.choice_rb2 = None
                self.choice_label = None
                self.choice_button = None

        if ((choice == 'front') or (choice == 'back')) and ((self.category == 'blouse') or (self.category == 'dress')):
            self.choice_label = customtkinter.CTkLabel(master=self,
                                                       text="Please choose the pattern\n region you want to"
                                                            " replace",
                                                       text_font=('Roboto', 11, 'bold'))
            self.choice_rb1 = customtkinter.CTkRadioButton(master=self, text='Armhole', text_font=('Roboto', 11),
                                                           variable=self.pattern_choice_var, value=0, width=15,
                                                           height=15)
            self.choice_rb2 = customtkinter.CTkRadioButton(master=self, text='Collar', text_font=('Roboto', 11),
                                                           variable=self.pattern_choice_var, value=1, width=15,
                                                           height=15)

            self.choice_label.grid(row=3, pady=(35,10))
            self.choice_rb1.grid(row=4)
            self.choice_rb2.grid(row=5)
            self.choice_rb1.select()

            self.choice_button = customtkinter.CTkButton(master=self, text='OK', text_font=('Roboto', 11),
                                                         command=self.on_select)
            self.choice_button.grid(row=12, pady=(150, 0))

        elif (choice == 'skirt front') or (choice == 'skirt back'):
            self.choice_label = customtkinter.CTkLabel(master=self, text="Do you want to change:",
                                                       text_font=('Roboto', 11))
            self.choice_rb1 = customtkinter.CTkRadioButton(master=self, text='The whole pattern',
                                                           variable=self.pattern_choice_var, value=2, width=15,
                                                           height=15,
                                                           text_font=('Roboto', 11))
            self.choice_rb2 = customtkinter.CTkRadioButton(master=self, text='The \"sides\" region',
                                                           variable=self.pattern_choice_var, value=3, width=15,
                                                           height=15,
                                                           text_font=('Roboto', 11))

            self.choice_label.grid(pady=(45, 10), row=3)
            self.choice_rb1.grid(row=4)
            self.choice_rb2.grid(row=5)
            self.choice_rb1.select()

            self.choice_button = customtkinter.CTkButton(master=self, text='OK', text_font=('Roboto', 11),
                                                         command=self.on_select)
            self.choice_button.grid(row=12, pady=(150, 0))
        else:
            self.not_available_info = customtkinter.CTkLabel(master=self, text="You cannot change this pattern",
                                                             text_font=('Roboto', EditorApp.FONT_SIZE))
            self.not_available_info.grid(row=2, pady=50)

    def on_select(self):
        app = AltCurvesApp(master=self,
                           category=self.category,
                           choice=EditorApp.regions[self.pattern_choice_var.get()],
                           pattern_selection=self.choice)
        app.render()


if __name__ == '__main__':
    pass
