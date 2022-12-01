import abc
import enum

from app import App
from app_models import QueryModel
from controllers import *
from layout import QueryImagePlaceholder


class AppStateEnum(enum.Enum):
    APP_INIT = 0
    APP_QUERY_UPLOADED_2D = 1
    APP_QUERY_UPLOADED_3D = 2
    APP_SELECTED_PATTERN = 3


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


class AppStateQueryUploaded2D(AppState):
    def __init__(self, _app, _mediator):
        super(AppStateQueryUploaded2D, self).__init__(_app=_app, _mediator=_mediator)
        self.app.controller_retrieval_apply = ControllerRetrievalApplyButton(self.app.query_model)
        self.app.retrieval_model_2d = Retrieval2DModel(App.DATABASE_PATH)

    def build(self):
        self.app.controller_query_sidebar.set_app_state(self)
        self.app.ui.layout.query_image_placeholder = QueryImagePlaceholder(master=self.app.ui.layout.root)
        self.app.ui.layout.root.bind('<Configure>', self.app.ui.layout.query_image_placeholder.dragging)
        self.app.retrieval_model_2d.build()
        self.app.controller_retrieval_apply.couple(self.app.ui.layout.query_image_placeholder.button_apply,
                                                   self.app.retrieval_model_2d, self.app.retrieval_model_3d)
        self.app.ui.layout.query_image_placeholder.draw(self.app.query_model.kind, self.app.query_model.filename)

    def update(self):
        self.app.ui.layout.query_image_placeholder.draw(self.app.query_model.kind, self.app.query_model.filename)

    def destroy(self):
        pass

    def notify_manager(self):
        pass


class AppStateQueryUploaded3D(AppState):
    def __init__(self, _app, _mediator):
        super(AppStateQueryUploaded3D, self).__init__(_app=_app, _mediator=_mediator)

    def build(self):
        pass

    def update(self):
        pass

    def destroy(self):
        pass

    def notify_manager(self):
        pass


class AppStateGarmentSelected(AppState):
    def __init__(self, _app):
        super(AppStateGarmentSelected, self).__init__(_app=_app)

    def build(self):
        pass

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
                1: AppStateQueryUploaded2D,
                2: AppStateQueryUploaded3D,
                3: AppStateGarmentSelected}

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
