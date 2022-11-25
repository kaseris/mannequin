import uuid

from os import PathLike
from pathlib import Path
from typing import Union

from individual_pattern import IndividualPattern
from interactive_mpl import InteractiveLine


class IndividualPatternModel:

    def __init__(self):
        self.__ind_pat = None
        self.__interactive_lines = []

    def build(self, garment_dir: Union[str, PathLike]):
        self.__ind_pat = IndividualPattern(garment_dir=garment_dir)
        self.__build_interactive_lines()

    def clear(self):
        self.__ind_pat = None
        self.__interactive_lines = None
        self.notify_controller(event_type='data_cleared')

    def __build_interactive_lines(self):
        # TODO: I could use the __ind_pat.pattern keys to label the interactive lines
        # It would be a convenient way to label my regions on hover
        for region in self.__ind_pat.patterns.keys():
            points = self.__ind_pat[region]
            uid = str(uuid.uuid4())
            line = InteractiveLine([points], id=uid, label=region)
            self.__interactive_lines.append(line)

    def update(self, new_garment_dir):
        self.clear()
        self.__ind_pat = IndividualPattern(new_garment_dir)
        self.__build_interactive_lines()
        self.notify_controller(event_type='data_updated')

    @property
    def ind_pat(self):
        return self.__ind_pat

    @property
    def interactive_lines(self):
        return self.__interactive_lines

    def notify_controller(self,
                          controller=None,
                          event_type=None):
        r"""
        Notifies the controller that an event happened. For example if the user requests for the data to be cleared,
        the method will let the controller know that the model data is now empty and issue a command to its bound view
        to clear the drawn data. Same applies for the change of data.

        Args:
            controller (Any): A controller that binds a IndividualPatternModel instance to a view.
            event_type (str): An event that lets the controller take a specific action to the corresponding view.
                Types can be: `clear`, `data_updated`.
        """
        pass


class QueryModel:
    def __init__(self):
        self.__query = None
        # Obj/img?
        self.__kind = None

    def build(self):
        if Path(self.__query).suffix == '.obj' or Path(self.__query).suffix == '.stl':
            self.__kind = 'mesh'
        else:
            self.__kind = 'image'

    def update(self, filename):
        self.__query = filename
        self.build()
        print(f'Updated. Current query: {self.__query}\nKind: {self.__kind}')

    def clear(self):
        self.__query = None
        self.__kind = None
