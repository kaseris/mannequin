import tkinter
import customtkinter


class EditorApp(customtkinter.CTkFrame):
    FONT_SIZE = 11
    GEOMETRY = (250, 200)

    choices = ['front', 'back', 'skirt front', 'skirt back']
    regions = ['armhole', 'collar', 'all', 'sides']

    def __init__(self, master: customtkinter.CTkFrame,
                 width,
                 category):
        super(EditorApp, self).__init__(master=master, width=width, corner_radius=25,
                                        fg_color='#2a2d2e')

        self.title = customtkinter.CTkLabel(self, text="Please select the pattern\n you want to change:",
                                            text_font=('Roboto', EditorApp.FONT_SIZE, 'bold'))

        self.radio_var = tkinter.IntVar()
        self.pattern_choice_var = tkinter.IntVar()
        self.category = category

        self.choice_rb1 = None
        self.choice_rb2 = None
        self.choice_label = None
        self.choice_button = None

        # Define the layout
        if category == 'blouse':
            self.rb1 = customtkinter.CTkRadioButton(master=self, text="Front", command=None, width=15, height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=0,
                                                    variable=self.radio_var)
            self.rb1.configure(command=self.on_click_ok)
            self.rb2 = customtkinter.CTkRadioButton(master=self, text="Back", command=None, width=15, height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=1,
                                                    variable=self.radio_var)
            self.rb2.configure(command=self.on_click_ok)
        elif category == 'dress':
            self.rb1 = customtkinter.CTkRadioButton(master=self, text="Front", command=None, width=15, height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=0,
                                                    variable=self.radio_var)
            self.rb1.configure(command=self.on_click_ok)
            self.rb2 = customtkinter.CTkRadioButton(master=self, text="Back", command=None, width=15, height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=1,
                                                    variable=self.radio_var)
            self.rb2.configure(command=self.on_click_ok)
            self.rb3 = customtkinter.CTkRadioButton(master=self, text="Skirt Front", command=None, width=15,
                                                    height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=2,
                                                    variable=self.radio_var)
            self.rb3.configure(command=self.on_click_ok)
            self.rb4 = customtkinter.CTkRadioButton(master=self, text="Skirt Back", command=None, width=15,
                                                    height=15,
                                                    text_font=('Roboto', EditorApp.FONT_SIZE), value=3,
                                                    variable=self.radio_var)
            self.rb4.configure(command=self.on_click_ok)
        elif category == 'skirt':
            self.title.configure(text='Information')
            self.message = customtkinter.CTkLabel(self,
                                                  text_font=('Roboto', EditorApp.FONT_SIZE),
                                                  text='The \"side\" regions of the front and the\n back pattern'
                                                       ' will be'
                                                       ' replaced!')
        self.grid(row=1, sticky='nswe', padx=(60, 0), column=1)

        if category == 'blouse':
            self.title.grid(row=0, pady=10)
            self.rb1.grid(row=1)
            self.rb2.grid(row=2)
        elif category == 'dress':
            self.title.grid(row=0, pady=10)
            self.rb1.grid(row=1)
            self.rb2.grid(row=2)
            self.rb3.grid(row=3)
            self.rb4.grid(row=4)
        elif category == 'skirt':
            self.title.grid(row=0, pady=10)
            self.message.grid(row=1)

    def on_click_ok(self):
        choice = EditorApp.choices[self.radio_var.get()]

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

        if (choice == 'front') or (choice == 'back'):
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

            self.choice_label.grid(row=8, pady=(35,10))
            self.choice_rb1.grid(row=9)
            self.choice_rb2.grid(row=10)
            self.choice_rb1.select()

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

            self.choice_label.grid(pady=(45,10), row=8)
            self.choice_rb1.grid(row=9)
            self.choice_rb2.grid(row=10)
            self.choice_rb1.select()

        self.choice_button = customtkinter.CTkButton(master=self, text='OK', text_font=('Roboto', 11),
                                                     command=None)
        self.choice_button.grid(row=12, pady=(150, 0))
    #
    #     new_window.mainloop()


if __name__ == '__main__':
    pass
