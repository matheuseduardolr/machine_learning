"""Constantes do estudo: dados, colunas da planilha e paleta dos núcleos."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKBOOK_PATH = ROOT / "data" / "localizacao_condominios.xlsx"
CACHE_PATH = ROOT / "data" / "geocode_cache.json"
PLOT_PATH = ROOT / "images" / "nucleos_kmeans.png"
MAP_PATH = ROOT / "images" / "nucleos_mapa.html"

N_CLUSTERS = 6
HEADER_ROW = 4
COL_ORDEM = 1
COL_NOME = 3
COL_ENDERECO = 4
COL_BAIRRO = 5
COL_CIDADE = 6
COL_LAT = 7
COL_LON = 8
COL_NUCLEO = 9
COL_COR = 10

# Litoral de Maceió e Praia do Francês.
LAT_MIN, LAT_MAX = -9.92, -9.45
LON_MIN, LON_MAX = -35.98, -35.55
ACCEPTED_ADDR_TYPES = {"PointAddress", "StreetAddress", "StreetName", "POI", "Subaddress"}
MIN_SCORE = {"PointAddress": 85, "StreetAddress": 85, "Subaddress": 85, "StreetName": 80, "POI": 90}

# Núcleos numerados de sul para norte, na mesma direção da rota operacional.
NUCLEUS_COLORS = [
    ("Vermelho", "E41A1C"),
    ("Laranja", "FF7F00"),
    ("Amarelo", "F2C200"),
    ("Verde", "4DAF4A"),
    ("Azul", "377EB8"),
    ("Roxo", "984EA3"),
]

STOPWORDS = {
    "rua",
    "avenida",
    "av",
    "travessa",
    "alameda",
    "praca",
    "pca",
    "via",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "lote",
    "lotes",
    "quadra",
    "condominio",
    "edificio",
    "residencial",
    "associacao",
    "moradores",
    "comercial",
    "brasil",
    "alagoas",
}

# Coordenadas lidas no mapa quando o endereço da planilha não geocodifica.
KNOWN_COORDINATES: dict[int, tuple[float, float]] = {
    80: (-9.663066773638867, -35.7036151831492),
    131: (-9.6060765896164, -35.681401479714296),
    132: (-9.627033710973773, -35.70241385129199),
}
