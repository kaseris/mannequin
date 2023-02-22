from app_models import *
from layout import UI
import cfg

class App:
    DATABASE_PATH = cfg.DATABASE_DIR
    # TODO:
    TEXTURES_PATH = f'{cfg.ROOT_DIR}/GarmentStudio/texture'
    EDITOR_3D_PATH = f'{cfg.ROOT_DIR}/GarmentStudio/'

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
        self.controller_save = None

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

    def clear(self, clear_query=False):
        if clear_query:
            if self.query_model:
                self.query_model.clear()
                self.ui.layout.query_image_placeholder.clear()

        if self.retrieval_model_2d:
            self.retrieval_model_2d.clear()

        if self.retrieval_model_3d:
            self.retrieval_model_3d.clear()

        for i in range(4):
            getattr(self.ui.layout, f'retrieved_viewport_{i + 1}').clear()

        if self.alt_curves_model:
            self.alt_curves_model.reset()

        # if self.app_state.app.relevant_garments_model:
        #     self.app_state.app.relevant_garments_model.reset()
        if self.ui.layout.frame_pattern_preview:
            self.ui.layout.frame_pattern_preview.clear()

        if self.ui.layout.frame_information:
            if self.ui.layout.frame_information.text_dummy_0 != '':
                self.ui.layout.frame_information.text_dummy_0.configure(placeholder_text='')
                self.ui.layout.frame_information.text_dummy_1.configure(placeholder_text='')
                self.ui.layout.frame_information.text_dummy_2.configure(placeholder_text='')
                self.ui.layout.frame_information.text_dummy_3.configure(placeholder_text='')
                self.ui.layout.frame_information.img_resized = None
                self.ui.layout.frame_information.image_garment_preview.configure(image=None)

        if self.ui.layout.frame_pattern_editor:
            self.ui.layout.frame_pattern_editor.reset()


if __name__ == '__main__':
    app = App()
    app.run()
