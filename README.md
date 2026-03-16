# Processamento Geoespacial com R

Este projeto está estruturado para análise de dados geoespaciais (SIG) seguindo boas práticas de organização.

## Estrutura de Pastas

- `data/raw/`: Dados originais e imutáveis (Altimetria, MapBiomas, Rodovias).
- `data/processed/`: Dados limpos e transformados prontos para análise.
- `R/`: Funções personalizadas e módulos reutilizáveis.
- `scripts/`: Scripts R para processamento pesado ou automação.
- `reports/`: Relatórios em Rmarkdown ou Quarto para visualização dos resultados.

## Pacotes Recomendados

Para começar, instale os pacotes principais executando no console do R:

```R
install.packages(c("sf", "terra", "tmap", "tidyverse", "here"))
```

- **sf**: Manipulação de vetores.
- **terra**: Manipulação de rasters.
- **tmap**: Visualização de mapas.
- **here**: Facilita o gerenciamento de caminhos de arquivos.

## Como usar

1. Abra o arquivo `proc_geo_espac.Rproj` no RStudio.
2. Coloque seus dados brutos em `data/raw/`.
3. Crie scripts de processamento em `scripts/` e salve os resultados em `data/processed/`.
