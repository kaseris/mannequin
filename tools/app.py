from app_models import *
# from controllers import *
from layout import UI


class App:
    DATABASE_PATH = '/home/kaseris/Documents/database'

    def __init__(self):
        self.ui = UI(test_shown=False)
        self.pat_model = IndividualPatternModel()
        self.query_model = None
        self.retrieval_model_2d = None
        self.retrieval_model_3d = None
        self.controller_pat_preview = None
        self.controller_query_sidebar = None
        self.controller_query_query_viewer = None
        self.controller_retrieval_apply = None
        self.controller_retrieved_views = None
        self.controller_ind_pat_editor = None
        self.controller_retrieved_views3d = None
        self.controller_relevant_view = None
        self.controller_relevant_pattern_preview = None
        self.controller_relevant_garment_info = None

        self.relevant_garments_model = None
        self.shape_similarity_window = None

        self.alt_curves_app = None
        self.alt_curves_model = None
        self.alt_curves_controller = None

        self.seam = None
        self.subpath = None

        self.controller_3d_editor_launcher = None

        self.editor_app_radio_button_last_choice = None

        self.query_kind = None

    def run(self):
        # self.setup()
        self.ui.run()

    def setup(self):
        pass


if __name__ == '__main__':
    app = App()
    app.run()
