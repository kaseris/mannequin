import os
import os.path as osp

from functools import partial
from typing import Union

import numpy as np
import tkinter.filedialog

import customtkinter

from app_models import IndividualPatternModel, QueryModel, Retrieval3DModel, Retrieval2DModel, RelevantGarmentsModel,\
    AlternativeCurvesModel
from layout import FramePatternPreview, Sidebar, ShapeSimilarityWindow, WindowAlternativeCurves
from interactive_mpl import InteractiveLine

from seam import Seam
from statemanager import AppState, AppStateEnum, AppStateGarmentSelected
from subpath import SubPath

from utils import check_path_type


class ControllerPatternModelPreview:
    def __init__(self,
                 app_state: AppState):
        self.model: Union[None, IndividualPatternModel] = None
        self.view: Union[None, FramePatternPreview] = None

        self.app_state = app_state

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
        if event.key == 'z':
            for il in self.model.interactive_lines:
                if il.state == 1:
                    self.view.interactive_preview.ax.set_xlim([il.min_x - 20., il.max_x + 20.0])
                    self.view.interactive_preview.ax.set_ylim([il.min_y - 20., il.max_y + 20.0])
                    self.view.interactive_preview.f.canvas.draw_idle()
                    break
        elif event.key == 'escape':
            min_x = min([np.min(v[:, 0]) for v in self.model.ind_pat.patterns.values()])
            min_y = min([np.min(v[:, 1]) for v in self.model.ind_pat.patterns.values()])
            max_x = max([np.max(v[:, 0]) for v in self.model.ind_pat.patterns.values()])
            max_y = max([np.max(v[:, 1]) for v in self.model.ind_pat.patterns.values()])
            self.view.interactive_preview.ax.set_xlim([min_x - 20., max_x + 20.0])
            self.view.interactive_preview.ax.set_ylim([min_y - 20., max_y + 20.0])
            self.view.interactive_preview.f.canvas.draw_idle()

    def on_double_click_canvas(self, relevant, event):
        if event.dblclick:
            self.app_state.app.ui.layout.shape_similarity_window = ShapeSimilarityWindow(relevant)
            self.app_state.app.ui.layout.shape_similarity_window.build()
            self.app_state.app.controller_relevant_garment_info.couple(
                relevant, self.app_state.app.ui.layout.shape_similarity_window,
                self.app_state.app.ui.layout.frame_information
            )

            self.bind(self.on_press)
            self.app_state.app.ui.layout.shape_similarity_window.run()

    def bind(self, fn):
        for i in range(1, 4):
            getattr(self.app_state.app.ui.layout.shape_similarity_window,
                    f'out_img_{i + 1}').configure(command=partial(fn, i))

    def on_press(self, index):
        self.app_state.app.relevant_garments_model.set_selected(index)
        self.app_state.app.pat_model.update(self.app_state.app.relevant_garments_model.suggested[index])
        self.app_state.app.ui.layout.frame_information.text_dummy_0.configure(
            placeholder_text=self.app_state.app.pat_model.name,
            state='normal')
        self.app_state.app.ui.layout.frame_information.text_dummy_1.configure(
            placeholder_text=self.app_state.app.pat_model.category,
            state='normal')
        self.app_state.app.ui.layout.frame_information.text_dummy_2.configure(
            placeholder_text=str(self.app_state.app.pat_model.n_patterns),
            state='normal')
        self.app_state.app.ui.layout.frame_information.text_dummy_3.configure(placeholder_text=str(
            self.app_state.app.pat_model.ind_pat.garment_dir),
            state='normal')
        self.app_state.app.ui.layout.frame_information.update_thumbnail(self.app_state.app.pat_model.ind_pat.garment_dir)
        self.app_state.app.ui.layout.frame_pattern_preview.draw_pattern(self.app_state.app.pat_model.interactive_lines)


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
        self.model: Union[None, Retrieval2DModel] = None
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
        self.relevant_ss_garment_model: Union[None, RelevantGarmentsModel] = None

        self.app_state: Union[None, AppStateGarmentSelected] = None

    def couple(self, model,
               view,
               pattern_preview,
               pat_model,
               information_view,
               relevant_ss_garment_model: RelevantGarmentsModel,
               app_state):
        self.model = model
        self.view = view
        self.pattern_preview = pattern_preview
        self.pat_model = pat_model
        self.information_view = information_view
        self.relevant_ss_garment_model = relevant_ss_garment_model
        self.app_state = app_state

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

        self.app_state.app.seam = Seam(self.pat_model.ind_pat.garment_dir)
        self.app_state.app.subpath = SubPath(self.pat_model.ind_pat.garment_dir)

    def request_state_update(self):
        pass


class ControllerModelReplaceButton:
    def __init__(self):
        self.model = None
        self.view = None

    def couple(self, model, view):
        self.model = model
        self.view = view

    def bind(self, event_type, callback_fn):
        if self.view.options_widget is not None:
            if hasattr(self.view.options_widget, 'button_replace'):
                self.view.options_widget.button_replace.configure(command=callback_fn)


class ControllerIndividualPatternEditor:
    def __init__(self, master, app_state):
        self.model = None
        self.view = None
        self.master = master
        self.app_state: AppStateGarmentSelected = app_state

    def couple(self, model, view):
        self.model = model
        self.view = view
        self.model.set_controller(self)

    def on_notify(self):
        self.view.update_state(f'GARMENT_{self.model.category.upper()}_SELECTED')
        self.view.update_option(self.model.selected_region)
        controller = ControllerAltCurvesAppEditor(master=self.master,
                                                  app_state=self.app_state)
        controller.couple(self.model, self.view)
        controller.bind(controller.open_alt_curve_app)
        controller_model_replace_button = ControllerModelReplaceButton()
        controller_model_replace_button.couple(self.model, self.view)
        controller_model_replace_button.bind(None, self.on_press_replace)

    def on_press_replace(self):
        curve_to_replace = None
        for il in self.model.interactive_lines:
            if ('alternative' in il.label) and (il.state == 1):
                curve_to_replace = il.data_array
                break

        choices = ['armhole', 'collar']

        for _region in curve_to_replace:
            self.model.ind_pat.replace(_region, self.model.selected_region)
            self.model.update_interactive_lines()
            if self.model.ind_pat.get_flag(choices[self.view.options_widget.choice_var.get()]):
                self.app_state.app.seam.replace(_region)
            else:
                self.app_state.app.subpath.replace(_region)

        self.app_state.app.ui.layout.frame_pattern_preview.draw_pattern(self.model.interactive_lines)

        if curve_to_replace is None:
            pass


class ControllerAltCurvesAltCurvesWindow:
    def __init__(self, app_state):
        self.model = None
        self.ind_pat_model = None
        self.view = None

        self.app_state = app_state

    def couple(self, model, ind_pat_model, view):
        self.model: AlternativeCurvesModel = model
        self.ind_pat_model = ind_pat_model
        self.view = view

    def bind(self, event_type, callback_fn):
        for view in self.view.grid.mpl_frames:
            if event_type == '<Button-1>':
                view.bind_all(event_type, callback_fn)
            else:
                view.bind(event_type, callback_fn)

    def on_enter(self, event):
        event.widget.f.patch.set_facecolor('#64676b')
        event.widget.preview.draw()

    def on_leave(self, event):
        event.widget.f.patch.set_facecolor('#343638')
        event.widget.preview.draw()

    def on_select(self, event):
        try:
            widget_idx = event.widget.master.index
            self.view.grid.set_selected(widget_idx)
            curve = self.view.grid.get_curve()
            self.model.set_curve_to_replace(curve)
            self.model.update_curves(self.ind_pat_model.ind_pat.garment_dir, self.ind_pat_model)
            self.view.destroy()
            self.app_state.app.ui.layout.frame_pattern_preview.draw_pattern(self.ind_pat_model.interactive_lines)
        except AttributeError:
            pass


class ControllerAltCurvesAppEditor:
    def __init__(self, master,
                 app_state):
        self.model = None
        self.view = None

        self.master = master
        self.__app_state = app_state

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
        model = AlternativeCurvesModel(region_choice=choices[_choice_var],
                                       garment_category=self.model.category,
                                       pattern_choice=self.model.selected_region,
                                       database='/home/kaseris/Documents/database')
        model.build()
        controller = ControllerAltCurvesAltCurvesWindow(app_state=self.__app_state)
        alt_curve_window = WindowAlternativeCurves(master=self.master)
        alt_curve_window.build(model.curves)
        controller.couple(model, self.model, alt_curve_window)
        controller.bind('<Enter>', controller.on_enter)
        controller.bind('<Leave>', controller.on_leave)
        controller.bind('<Button-1>', controller.on_select)
        alt_curve_window.mainloop()


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
        self.view_relevant = None
        self.view_info = None

    def couple(self, model, view_relevant, view_info):
        self.model = model
        self.view_relevant = view_relevant
        self.view_info = view_info

    def bind(self, event_type, callback_fn):
        pass


class Controller3DEditorLauncher:
    def __init__(self, app_state: AppStateGarmentSelected):
        self.model = None
        self.view = None
        self.app_state: AppStateGarmentSelected = app_state

    def couple(self, model, view):
        self.model = model
        self.view = view

    def bind(self, callback_fn):
        self.view.configure(command=callback_fn)

    def on_press(self):
        import subprocess
        import shutil
        if self.app_state.app.ui.layout.frame_information.text_dummy_3 != '':
            old_dir = os.getcwd()

            split_path = self.app_state.app.pat_model.ind_pat.garment_dir.split(osp.sep)
            subcategory, model = split_path[-2], split_path[-1]

            if osp.exists(osp.join(self.app_state.app.DATABASE_PATH, '.temp')):
                shutil.rmtree(osp.join(self.app_state.app.DATABASE_PATH, '.temp'))

            shutil.copytree(self.app_state.app.pat_model.ind_pat.garment_dir,
                            osp.join(self.app_state.app.DATABASE_PATH, '.temp', subcategory, model))

            if self.app_state.app.seam is None:
                self.app_state.app.seam = Seam(self.app_state.app.pat_model.ind_pat.garment_dir)

            if self.app_state.app.subpath is None:
                self.app_state.app.subpath = SubPath(self.app_state.app.pat_model.ind_pat.garment_dir)

            self.app_state.app.seam.export_to_file(
                osp.join(self.app_state.app.DATABASE_PATH, '.temp', subcategory, model), 'seam.txt')
            self.app_state.app.subpath.export_to_file(
                osp.join(self.app_state.app.DATABASE_PATH, '.temp', subcategory, model), 'subpath.txt')
            os.chdir('/home/kaseris/Documents/iMannequin_3D_Tool_v11_venia/')
            subprocess.run([f'{osp.join(os.getcwd(), "main.out")}',
                            osp.join(self.app_state.app.DATABASE_PATH, '.temp', subcategory, model) + '/'])
            os.chdir(old_dir)
        else:
            pass
