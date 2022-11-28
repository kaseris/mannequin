import os
import os.path as osp

from pathlib import Path

import tkinter.filedialog

import customtkinter

from app_models import IndividualPatternModel, QueryModel, Retrieval2DModel
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


class ControllerRetrievalApplyButton:
    def __init__(self, model_query: QueryModel):
        self.model_2d_retrieval = None
        self.model_3d_retrieval = None
        self.view = None

        self.model_query = model_query

    def couple(self, view, model2d, model3d):
        self.view = view
        self.model_2d_retrieval = model2d
        self.model_3d_retrieval = model3d

    def bind(self, callback_fn):
        self.view.configure(command=callback_fn)

    def on_apply(self):
        if not self.model_query.is_empty:
            if self.model_query.kind == 'image':
                self.model_2d_retrieval.infer(self.model_query.filename)
            else:
                pass
        else:
            print('No query')


class ControllerRetrievedViewportViews:
    def __init__(self):
        self.model: Retrieval2DModel = None

    def couple(self,
               model: Retrieval2DModel,
               viewlist):
        self.model = model
        for idx, view in enumerate(viewlist):
            setattr(self, f'view_{idx + 1}', view)
        self.model.set_controller(self)

    def bind(self):
        pass

    def draw(self):
        for idx, retrieved in enumerate(self.model.retrieved):
            # TODO: For now I placed 'image' but it should be inferred automatically.
            getattr(self, f'view_{idx + 1}').draw('image', retrieved[0])


class ControllerRetrievedPatternPreview:
    def __init__(self):
        self.model = None
        self.view = None
        self.pattern_preview = None
        self.pat_model = None
        self.information_view = None

    def couple(self, model,
               view,
               pattern_preview,
               pat_model,
               information_view):
        self.model = model
        self.view = view
        self.pattern_preview = pattern_preview
        self.pat_model = pat_model
        self.information_view = information_view

    def bind(self, event_type, callback_fn):
        self.view.bind(event_type, callback_fn)
        # Need to update some other views, i.e. the pattern info view and the editor view. For now, I only update the
        # pattern preview view.

    def say_hi(self, event):
        idx = self.view.idx
        garment_dir = self.model.paths[idx - 1]
        self.pat_model.update(garment_dir)
        self.pattern_preview.draw_pattern(self.pat_model.interactive_lines)
        self.information_view.text_dummy_0.configure(placeholder_text=str(Path(self.model.paths[idx - 1]).name),
                                                     state='normal')
        ind_patterns_path = osp.join(self.model.paths[idx - 1], 'individual patterns')
        # Workaround
        n_patterns = len(os.listdir(ind_patterns_path)) // 2
        self.information_view.text_dummy_1.configure(placeholder_text=str(n_patterns),
                                                     state='normal')
        categories = ['dress', 'blouse', 'skirt']
        for cat in categories:
            if cat in self.model.paths[idx - 1]:
                category = cat
        self.information_view.text_dummy_2.configure(placeholder_text=str(category.title()), state='normal')
        self.information_view.text_dummy_3.configure(placeholder_text=str(self.model.paths[idx - 1]), state='normal')
        self.information_view.update_thumbnail(self.model.paths[idx - 1])
