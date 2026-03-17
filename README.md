# Processamento Geoespacial com Python

Este projeto está estruturado para análise de dados geoespaciais (GIS) utilizando Python.

## Estrutura de Pastas

- `data/raw/`: Dados originais e imutáveis (Altimetria, MapBiomas, Rodovias).
- `data/processed/`: Dados limpos e transformados (Parquet, GeoPackage).
- `src/`: Código fonte modular (.py).
  - `processing/`: Scripts de processamento e limpeza.
  - `viz/`: Scripts para geração de mapas.
- `notebooks/`: Protótipos e análises exploratórias em Jupyter (.ipynb).

## Instalação

Recomenda-se o uso de um ambiente virtual (venv ou conda):

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar no Windows
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## Bibliotecas Principais

- **GeoPandas**: Manipulação de dados vetoriais.
- **Rasterio**: Manipulação de rasters (imagens de satélite, MDTs).
- **Folium**: Mapas interativos para web.
- **Contextily**: Provedor de mapas base (tiles).
