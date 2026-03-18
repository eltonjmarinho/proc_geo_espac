import geobr
import os
import geopandas as gpd

def fetch_schools_pb():
    output_path = "data/raw/escolas_pb.gpkg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Baixando dados de escolas do Brasil (INEP via geobr)...")
    try:
        # read_schools() traz o Brasil todo, vamos filtrar logo após
        schools = geobr.read_schools(year=2020)
        
        print("Filtrando escolas da Paraíba (PB)...")
        # geobr usa 'abbrev_state' geralmente
        if 'abbrev_state' in schools.columns:
            schools_pb = schools[schools['abbrev_state'] == 'PB'].copy()
        elif 'code_state' in schools.columns:
            schools_pb = schools[schools['code_state'] == 25].copy() # 25 é PB
        else:
            print("Aviso: Colunas de estado não identificadas. Tentando filtrar por nome de município or listagem.")
            schools_pb = schools # Fallback: manter tudo se não souber filtrar agora
            
        print(f"Salvando {len(schools_pb)} escolas em: {output_path}")
        schools_pb.to_file(output_path, driver="GPKG")
        print("Sucesso!")
        
    except Exception as e:
        print(f"Erro ao baixar escolas: {e}")

if __name__ == "__main__":
    fetch_schools_pb()
