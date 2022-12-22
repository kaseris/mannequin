from app_models import *
from layout import UI


class App:
    DATABASE_PATH = '/home/kaseris/Documents/database'
    TEXTURES_PATH = '/home/kaseris/Documents/iMannequin_3D_Tool_v11_venia/texture'
    EDITOR_3D_PATH = '/home/kaseris/Documents/iMannequin_3D_Tool_v11_venia'

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
        self.controller_clear = None

        self.relevant_garments_model = None
        self.shape_similarity_window = None

        self.alt_curves_app = None
        self.alt_curves_model = None
        self.alt_curves_controller = None

        self.seam = None
        self.subpath = None

        self.controller_3d_editor_launcher = None
        self.controller_texture_selection = None

        self.editor_app_radio_button_last_choice = None

        self.query_kind = None

        self.model_selected_texture = SelectedTextureModel(texture_dir=App.TEXTURES_PATH)
        self.texture_int_value = self.model_selected_texture.texture_files[0]

        self.selected_texture_img = None

    def run(self):
        self.ui.run()

    def setup(self):
        pass


if __name__ == '__main__':
    app = App()
    app.run()
