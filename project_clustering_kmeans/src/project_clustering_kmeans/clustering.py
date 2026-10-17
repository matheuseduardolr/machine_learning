"""K-Means geográfico com núcleos de tamanho parecido."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans

from project_clustering_kmeans.settings import N_CLUSTERS


def to_local_meters(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    """Projeção equiretangular local, em metros, para a distância euclidiana do K-Means."""
    lat0 = np.deg2rad(float(np.mean(latitudes)))
    x = (longitudes - np.mean(longitudes)) * 111_320 * np.cos(lat0)
    y = (latitudes - np.mean(latitudes)) * 110_540
    return np.column_stack([x, y])


def cluster_balanced(latitudes: np.ndarray, longitudes: np.ndarray) -> np.ndarray:
    """Agrupa os pontos em 6 núcleos e equilibra o volume de cada um.

    O K-Means define os centros. Em seguida, cada condomínio é atribuído ao
    centro mais próximo com um limite de vagas, para que os núcleos fiquem
    com 22 ou 23 prédios. Os rótulos finais seguem a ordem sul → norte.
    """
    points = to_local_meters(latitudes, longitudes)
    count = len(points)
    base, extra = divmod(count, N_CLUSTERS)
    seed = KMeans(n_clusters=N_CLUSTERS, n_init=20, random_state=42).fit(points)
    centroids = seed.cluster_centers_.copy()
    capacities = np.full(N_CLUSTERS, base, dtype=int)
    largest = np.argsort(-np.bincount(seed.labels_, minlength=N_CLUSTERS))
    capacities[largest[:extra]] += 1

    labels = seed.labels_.copy()
    for _ in range(40):
        slots: list[int] = []
        for cluster, capacity in enumerate(capacities):
            slots.extend([cluster] * int(capacity))
        cost = cdist(points, centroids)[:, slots]
        _, columns = linear_sum_assignment(cost)
        labels = np.array([slots[column] for column in columns], dtype=int)
        updated = np.vstack(
            [
                points[labels == cluster].mean(axis=0)
                if np.any(labels == cluster)
                else centroids[cluster]
                for cluster in range(N_CLUSTERS)
            ]
        )
        if np.allclose(updated, centroids):
            break
        centroids = updated

    centroid_lat = [float(latitudes[labels == cluster].mean()) for cluster in range(N_CLUSTERS)]
    order = np.argsort(centroid_lat)
    remap = {int(old): new + 1 for new, old in enumerate(order)}
    return np.array([remap[int(label)] for label in labels], dtype=int)


def assign_nuclei(rows: list[dict], located: dict[int, dict]) -> dict[int, int]:
    located_rows = [item for item in rows if item["ordem"] in located]
    latitudes = np.array([located[item["ordem"]]["lat"] for item in located_rows])
    longitudes = np.array([located[item["ordem"]]["lon"] for item in located_rows])
    labels = cluster_balanced(latitudes, longitudes)
    return {item["ordem"]: int(label) for item, label in zip(located_rows, labels)}
