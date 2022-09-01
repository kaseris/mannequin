from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from mannequin.retrieval2d.retrieval_dimis import *


def main():
    extractor = load_test_model()
    deep_feats, color_feats, labels = load_feat_db()

    query_img = '/home/kaseris/Documents/fir/1.jpg'
    img = Image.open(query_img)
    f = dump_single_feature(query_img, extractor)

    clf = load_kmeans_model()
    # number 4 in the args possibly refers to the number of imgs to retrieve
    result = naive_query(f, deep_feats, color_feats, labels, 4)
    result_kmeans = kmeans_query(clf, f, deep_feats, color_feats, labels, 4)

    print(result_kmeans)
    # for i in range(len(result_kmeans)):
    #     bname = os.path.basename(result_kmeans[i][0])
    #     new_name = 'static/img/' + bname
    #     result_kmeans[i] = (new_name, result_kmeans[i][1])

if __name__ == '__main__':
    main()