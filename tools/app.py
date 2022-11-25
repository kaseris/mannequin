from app_models import *
from controllers import *
from layout import UI

import tkinter.filedialog as filedialog


class App:
    def __init__(self):
        self.ui = UI(test_shown=True)
        self.pat_model = IndividualPatternModel()
        self.query_model = None
        self.controller_pat_preview = None
        self.controller_query_sidebar = None
        self.controller_query_query_viewer = None

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
        self.controller_query_query_viewer.couple(self.query_model, self.ui.layout.query_image_placeholder)
        self.controller_pat_preview.couple(self.pat_model, self.ui.layout.frame_pattern_preview)
        self.controller_query_sidebar.couple(self.query_model, self.ui.layout.sidebar.button_upload)
        self.controller_pat_preview.bind_('pick_event', self.controller_pat_preview.on_pick)
        self.controller_pat_preview.bind_('motion_notify_event', self.controller_pat_preview.on_hover)
        self.controller_query_sidebar.bind_(event_type=None, callback_fn=self.controller_query_sidebar.open_file)


if __name__ == '__main__':
    app = App()
    app.run()
