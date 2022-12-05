import os
import os.path as osp

from pathlib import Path

import tkinter.filedialog

import customtkinter

from app_models import IndividualPatternModel, QueryModel, Retrieval3DModel, Retrieval2DModel, RelevantGarmentsModel
from layout import FramePatternPreview, Sidebar, ShapeSimilarityWindow
from interactive_mpl import InteractiveLine

from altcurves import AltCurvesApp

from statemanager import AppState, AppStateEnum, AppStateInit, AppStateQueryUploaded

from utils import check_path_type


class ControllerPatternModelPreview:
    def __init__(self):
        self.model: IndividualPatternModel = None
        self.view: FramePatternPreview = None

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
                self.model.set_selected_region(interactive_line.label)
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

    def on_double_click_canvas(self, relevant, event):
        if event.dblclick:
            a = ShapeSimilarityWindow(relevant)
            a.build()


class ControllerQueryObjectModelUploadButton:
    def __init__(self,
                 app_state):

        self.model: QueryModel = None
        self.view: customtkinter.CTkButton = None

        self.__app_state = app_state

        self.opened_query = False

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
        if check_path_type(filename, ['.jpg', '.obj', '.stl', '.jpeg']):
            self.model.update(filename=filename)
            if self.model.kind == 'image':
                self.request_state_update(True, filename, AppStateEnum.APP_QUERY_UPLOADED)
            else:
                self.request_state_update(True, filename, AppStateEnum.APP_QUERY_UPLOADED)
        else:
            self.request_state_update(False, filename, AppStateEnum.APP_INIT)

    def request_state_update(self, update_flag, filename, next_state):
        # TODO: Pio sovaros elegxos sto filename
        if not self.opened_query:
            self.__app_state.notify_manager(update_flag, filename=filename,
                                            next_state=next_state)
            self.opened_query = True
        else:
            self.__app_state.update()

    def set_app_state(self, new_state):
        self.__app_state = None
        self.__app_state = new_state


class ControllerQueryObjectQueryViewer:
    def __init__(self,
                 app_state: AppState):
        self.model: QueryModel = None
        self.view = None

        self.__app_state = app_state

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
                self.model_3d_retrieval.infer(self.model_query.filename)
        else:
            print('No query')


class ControllerRetrievedViewportViews:
    def __init__(self, app_state: AppState):
        self.model: Retrieval2DModel = None
        self.__app_state = app_state

        self.needs_update_state = True

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

    def on_notify(self):
        if self.needs_update_state:
            self.__app_state.notify_manager()
            self.needs_update_state = False


class ControllerRetrieved3DViewportViews:
    def __init__(self):
        self.model: Retrieval3DModel = None

    def couple(self,
               model: Retrieval3DModel,
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
            getattr(self, f'view_{idx + 1}').draw('mesh', retrieved)

    def on_notify(self):
        pass


class ControllerRetrievedPatternPreview:
    def __init__(self):
        self.model = None
        self.view = None
        self.pattern_preview = None
        self.pat_model = None
        self.information_view = None
        self.relevant_ss_garment_model: RelevantGarmentsModel = None

    def couple(self, model,
               view,
               pattern_preview,
               pat_model,
               information_view,
               relevant_ss_garment_model: RelevantGarmentsModel):
        self.model = model
        self.view = view
        self.pattern_preview = pattern_preview
        self.pat_model = pat_model
        self.information_view = information_view
        self.relevant_ss_garment_model = relevant_ss_garment_model

    def bind(self, event_type, callback_fn):
        self.view.bind(event_type, callback_fn)
        # Need to update some other views, i.e. the pattern info view and the editor view. For now, I only update the
        # pattern preview view.

    def update_information(self, event):
        idx = self.view.idx
        garment_dir = self.model.paths[idx - 1]
        self.pat_model.update(garment_dir)
        self.pattern_preview.draw_pattern(self.pat_model.interactive_lines)
        self.information_view.text_dummy_0.configure(placeholder_text=str(self.pat_model.name),
                                                     state='normal')
        self.information_view.text_dummy_1.configure(placeholder_text=str(self.pat_model.category),
                                                     state='normal')
        self.information_view.text_dummy_2.configure(placeholder_text=self.pat_model.n_patterns, state='normal')
        self.information_view.text_dummy_3.configure(placeholder_text=str(self.model.paths[idx - 1]), state='normal')
        self.information_view.update_thumbnail(self.model.paths[idx - 1])
        self.relevant_ss_garment_model.update(self.model.paths[idx - 1])

    def request_state_update(self):
        pass


class ControllerIndividualPatternEditor:
    def __init__(self, master):
        self.model = None
        self.view = None
        self.master = master

    def couple(self, model, view):
        self.model = model
        self.view = view
        self.model.set_controller(self)

    def on_notify(self):
        self.view.update_state(f'GARMENT_{self.model.category.upper()}_SELECTED')
        self.view.update_option(self.model.selected_region)
        controller = ControllerAltCurvesAppEditor(master=self.master)
        controller.couple(self.model, self.view)
        controller.bind(controller.open_alt_curve_app)


class ControllerAltCurvesAppEditor:
    def __init__(self, master):
        self.model = None
        self.view = None

        self.master = master

    def couple(self, model, view):
        self.model = model
        self.view = view

    def bind(self, callback_fn):
        if self.view.options_widget is None:
            pass
        else:
            if hasattr(self.view.options_widget, 'button_search'):
                self.view.options_widget.button_search.configure(command=self.open_alt_curve_app)
            else:
                pass

    def open_alt_curve_app(self):
        choices = ['armhole', 'collar']
        _choice_var = self.view.options_widget.choice_var.get()
        app = AltCurvesApp(master=self.master,
                           choice=choices[_choice_var],
                           category=self.model.category,
                           pattern_selection=self.model.selected_region)
        app.render()


class ControllerRelevantPatternViews:
    def __init__(self):
        self.model: RelevantGarmentsModel = None
        self.view = None

    def couple(self,
               model: RelevantGarmentsModel,
               view):
        self.model = model
        self.view = view

    def bind(self, event_type, callback_fn):
        pass


class ControllerRelevantPatternPatternPreview:
    def __init__(self):
        self.model = None
        self.view = None

    def couple(self,
               model,
               view):
        self.model = model
        self.view = view

    def bind(self, event_type, callback_fn):
        pass


class ControllerRelevantPatternFrameInformation:
    def __init__(self):
        self.model = None
        self.view = None

    def couple(self, model, view):
        self.model = model
        self.view = view

    def bind(self, event_type, callback_fn):
        pass
