import geopandas as gpd
import os

def plot_pb_interactive():
    input_path = "data/raw/municipios.gpkg"
    output_path = "reports/maps/mapa_paraiba_interativo.html"
    
    if not os.path.exists(input_path):
        print(f"Erro: Arquivo {input_path} não encontrado. Execute fetch_municipalities.py primeiro.")
        return

    # Garantir diretório de saída
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Carregando malha municipal...")
    muni = gpd.read_file(input_path)
    
    print("Filtrando municípios da Paraíba (PB)...")
    pb = muni[muni['abbrev_state'] == 'PB'].copy()
    
    if pb.empty:
        print("Erro: Nenhum município encontrado para PB.")
        return
        
    print(f"Gerando mapa interativo para {len(pb)} municípios...")
    # Usando o método explore() do GeoPandas (que usa folium por baixo)
    # tooltip mostra o nome do município ao passar o mouse
    # popup mostra detalhes ao clicar
    m = pb.explore(
        column='name_muni',  # Cores baseadas no nome (distintas) ou deixar uniforme
        tooltip='name_muni',
        popup=True,
        cmap='viridis',
        tiles="CartoDB positron",  # Fundo leve e limpo
        style_kwds=dict(color="black", weight=0.5) # Bordas finas
    )
    
    print(f"Salvando mapa em: {output_path}")
    m.save(output_path)
    print("Sucesso! Abra o arquivo HTML no seu navegador para ver o mapa.")

if __name__ == "__main__":
    plot_pb_interactive()
