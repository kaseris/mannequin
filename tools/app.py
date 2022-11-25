from app_models import *
from controllers import *
from layout import UI


class App:
    DATABASE_PATH = '/home/kaseris/Documents/database'

    def __init__(self):
        self.ui = UI(test_shown=True)
        self.pat_model = IndividualPatternModel()
        self.query_model                    = None
        self.retrieval_model_2d             = None
        self.controller_pat_preview         = None
        self.controller_query_sidebar       = None
        self.controller_query_query_viewer  = None
        self.controller_retrieval_apply     = None

    def run(self):
        self.setup()
        self.ui.run()

    def setup(self):
        self.pat_model.build('/home/kaseris/Documents/database/dress/d1/W62K92')
        self.ui.layout.frame_pattern_preview.draw_pattern(self.pat_model.interactive_lines)
        self.controller_pat_preview = ControllerPatternModelPreview()
        self.controller_query_sidebar = ControllerQueryObjectModelUploadButton()
        self.controller_query_query_viewer = ControllerQueryObjectQueryViewer()

        self.query_model = QueryModel(external_controller=self.controller_query_query_viewer)
        self.retrieval_model_2d = Retrieval2DModel(App.DATABASE_PATH)
        self.retrieval_model_2d.build()

        self.controller_retrieval_apply = ControllerRetrievalApplyButton(self.query_model)
        self.controller_retrieval_apply.couple(self.ui.layout.query_image_placeholder.button_apply,
                                               self.retrieval_model_2d, None)
        self.controller_retrieval_apply.bind(self.controller_retrieval_apply.on_apply)

        self.controller_query_query_viewer.couple(self.query_model, self.ui.layout.query_image_placeholder)
        self.controller_pat_preview.couple(self.pat_model, self.ui.layout.frame_pattern_preview)
        self.controller_query_sidebar.couple(self.query_model, self.ui.layout.sidebar.button_upload)
        self.controller_pat_preview.bind_('pick_event', self.controller_pat_preview.on_pick)
        self.controller_pat_preview.bind_('motion_notify_event', self.controller_pat_preview.on_hover)
        self.controller_query_sidebar.bind_(event_type=None, callback_fn=self.controller_query_sidebar.open_file)


if __name__ == '__main__':
    app = App()
    app.run()
