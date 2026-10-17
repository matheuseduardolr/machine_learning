"""Gráfico e mapa dos núcleos encontrados pelo K-Means."""

from __future__ import annotations

import html

import folium
import matplotlib.pyplot as plt
import numpy as np
import xyzservices.providers as tiles
from scipy.spatial import ConvexHull, QhullError

from project_clustering_kmeans.settings import MAP_PATH, NUCLEUS_COLORS, PLOT_PATH

# O htmlpreview do GitHub só executa scripts que estão no repositório.
# Leaflet e jQuery ficam em vendor/ e o HTML aponta para esses arquivos.
_LOCAL_SCRIPTS = {
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js": "../vendor/leaflet.js",
    "https://code.jquery.com/jquery-3.7.1.min.js": "../vendor/jquery.min.js",
}


def save_plot(rows: list[dict], located: dict[int, dict], nuclei: dict[int, int]) -> None:
    PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 10))
    for nucleus, (color_name, color_hex) in enumerate(NUCLEUS_COLORS, start=1):
        points = [
            item
            for item in rows
            if nuclei.get(item["ordem"]) == nucleus and item["ordem"] in located
        ]
        if not points:
            continue
        ax.scatter(
            [located[item["ordem"]]["lon"] for item in points],
            [located[item["ordem"]]["lat"] for item in points],
            c=f"#{color_hex}",
            s=36,
            label=f"Núcleo {nucleus} ({color_name})",
            zorder=2,
        )
    ax.set_title("Condomínios agrupados em 6 núcleos de volume parecido")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect(1 / np.cos(np.deg2rad(9.66)))
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(loc="upper left", frameon=True)
    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=140)
    plt.close(fig)


def group_polygon(latitudes: list[float], longitudes: list[float]) -> list[list[float]] | None:
    points = np.unique(np.round(np.column_stack([latitudes, longitudes]), 6), axis=0)
    if len(points) < 3:
        return None
    try:
        hull = ConvexHull(points)
    except QhullError:
        return None
    return points[hull.vertices].tolist()


def _use_local_scripts(path) -> None:
    text = path.read_text(encoding="utf-8")
    for remote, local in _LOCAL_SCRIPTS.items():
        text = text.replace(f'<script src="{remote}"></script>', f'<script src="{local}"></script>')
    path.write_text(text, encoding="utf-8")


def save_map(rows: list[dict], located: dict[int, dict], nuclei: dict[int, int]) -> None:
    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    located_rows = [item for item in rows if item["ordem"] in located and item["ordem"] in nuclei]
    latitudes = [located[item["ordem"]]["lat"] for item in located_rows]
    longitudes = [located[item["ordem"]]["lon"] for item in located_rows]
    mapa = folium.Map(
        location=[float(np.mean(latitudes)), float(np.mean(longitudes))],
        zoom_start=12,
        tiles=tiles.Esri.WorldStreetMap,
        control_scale=True,
    )

    for nucleus, (color_name, color_hex) in enumerate(NUCLEUS_COLORS, start=1):
        members = [item for item in located_rows if nuclei[item["ordem"]] == nucleus]
        if not members:
            continue
        layer = folium.FeatureGroup(name=f"Núcleo {nucleus} · {color_name} ({len(members)})", show=True)
        color = f"#{color_hex}"
        polygon = group_polygon(
            [located[item["ordem"]]["lat"] for item in members],
            [located[item["ordem"]]["lon"] for item in members],
        )
        if polygon is not None:
            folium.Polygon(
                locations=polygon,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.16,
                tooltip=f"Núcleo {nucleus} · {color_name}",
            ).add_to(layer)
        for item in members:
            found = located[item["ordem"]]
            popup = (
                f"<b>{html.escape(item['nome'])}</b><br>"
                f"Núcleo {nucleus} · {color_name}<br>"
                f"{html.escape(item['endereco'])}<br>"
                f"{html.escape(item['bairro'])}, {html.escape(item['cidade'])}"
            )
            folium.CircleMarker(
                location=[found["lat"], found["lon"]],
                radius=7,
                color="#ffffff",
                weight=1.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.95,
                tooltip=f"Núcleo {nucleus} · {item['nome']}",
                popup=folium.Popup(popup, max_width=320),
            ).add_to(layer)
        layer.add_to(mapa)

    legend_rows = "".join(
        (
            "<div style='display:flex;align-items:center;gap:8px;margin:4px 0'>"
            f"<span style='width:12px;height:12px;border-radius:50%;background:#{color_hex};"
            "display:inline-block;border:1px solid #fff'></span>"
            f"<span>Núcleo {nucleus} · {color_name}</span></div>"
        )
        for nucleus, (color_name, color_hex) in enumerate(NUCLEUS_COLORS, start=1)
    )
    legend = (
        "<div style='position:fixed;bottom:24px;left:24px;z-index:9999;background:#fff;"
        "padding:10px 12px;border:1px solid #ccc;font:14px sans-serif'>"
        "<div style='font-weight:700;margin-bottom:6px'>Núcleos</div>"
        f"{legend_rows}</div>"
    )
    mapa.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(mapa)
    mapa.fit_bounds([[min(latitudes), min(longitudes)], [max(latitudes), max(longitudes)]], padding=(24, 24))
    mapa.save(MAP_PATH)
    _use_local_scripts(MAP_PATH)
