from app_models import IndividualPatternModel
from controllers import ControllerPatternModelPreview
from layout import UI


class App:
    def __init__(self):
        self.ui = UI(test_shown=True)
        self.pat_model = IndividualPatternModel()

    def run(self):
        self.setup()
        self.ui.run()

    def setup(self):
        self.pat_model.build('/home/kaseris/Documents/database/dress/d1/W62K92')
        self.ui.layout.frame_pattern_preview.draw_pattern(self.pat_model.interactive_lines)
        self.controller_pat_preview = ControllerPatternModelPreview()
        self.controller_pat_preview.couple(self.pat_model, self.ui.layout.frame_pattern_preview)
        self.controller_pat_preview.bind_('pick_event', self.controller_pat_preview.on_pick)
        self.controller_pat_preview.bind_('key_press_event', self.controller_pat_preview.on_key_press)


if __name__ == '__main__':
    app = App()
    app.run()
