import geopandas as gpd
import os

def process_roads_pb():
    input_path = "data/raw/rodovias/SNV_202504A.shp"
    output_path = "data/raw/rodovias_pb.gpkg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Lendo malha rodoviária de: {input_path}")
    if not os.path.exists(input_path):
        print("Erro: Arquivo SNV não encontrado.")
        return

    try:
        # Lendo apenas colunas necessárias para economizar memória
        roads = gpd.read_file(input_path)
        
        print("Filtrando rodovias da Paraíba (sg_uf == 'PB')...")
        roads_pb = roads[roads['sg_uf'] == 'PB'].copy()
        
        if roads_pb.empty:
            print("Aviso: Nenhuma rodovia encontrada para PB. Verifique a coluna 'sg_uf'.")
            return

        print("Simplificando geometrias para otimizar o mapa...")
        # Simplificação leve (0.0001 graus ~ 10 metros)
        # Primeiro reprojetamos para metros se quisermos precisão, mas aqui graus basta para o mapa base.
        roads_pb['geometry'] = roads_pb.simplify(0.0001, preserve_topology=True)
        
        print(f"Salvando {len(roads_pb)} trechos em: {output_path}")
        roads_pb.to_file(output_path, driver="GPKG")
        print("Sucesso!")
        
    except Exception as e:
        print(f"Erro ao processar rodovias: {e}")

if __name__ == "__main__":
    process_roads_pb()
