from app_models import IndividualPatternModel
from layout import UI


class App:
    def __init__(self):
        self.ui = UI(test_shown=False)
        self.pat_model = IndividualPatternModel()
        # self.pat_model.build('/home/kaseris/Documents/database/dress/d1/W62K92')
        # self.ui.layout.frame_pattern_preview.draw_pattern(self.pat_model.interactive_lines)

    def run(self):
        self.ui.run()


if __name__ == '__main__':
    app = App()
    app.run()
