import geobr
import os
import geopandas as gpd

def fetch_risk_areas_pb():
    output_path = "data/raw/areas_risco_pb.gpkg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print("Baixando áreas de risco do Brasil (IBGE via geobr)...")
    try:
        # read_disaster_risk_area()
        risk_areas = geobr.read_disaster_risk_area(year=2010)
        
        print("Filtrando áreas de risco da Paraíba (PB)...")
        if 'abbrev_state' in risk_areas.columns:
            risk_pb = risk_areas[risk_areas['abbrev_state'] == 'PB'].copy()
        elif 'code_state' in risk_areas.columns:
            risk_pb = risk_areas[risk_areas['code_state'] == 25].copy()
        else:
            print("Aviso: Colunas de estado não identificadas.")
            risk_pb = risk_areas
            
        print(f"Salvando {len(risk_pb)} áreas de risco em: {output_path}")
        risk_pb.to_file(output_path, driver="GPKG")
        print("Sucesso!")
        
    except Exception as e:
        print(f"Erro ao baixar áreas de risco: {e}")

if __name__ == "__main__":
    fetch_risk_areas_pb()
