import json
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.cluster import KMeans

a = pd.read_csv('data/processed/sampling/eligibility_audit.csv')
p = a[a.p4_use == 'POSITIVE_EVENT']
inv = pd.read_csv('data/processed/inventory/inventory_spatial_suitability.csv').set_index('source_record_id')
from pyproj import Transformer
tr = Transformer.from_crs('EPSG:4326', 'EPSG:32643', always_xy=True)
x, y = tr.transform(inv.loc[p.source_record_id, 'lon_original'].to_numpy(float),
                    inv.loc[p.source_record_id, 'lat_original'].to_numpy(float))
xy = np.c_[x, y]
pairs = cKDTree(xy).query_pairs(1000.0, output_type='ndarray')
n = len(xy)
parent = list(range(n))
def f(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i
for u, v in pairs:
    ru, rv = f(int(u)), f(int(v))
    if ru != rv:
        parent[rv] = ru
lab = np.array([f(i) for i in range(n)])
_, lab = np.unique(lab, return_inverse=True)
nc = lab.max() + 1
cxy = np.array([xy[lab == c].mean(axis=0) for c in range(nc)])
cn = np.array([(lab == c).sum() for c in range(nc)], dtype=float)
print('clusters', nc, 'sizes', sorted(cn.astype(int), reverse=True)[:8])

km = KMeans(n_clusters=5, random_state=20261026, n_init=100).fit(cxy, sample_weight=cn)
print('kmeans fold counts', np.bincount(km.labels_, weights=cn, minlength=5).astype(int).tolist())

MIN = 45
labels = km.labels_.copy()
counts = np.bincount(labels, weights=cn, minlength=5).astype(int)
print('start spread', counts.max() - counts.min(), counts.tolist())
for it in range(500):
    counts = np.bincount(labels, weights=cn, minlength=5).astype(int)
    hi, lo = int(counts.argmax()), int(counts.argmin())
    move, score_best = None, int(counts.max() - counts.min())
    for c in np.flatnonzero(labels == hi):
        if counts[hi] - cn[c] < MIN:
            continue
        t = counts.copy(); t[hi] -= int(cn[c]); t[lo] += int(cn[c])
        s = int(t.max() - t.min())
        if s < score_best:
            move, score_best = int(c), s
    if move is None:
        break
    labels[move] = lo
print('after', it, 'moves', np.bincount(labels, weights=cn, minlength=5).astype(int).tolist())
print('cluster sizes in hi fold?', )
for fo in range(5):
    print(' fold', fo, 'clusters', (labels == fo).sum(), 'positives',
          int(np.bincount(labels, weights=cn, minlength=5)[fo]))
