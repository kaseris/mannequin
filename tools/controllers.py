import tkinter.filedialog

import customtkinter

from app_models import IndividualPatternModel, QueryModel
from layout import FramePatternPreview, Sidebar
from interactive_mpl import InteractiveLine


class ControllerPatternModelPreview:
    def __init__(self):
        self.model : IndividualPatternModel = None
        self.view : FramePatternPreview = None

    def couple(self,
               model: IndividualPatternModel,
               view: FramePatternPreview):
        """Couples a model instance to a view. For example we can couple the individual pattern's model to the
        interactive preview view. Any events that happen in the interactive preview, are sent to the controller and in
        turn, the controller updates the model's data."""
        self.model = model
        self.view = view

    def bind_(self, event_type, callback_fn):
        """Associate an event type to a callback function."""
        self.view.bind_event(event_type, callback_fn)

    def on_pick(self, event):
        ind = event.artist.ID
        for interactive_line in self.model.interactive_lines:
            id = interactive_line.id
            if ind != id:
                interactive_line.set_state(0)
                interactive_line.line.set_color(InteractiveLine.normal_selected_color[0])
            else:
                interactive_line.set_state(1)
                interactive_line.line.set_color(InteractiveLine.normal_selected_color[1])
        self.view.interactive_preview.f.canvas.draw_idle()

    def on_hover(self, event):
        if event.inaxes == self.view.interactive_preview.ax:
            self.view.interactive_preview.annot.set_visible(False)
            for interactive_line in self.model.interactive_lines:
                cont, ind = interactive_line.line.contains(event)
                if interactive_line.state == 1:
                    continue

                if cont:
                    interactive_line.set_state(2)
                    interactive_line.line.set_color(InteractiveLine.normal_selected_color[2])

                    x, y = event.x, event.y
                    self.view.interactive_preview.annot.xy = (x, y)
                    self.view.interactive_preview.annot.xyann = (x + 20, y + 20)

                    self.view.interactive_preview.annot.set_text(interactive_line.label)
                    self.view.interactive_preview.annot.get_bbox_patch().set_facecolor('#5577ad')
                    self.view.interactive_preview.annot.get_bbox_patch().set_alpha(0.8)
                    self.view.interactive_preview.annot.set_visible(True)

                    self.view.interactive_preview.f.canvas.draw_idle()
                else:
                    interactive_line.set_state(0)
                    interactive_line.line.set_color(InteractiveLine.normal_selected_color[0])
                    self.view.interactive_preview.f.canvas.draw_idle()

    def on_key_press(self, event):
        pass


class ControllerQueryObjectModelUploadButton:
    def __init__(self):
        self.model : QueryModel = None
        self.view : customtkinter.CTkButton = None

    def couple(self,
               model: QueryModel,
               view: Sidebar):
        r"""
        Couples a model instance to a view. For example we can couple the individual pattern's model to the
        interactive preview view. Any events that happen in the interactive preview, are sent to the controller and in
        turn, the controller updates the model's data.
        """
        self.model = model
        self.view = view

    def bind_(self, event_type, callback_fn):
        """Associate an event type to a callback function."""
        self.view.configure(command=callback_fn)

    def open_file(self):
        filename = tkinter.filedialog.askopenfilename(title="Select file to open",
                                                      filetypes=(("JPEG Image", "*.jpg"),
                                                                 ("JPEG Image", "*.jpeg"),
                                                                 ("OBJ files", "*.obj"),
                                                                 ("STL Files", "*.stl"),
                                                                 ("all files", "*.*")))
        self.model.update(filename=filename)


class ControllerQueryObjectQueryViewer:
    def __init__(self):
        self.model: QueryModel = None
        self.view = None

    def couple(self,
               model: QueryModel,
               view: Sidebar):
        r"""
        Couples a model instance to a view. For example we can couple the individual pattern's model to the
        interactive preview view. Any events that happen in the interactive preview, are sent to the controller and in
        turn, the controller updates the model's data.
        """
        self.model = model
        self.view = view

    def update_view(self):
        self.view.draw(self.model.kind, self.model.filename)
