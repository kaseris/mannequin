from functools import partial

from app_models import IndividualPatternModel
from layout import FramePatternPreview
from interactive_mpl import InteractiveLine


class ControllerPatternModelPreview:
    def __init__(self):
        self.model : IndividualPatternModel = None
        self.view : FramePatternPreview = None

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
        self.view.interactive_preview.f.canvas.draw_idle()

    def on_key_press(self, event):
        pass
