import abc
import enum

from PIL import Image, ImageOps, ImageTk

from app import App
# from app_models import QueryModel
import instructions
from controllers import *
from layout import QueryImagePlaceholder, FrameRetrievedPlaceholder, RetrievedViewportPlaceholder,\
    FrameGarmentInformation, FramePatternPreview, FrameEditorView

class AppStateEnum(enum.Enum):
    APP_INIT = 0
    APP_QUERY_UPLOADED = 1
    APP_SELECTED_PATTERN = 2


class AppState(abc.ABC):
    def __init__(self,
                 _app: App,
                 _mediator):
        self.app = _app
        self.mediator = _mediator

    @abc.abstractmethod
    def build(self):
        pass

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def destroy(self):
        pass

    @abc.abstractmethod
    def notify_manager(self, update_flag, filename, next_state):
        pass


class AppStateInit(AppState):

    def __init__(self, _app, mediator):
        super(AppStateInit, self).__init__(_app=_app, _mediator=mediator)
        self.__is_app_running = False
        self.mediator = mediator

    def build(self):
        self.app.controller_query_query_viewer = ControllerQueryObjectQueryViewer(app_state=self)
        self.app.controller_query_sidebar = ControllerQueryObjectModelUploadButton(app_state=self)
        self.app.query_model = QueryModel(external_controller=self.app.controller_query_query_viewer)
        self.app.controller_query_query_viewer.couple(self.app.query_model, self.app.ui.layout.query_image_placeholder)
        self.app.controller_query_sidebar.couple(self.app.query_model, self.app.ui.layout.sidebar.button_upload)
        self.app.controller_query_sidebar.bind_(event_type=None,
                                                callback_fn=self.app.controller_query_sidebar.open_file)
        if not self.__is_app_running:
            self.__is_app_running = True
            self.app.ui.run()

    def update(self):
        pass

    def destroy(self):
        pass

    def notify_manager(self, update_flag: bool, filename, next_state):
        if update_flag:
            print(f'Going to state: {next_state}')
            self.mediator.notify(next_state)
        else:
            print(f'I wont go to the next state')


class AppStateQueryUploaded(AppState):
    def __init__(self, _app, _mediator):
        super(AppStateQueryUploaded, self).__init__(_app=_app, _mediator=_mediator)
        self.app.controller_retrieval_apply = ControllerRetrievalApplyButton(self.app.query_model)
        self.app.retrieval_model_2d = Retrieval2DModel(App.DATABASE_PATH)
        self.app.retrieval_model_3d = Retrieval3DModel()

        # self.controller_retrieval_apply = ControllerRetrievalApplyButton(model_query=self.app.query_model,
        #                                                                  app_state=self)
        self.app.controller_retrieved_views = ControllerRetrievedViewportViews(app_state=self)
        self.app.controller_retrieved_views3d = ControllerRetrieved3DViewportViews(app_state=self)
        self.app.controller_clear = ControllerClear(app_state=self)

    def build(self):
        self.app.ui.layout.sidebar.instructions.configure(text=instructions.INSTRUCTIONS_APPLY)
        self.app.controller_query_sidebar.set_app_state(self)
        self.app.ui.layout.query_image_placeholder = QueryImagePlaceholder(master=self.app.ui.layout.root)
        self.app.ui.layout.root.bind('<Configure>', self.app.ui.layout.query_image_placeholder.dragging)

        self.app.ui.layout.frame_retrieved = FrameRetrievedPlaceholder(master=self.app.ui.layout.frame_watermark,
                                                                       width=1290,
                                                                       height=355)
        self.app.ui.layout.frame_retrieved.build()
        for i in range(4):
            setattr(self.app.ui.layout, f'retrieved_viewport_{i + 1}',
                    RetrievedViewportPlaceholder(i, '260x260',
                                                 master=self.app.ui.layout.root))

        self.app.controller_retrieved_views3d.couple(self.app.retrieval_model_3d,
                                                     [getattr(self.app.ui.layout,
                                                              f'retrieved_viewport_{i + 1}') for i in range(4)])
        self.app.controller_retrieved_views.couple(self.app.retrieval_model_2d,
                                                   [getattr(self.app.ui.layout, f'retrieved_viewport_{i + 1}') for i in
                                                    range(4)])

        self.app.retrieval_model_2d.build()
        self.app.controller_retrieval_apply.couple(self.app.ui.layout.query_image_placeholder.button_apply,
                                                   self.app.retrieval_model_2d, self.app.retrieval_model_3d)
        self.app.ui.layout.query_image_placeholder.draw(self.app.query_model.kind, self.app.query_model.filename)

        self.app.controller_retrieval_apply.couple(self.app.ui.layout.query_image_placeholder.button_apply,
                                                   self.app.retrieval_model_2d, self.app.retrieval_model_3d)
        self.app.controller_retrieval_apply.bind(self.app.controller_retrieval_apply.on_apply)
        self.app.ui.layout.frame_watermark.label.configure(image='')
        self.app.ui.layout.frame_watermark.label.configure(text='')

        self.app.controller_clear.couple(None, self.app.ui.layout.sidebar.button_clear_all)
        self.app.controller_clear.bind(None, self.app.controller_clear.on_press)

    def update(self):
        self.app.ui.layout.query_image_placeholder.draw(self.app.query_model.kind, self.app.query_model.filename)

    def destroy(self):
        pass

    def notify_manager(self):
        self.mediator.notify(new_state=AppStateEnum.APP_SELECTED_PATTERN)


class AppStateGarmentSelected(AppState):
    def __init__(self, _app, _mediator):
        super(AppStateGarmentSelected, self).__init__(_app=_app, _mediator=_mediator)
        for i in range(4):
            setattr(self.app, f'controller_retrieved_pattern_preview_{i + 1}',
                    ControllerRetrievedPatternPreview())
        self.app.controller_pat_preview = ControllerPatternModelPreview(app_state=self)
        self.app.controller_relevant_view = ControllerRelevantPatternViews()
        self.app.controller_relevant_pattern_preview = ControllerRelevantPatternPatternPreview()
        self.app.controller_relevant_garment_info = ControllerRelevantPatternFrameInformation()
        self.app.relevant_garments_model = RelevantGarmentsModel(database_path=self.app.DATABASE_PATH)
        self.app.controller_texture_selection = ControllerTextureSelection(app_state=self)
        self.app.controller_save = ControllerSave(app_state=self)
        self.app.controller_accessory_editor = ControllerAccessoryEditor(app_state=self)

    def build(self):
        self.app.ui.layout.sidebar.instructions.configure(text=instructions.INSTRUCTIONS_SELECT)
        self.app.ui.layout.frame_information = FrameGarmentInformation(master=self.app.ui.layout.frame_watermark,
                                                                       corner_radius=9, width=327, height=553)
        self.app.ui.layout.frame_pattern_preview = FramePatternPreview(master=self.app.ui.layout.frame_watermark,
                                                                       corner_radius=9, width=1290, height=553)
        self.app.controller_pat_preview.couple(self.app.pat_model, self.app.ui.layout.frame_pattern_preview)
        self.app.controller_save.couple(None, self.app.ui.layout.sidebar.button_save)
        self.app.controller_save.bind(None, self.app.controller_save.on_press)
        self.app.ui.layout.frame_information.build()
        self.app.ui.layout.frame_pattern_preview.build()
        self.app.controller_pat_preview.bind_('pick_event', self.app.controller_pat_preview.on_pick)
        self.app.controller_pat_preview.bind_('motion_notify_event', self.app.controller_pat_preview.on_hover)
        self.app.controller_pat_preview.bind_('button_press_event',
                                              partial(self.app.controller_pat_preview.on_double_click_canvas,
                                                      self.app.relevant_garments_model))
        self.app.controller_pat_preview.bind_('key_press_event', self.app.controller_pat_preview.on_key_press)

        self.app.ui.layout.frame_pattern_editor = FrameEditorView(master=self.app.ui.layout.frame_pattern_preview,
                                                                  fg_color='#343638', width=300, height=500,
                                                                  bg_color='#343638')
        self.app.ui.layout.frame_pattern_editor.build()

        self.app.controller_ind_pat_editor = ControllerIndividualPatternEditor(master=self.app.ui.layout.root,
                                                                               app_state=self)
        self.app.controller_ind_pat_editor.couple(self.app.pat_model, self.app.ui.layout.frame_pattern_editor)

        self.app.controller_3d_editor_launcher = Controller3DEditorLauncher(app_state=self)
        self.app.controller_3d_editor_launcher.couple(None, self.app.ui.layout.frame_information.button_launch_editor)
        self.app.controller_3d_editor_launcher.bind(self.app.controller_3d_editor_launcher.on_press)
        # self.app.controller_texture_selection_browse.bind(self)

        for i in range(4):
            _controller = getattr(self.app, f'controller_retrieved_pattern_preview_{i + 1}')
            _controller.couple(self.app.retrieval_model_2d, getattr(self.app.ui.layout, f'retrieved_viewport_{i + 1}'),
                               self.app.ui.layout.frame_pattern_preview, self.app.pat_model,
                               self.app.ui.layout.frame_information, self.app.relevant_garments_model,
                               self)
            _controller.bind('<Button-1>', _controller.update_information)
            _controller.bind('<Enter>', _controller.on_enter)
            _controller.bind('<Leave>', _controller.on_leave)

        self.app.controller_texture_selection.couple(self.app.model_selected_texture,
                                                     self.app.ui.layout.frame_information.texture_setting)
        self.app.model_selected_texture.set_selected_texture(self.app.model_selected_texture.texture_files[0])
        img_default = Image.open(self.app.model_selected_texture.selected_texture)
        img_default_resized = ImageOps.contain(img_default, (55, 55))
        self.app.selected_texture_img = ImageTk.PhotoImage(img_default_resized)
        self.app.ui.layout.frame_information.label_picked_texture_preview.configure(
            image=self.app.selected_texture_img)
        self.app.controller_texture_selection.bind(None, self.app.controller_texture_selection.on_press_select_texture)

    def update(self):
        pass

    def destroy(self):
        pass

    def notify_manager(self):
        pass


class StateManager:
    def __init__(self,
                 app: App = None,
                 initial_state: AppStateEnum = AppStateEnum.APP_INIT):
        self.__app = app
        self.__initial_state = initial_state

        self.__state: AppStateEnum = initial_state
        self.__state_instance: AppState = None
        self.__mediator = Mediator(manager=self)

    def build(self):
        self.__state_instance = StateGenerator.create_state(self.__state.value, self.__app, self.__mediator)
        self.__state_instance.build()

    def update(self, new_state):
        self.__state_instance.destroy()
        self.__state = new_state
        self.__state_instance = StateGenerator.create_state(self.__state.value, self.__app, self.__mediator)
        self.__state_instance.build()


class StateGenerator:
    __states = {0: AppStateInit,
                1: AppStateQueryUploaded,
                2: AppStateGarmentSelected}

    @staticmethod
    def create_state(state, *args, **kwargs) -> AppState:
        return StateGenerator.__states[state](*args, **kwargs)


class Mediator:
    def __init__(self, manager):
        self.manager = manager

    def notify(self, new_state):
        self.manager.update(new_state=new_state)


if __name__ == '__main__':
    app = App()
    state_manager = StateManager(app=app, initial_state=AppStateEnum.APP_INIT)
    state_manager.build()
