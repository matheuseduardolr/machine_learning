# Agrupamento de condomínios com K-Means

Estudo de agrupamento geográfico dos condomínios de uma rota operacional no litoral de Maceió e na Praia do Francês. O objetivo é formar 6 núcleos pela proximidade, com volume parecido entre os grupos.

## Objetivo

Particionar os condomínios em **k = 6** núcleos de modo que:

- prédios próximos fiquem no mesmo núcleo;
- nenhum núcleo concentre quase toda a rota enquanto outro fica com poucos prédios.

O K-Means clássico não controla o tamanho dos grupos. Aqui a atribuição dos pontos aos centros respeita uma capacidade, e cada núcleo fica com 22 ou 23 condomínios.

## Dados

A planilha `data/localizacao_condominios.xlsx` traz nome, endereço, bairro e cidade. Esses campos são geocodificados para latitude e longitude, que entram no modelo como atributos. Três endereços não foram localizados pelo geocodificador e usam coordenada informada manualmente.

## Método

1. Geocodificar nome, endereço, bairro e cidade.
2. Projetar latitude e longitude para um plano local em metros, para que a distância euclidiana do K-Means corresponda à proximidade no mapa.
3. Ajustar `KMeans(n_clusters=6, n_init=20, random_state=42)`.
4. Reatribuir cada condomínio ao centro mais próximo, com vagas limitadas, pelo algoritmo de atribuição de custo mínimo.
5. Numerar os núcleos pela latitude do centroide, de sul para norte, e associar uma cor a cada um.

## Resultados

- 134 condomínios georreferenciados.
- 6 núcleos, com 22 ou 23 condomínios cada.
- Planilha com latitude, longitude, núcleo e cor.
- Gráfico em `images/nucleos_kmeans.png`.
- Mapa interativo em `images/nucleos_mapa.html`.

## Como executar

Na pasta do projeto:

```text
uv run project-clustering-kmeans
```

O notebook `notebooks/main.ipynb` reproduz o agrupamento a partir das coordenadas já gravadas na planilha, sem chamar o geocodificador de novo.

## Estrutura

```text
.
├── data/                  # planilha e cache de geocodificação
├── images/                # gráfico e mapa dos núcleos
├── notebooks/main.ipynb   # estudo do K-Means
└── src/project_clustering_kmeans/
    ├── geocoding.py       # endereço → coordenada
    ├── clustering.py      # K-Means com capacidade
    ├── data.py            # leitura e gravação da planilha
    ├── visualization.py   # gráfico e mapa
    └── pipeline.py        # execução do estudo
```

## Tecnologias

* Python 3.12
* Pandas, NumPy
* Scikit-learn (`KMeans`)
* SciPy (atribuição com capacidade)
* Matplotlib, Folium
* GeoPy, OpenPyXL
