import customtkinter
from tkinter import ttk
import tkinter as tk
import functools

fp = functools.partial


class VerticalScrolledFrame(customtkinter.CTkFrame):
    def __init__(self, parent, *args, **kw):

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        def _on_mousewheel(event, scroll):
            canvas.yview_scroll(int(scroll), "units")

        def _bind_to_mousewheel(event):
            canvas.bind_all("<Button-4>", fp(_on_mousewheel, scroll=-1))
            canvas.bind_all("<Button-5>", fp(_on_mousewheel, scroll=1))

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        customtkinter.CTkFrame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = customtkinter.CTkScrollbar(self, orientation=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=vscrollbar.set, bg='#212224')
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.configure(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas, bg='#212224')

        interior_id = canvas.create_window((0, 0), window=interior,
                                           anchor=tk.NW)

        interior.bind('<Configure>', _configure_interior)
        canvas.bind('<Configure>', _configure_canvas)
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)


if __name__ == "__main__":
    pass
