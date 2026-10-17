# Customer Data Preprocessing & Feature Engineering Pipeline



Pipeline de pré-processamento e feature engineering para dados de clientes, pronto para uso em modelos de Machine Learning.



## Overview

Projeto focado na construção de um workflow de dados com **Python** e **Scikit-learn**, cobrindo etapas de **limpeza, transformação e geração de features**. Incluindo análise exploratória (**EDA**), limpeza, transformação e feature engineering, com pré-processamento estruturado usando **Pipeline**.



## Tech Stack

* Python 3.12  
* Pandas, NumPy  
* Matplotlib, Seaborn  
* Scikit-learn (Pipeline, ColumnTransformer, Encoding, Scaling)  

## Estrutura do Projeto

```text
.
├── data/               # dataset original (csv)
├── notebooks/          # análise exploratória e pipeline
```

## Workflow

* **EDA:** análise exploratória com pandas (shape, tipos, estatísticas), identificação de valores faltantes e visualização com gráficos e heatmap.  

* **Limpeza:** detecção de outliers com IQR, aplicação de regras de negócio (filtro de idade, clipping de score), transformação logarítmica e remoção de duplicatas.  

* **Feature Engineering:** criação de variáveis derivadas (razão e interação) e transformação ordinal de variáveis categóricas.  

* **Pipeline de pré-processamento:** uso de `Pipeline` e `ColumnTransformer` para imputação (median / most frequent), encoding (Ordinal + One-Hot) e normalização com MinMaxScaler, separados por tipo de variável (numérica, ordinal, nominal).   