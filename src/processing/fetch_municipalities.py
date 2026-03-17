import geobr
import geopandas as gpd
import os

def fetch_municipalities():
    output_path = "data/raw/municipios.gpkg"
    
    # Garantir que o diretório existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Baixando malha municipal do Brasil via geobr (IBGE)...")
    try:
        # Baixa os municípios do ano mais recente disponível ou específico (ex: 2022)
        # 2022 é o censo mais recente, mas geobr costuma ter 2020/2022.
        muni = geobr.read_municipality(year=2022)
        
        # Compatibilizar para 6 dígitos (truncando o último dígito)
        # O geobr traz como int ou float, vamos garantir string de 7 e pegar os 6 primeiros
        muni['code_muni'] = muni['code_muni'].astype(str).str.replace('\.0', '', regex=True)
        muni['code_muni6'] = muni['code_muni'].str[:6]
        
        print(f"Salvando malha em: {output_path}")
        # Salvar como GeoPackage (.gpkg) que é mais moderno e performático que Shapefile
        muni.to_file(output_path, driver="GPKG")
        
        print(f"Sucesso! {len(muni)} municípios carregados.")
        print(f"Colunas disponíveis: {muni.columns.tolist()}")
        
    except Exception as e:
        print(f"Erro ao baixar municípios: {e}")
        print("Certifique-se de que a biblioteca 'geobr' está instalada (pip install geobr).")

if __name__ == "__main__":
    fetch_municipalities()
