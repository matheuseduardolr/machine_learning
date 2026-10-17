"""Executa o estudo: geocodifica os endereços, ajusta o K-Means e grava os núcleos."""

from __future__ import annotations

from openpyxl import load_workbook

from project_clustering_kmeans.clustering import assign_nuclei
from project_clustering_kmeans.data import read_rows, write_results
from project_clustering_kmeans.geocoding import Geocoder
from project_clustering_kmeans.settings import MAP_PATH, NUCLEUS_COLORS, PLOT_PATH, WORKBOOK_PATH
from project_clustering_kmeans.visualization import save_map, save_plot


def summarize(rows: list[dict], located: dict[int, dict], nuclei: dict[int, int]) -> None:
    print(f"\nGeocodificados: {len(located)} de {len(rows)}")
    missing = [item for item in rows if item["ordem"] not in located]
    if missing:
        print("Sem coordenada:")
        for item in missing:
            print(f"  {item['ordem']:>3} {item['nome']} | {item['endereco']} | {item['bairro']}")

    approximate = [item for item in rows if located.get(item["ordem"], {}).get("quality") == "rua"]
    if approximate:
        print("Coordenada no meio da rua (sem número):")
        for item in approximate:
            found = located[item["ordem"]]
            print(f"  {item['ordem']:>3} {item['nome']} -> {found['address']}")

    print("\nNúcleos (sul → norte):")
    for nucleus, (color_name, _) in enumerate(NUCLEUS_COLORS, start=1):
        members = [item for item in rows if nuclei.get(item["ordem"]) == nucleus]
        bairros: dict[str, int] = {}
        for item in members:
            bairros[item["bairro"]] = bairros.get(item["bairro"], 0) + 1
        detail = ", ".join(f"{name} ({count})" for name, count in sorted(bairros.items()))
        print(f"  Núcleo {nucleus} {color_name}: {len(members)} condomínios — {detail}")


def main() -> None:
    geocoder = Geocoder()
    workbook = load_workbook(WORKBOOK_PATH)
    worksheet = workbook.active
    rows = read_rows(worksheet)
    located: dict[int, dict] = {}

    for position, item in enumerate(rows, start=1):
        found = geocoder.geocode_row(
            item["ordem"], item["nome"], item["endereco"], item["bairro"], item["cidade"]
        )
        if found is not None:
            located[item["ordem"]] = found
        status = "ok" if found else "falhou"
        quality = found["quality"] if found else "-"
        print(
            f"[{position:>3}/{len(rows)}] {status:6} {quality:6} {item['nome']}",
            flush=True,
        )
        if position % 10 == 0:
            geocoder.save()
    geocoder.save()

    nuclei = assign_nuclei(rows, located)
    write_results(worksheet, rows, located, nuclei)
    workbook.save(WORKBOOK_PATH)
    save_plot(rows, located, nuclei)
    save_map(rows, located, nuclei)
    summarize(rows, located, nuclei)
    print(f"\nPlanilha atualizada: {WORKBOOK_PATH}")
    print(f"Gráfico dos núcleos: {PLOT_PATH}")
    print(f"Mapa dos núcleos: {MAP_PATH}")
