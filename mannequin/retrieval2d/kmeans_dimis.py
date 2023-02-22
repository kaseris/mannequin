# -*- coding:utf-8 -*-


from sklearn.cluster import KMeans
from .retrieval_dimis import load_feat_db
import joblib
from .config import N_CLUSTERS, DIMIS_DATASET_BASE
import os


if __name__ == '__main__':
    feats, colored_labels, labels = load_feat_db()
    model = KMeans(n_clusters=N_CLUSTERS, random_state=0).fit(feats)
    model_path = os.path.join(DIMIS_DATASET_BASE, r'embeddings/models', r'kmeans.m')
    joblib.dump(model, model_path)
