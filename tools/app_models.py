import os
import os.path as osp

import uuid

from os import PathLike
from pathlib import Path
from typing import Union

from individual_pattern import IndividualPattern
from interactive_mpl import InteractiveLine

from mannequin.retrieval2d.retrieval_dimis import *
from infer_retrieval import infer
from shape_similarities_idx import ss_dict_name_to_idx, ss_dict_idx_to_name
from utils import create_ss_matrix, similarity


class IndividualPatternModel:

    def __init__(self):
        self.__ind_pat = None
        self.__interactive_lines = []
        self.__category = None
        self.__n_patterns = None
        self.__name = None
        self.__selected_region = None

        self.__editor_controller = None

    def build(self, garment_dir: Union[str, PathLike]):
        self.__ind_pat = IndividualPattern(garment_dir=garment_dir)
        self.__name = Path(garment_dir).name
        _ind_patterns_path = osp.join(garment_dir, 'individual patterns')
        _n_pats = len(os.listdir(_ind_patterns_path)) // 2
        self.__n_patterns = _n_pats
        categories = ['dress', 'blouse', 'skirt']
        for cat in categories:
            if cat in garment_dir:
                category = cat
        self.__category = category
        self.__build_interactive_lines()

    def clear(self):
        self.__ind_pat = None
        self.__category = None
        self.__n_patterns = None
        self.__name = None
        self.__selected_region = None
        self.__interactive_lines = []
        # self.notify_controller()

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
        self.__name = Path(new_garment_dir).name
        _ind_patterns_path = osp.join(new_garment_dir, 'individual patterns')
        _n_pats = len(os.listdir(_ind_patterns_path)) // 2
        self.__n_patterns = _n_pats
        categories = ['dress', 'blouse', 'skirt']
        for cat in categories:
            if cat in new_garment_dir:
                category = cat
        self.__category = category
        self.__build_interactive_lines()

    @property
    def ind_pat(self):
        return self.__ind_pat

    @property
    def interactive_lines(self):
        return self.__interactive_lines

    @property
    def name(self):
        return self.__name

    @property
    def n_patterns(self):
        return self.__n_patterns

    @property
    def category(self):
        return self.__category

    def set_selected_region(self, region):
        self.__selected_region = region
        self.notify_controller()

    @property
    def selected_region(self):
        return self.__selected_region

    def set_controller(self, controller):
        self.__editor_controller = controller

    def notify_controller(self):
        r"""
        Notifies the controller that an event happened. For example if the user requests for the data to be cleared,
        the method will let the controller know that the model data is now empty and issue a command to its bound view
        to clear the drawn data. Same applies for the change of data.
        """
        self.__editor_controller.on_notify()


class QueryModel:
    def __init__(self,
                 external_controller):
        self.__query = None
        # Obj/img?
        self.__kind = None
        self.__external_controller = external_controller

    def build(self):
        if Path(self.__query).suffix == '.obj' or Path(self.__query).suffix == '.stl':
            self.__kind = 'mesh'
        else:
            self.__kind = 'image'

    def update(self, filename):
        self.__query = filename
        self.build()
        # self.notify_controller()

    def clear(self):
        self.__query = None
        self.__kind = None

    @property
    def kind(self):
        return self.__kind

    @property
    def filename(self):
        return self.__query

    @property
    def is_empty(self):
        return self.__query is None

    def notify_controller(self):
        r"""
        Notifies the controller that an event happened. For example if the user requests for the data to be cleared,
        the method will let the controller know that the model data is now empty and issue a command to its bound view
        to clear the drawn data. Same applies for the change of data.
        """
        self.__external_controller.update_view()


class Retrieval2DModel:
    def __init__(self, database_path):
        self.extractor = None
        self.deep_feats, self.color_feats, self.labels = None, None, None
        self.clf = None
        self.database_path = database_path

        self.__garments_path = []
        self.__retrieved = []
        self.__ind = []
        self.__paths = []

        self.__external_controller = None

    def build(self):
        self.extractor = load_test_model()
        self.deep_feats, self.color_feats, self.labels = load_feat_db()
        self.clf = load_kmeans_model()
        with open(osp.join(self.database_path, 'paths/garment_paths.txt'), 'r') as _f:
            for line in _f:
                _l = line.strip().split(', ')
                self.__garments_path.append(osp.join(self.database_path, _l[0][2:]))

    def infer(self, query_img):
        _features = dump_single_feature(query_img, self.extractor)
        res, ind = naive_query(_features, self.deep_feats, self.color_feats, self.__garments_path, retrieval_top_n=4)
        self.update(res, ind)

    def update(self, res, ind):
        self.__retrieved = res
        self.__ind = ind
        self.__paths = list(map(lambda _x: str(Path(_x[0]).parent), res))
        self.notify_controller()

    def clear(self):
        self.__retrieved = []
        self.__ind = []
        self.__paths = []

    @property
    def retrieved(self):
        return self.__retrieved

    @property
    def ind(self):
        return self.__ind

    @property
    def paths(self):
        return self.__paths

    def set_controller(self, controller):
        self.__external_controller = controller

    def notify_controller(self):
        self.__external_controller.draw()
        self.__external_controller.on_notify()


class Retrieval3DModel:
    def __init__(self):
        self.__garments_path = []
        self.__retrieved = []
        self.__ind = []
        self.__paths = []

        self.__external_controller = None

    def build(self):
        pass

    def infer(self, query_obj):
        retrieved, ind = infer(query_obj, k=4, gallery_paths=None, object_type='obj')
        self.update(retrieved, ind)

    def update(self, res, ind):
        self.__retrieved = res
        self.__ind = ind
        self.__paths = list(map(lambda _x: str(Path(_x).parent), res))
        self.notify_controller()

    def clear(self):
        self.__retrieved = []
        self.__ind = []
        self.__paths = []

    @property
    def retrieved(self):
        return self.__retrieved

    @property
    def ind(self):
        return self.__ind

    @property
    def paths(self):
        return self.__paths

    def set_controller(self, controller):
        self.__external_controller = controller

    def notify_controller(self):
        self.__external_controller.draw()


class RelevantGarmentsModel:
    def __init__(self,
                 database_path):
        self.selected_garment = IndividualPatternModel()
        self.database_path = database_path
        self._suggested = []
        self.filenames = []
        self.__controller = None

    def build(self):
        path_to_ss = osp.join(self.database_path,
                              self.selected_garment.category,
                              f'ss_{self.selected_garment.category}.txt')
        try:
            selected_idx = ss_dict_name_to_idx[self.selected_garment.category][self.selected_garment.name]
        except KeyError:
            selected_idx = ss_dict_name_to_idx[self.selected_garment.category][self.selected_garment.name]
        ss_mat = create_ss_matrix(path_to_ss)

        list_similarities = []
        for i in range(len(ss_mat)):
            list_similarities.append(similarity(selected_idx, i, ss_mat))

        arr = np.asarray(list_similarities)
        suggested = arr.argsort()[-4:]
        # self._suggested = [osp.join(self.database_path,
        #                             self.selected_garment.category,
        #                             ss_dict_idx_to_name[self.selected_garment.category][idx]) for idx in suggested]
        filenames = []
        for root, dirs, files in os.walk(self.database_path):
            for name in dirs:
                filenames.append(os.path.join(root, name))
        self._suggested = []
        for idx, s in enumerate(suggested):
            for dirname in filenames:
                if ss_dict_idx_to_name[self.selected_garment.category][s] in dirname:
                    self._suggested.append(dirname)
                    break
            # self._suggested = [a for a in filenames if a in ss_dict_idx_to_name[self.selected_garment.category][_]]

        self._suggested[0] = self.selected_garment.ind_pat.garment_dir

    def update(self, new_garment):
        self.selected_garment.update(new_garment_dir=new_garment)
        self.build()

    def set_controller(self, controller):
        self.__controller = controller
