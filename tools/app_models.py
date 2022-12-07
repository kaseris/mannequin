import os
import os.path as osp

import uuid

from os import PathLike
from pathlib import Path
from typing import Union

from individual_pattern import IndividualPattern
from interactive_mpl import InteractiveLine

from mannequin.retrieval2d.retrieval_dimis import *

from fusion import get_keypoint_count, get_filename_for_bezier_points, read_bezier_points_from_txt, align_regions, \
    propose_intermediate_curves
from infer_retrieval import infer
from shape_similarities_idx import ss_dict_name_to_idx, ss_dict_idx_to_name
from utils import create_ss_matrix, similarity
from rules import rules_blouse


class IndividualPatternModel:

    def __init__(self):
        self.__ind_pat = None
        self.__interactive_lines = []
        self.__category = None
        self.__n_patterns = None
        self.__name = None
        self.__selected_region = None
        self.__last_option = None
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
        self.__ind_pat: Union[None, IndividualPattern] = None
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
        self.__ind_pat: IndividualPattern = IndividualPattern(new_garment_dir)
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
        if 'alternative' in self.__selected_region:
            self.__selected_region = self.__last_option
        else:
            self.__selected_region = region
            self.__last_option = region
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

    def add_alternative_curves(self, curves):
        self.__ind_pat.add_alternative_curves(curves)
        self.__interactive_lines = []
        self.__build_interactive_lines()


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
        self.__selected = None

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

    @property
    def suggested(self):
        return self._suggested

    @property
    def selected(self):
        return self.__selected

    def set_selected(self, idx):
        self.__selected = idx


class AlternativeCurvesModel:
    def __init__(self, region_choice='collar',
                 garment_category='dress',
                 pattern_choice='front',
                 database=None):
        self.region_choice = region_choice
        self.garment_category = garment_category
        self.pattern_choice = pattern_choice
        self.curves = []
        self.alt_garments = []
        self.__curve_to_replace = None
        self.database = database

    def build(self):
        self.alt_garments = self.find_garments_based_on_choice()
        self.get_corresponding_pattern_part()

    def reset(self):
        self.curves = []
        self.alt_garments = []
        self.__curve_to_replace = None

    def find_garments_based_on_choice(self):
        category_path = osp.join(self.database, self.garment_category)
        list_subfolders_with_paths = [f.path for f in os.scandir(category_path) if f.is_dir()]
        l = []
        for subfolder in list_subfolders_with_paths:
            for s in os.listdir(subfolder):
                l.append(osp.join(subfolder, s))
        return l

    def get_corresponding_pattern_part(self):
        for g in self.alt_garments:
            try:
                which1 = rules_blouse[self.region_choice][get_keypoint_count(g, pattern=self.pattern_choice)]
                fnames1 = [get_filename_for_bezier_points(g, self.pattern_choice, n=n) for n in which1]
                curve = []
                for fname in fnames1:
                    curve.append(read_bezier_points_from_txt(fname))
                self.curves.append(curve)
            except FileNotFoundError:
                continue

    def set_curve_to_replace(self, data):
        print(f'Replacing with data:\n {data}')
        self.__curve_to_replace = data

    @property
    def curve_to_replace(self):
        return self.__curve_to_replace

    def update_curves(self, path_to_garment1, ind_pat_model):
        aligned_alt_curve = align_regions(path_to_garment1,
                                          self.curve_to_replace,
                                          pattern=self.pattern_choice,
                                          selection=self.region_choice)
        proposed_curves = propose_intermediate_curves(path_to_garment1,
                                                      aligned_alt_curve,
                                                      pattern=self.pattern_choice,
                                                      selection=self.region_choice)
        ind_pat_model.add_alternative_curves(proposed_curves)
