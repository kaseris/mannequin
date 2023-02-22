# -*- coding:utf-8 -*-


from sklearn.cluster import KMeans
from .retrieval import load_feat_db
import joblib
from .config import DATASET_BASE, N_CLUSTERS, DIMIS_DATASET_BASE
import os


if __name__ == '__main__':
    feats, colored_labels, labels = load_feat_db()
    model = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(feats)
    model_path = os.path.join(DATASET_BASE, r'models', r'kmeans.m')
    joblib.dump(model, model_path)
