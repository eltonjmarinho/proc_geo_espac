import pandas as pd
import os

def aggregate_annual(years=[2023, 2024, 2025]):
    all_dfs = []
    output_path = "data/processed/bolsa_familia_all_annual.csv"
    
    for year in years:
        input_path = f"data/processed/bolsa_familia_{year}.csv"
        if not os.path.exists(input_path):
            print(f"Aviso: Arquivo {input_path} não encontrado. Pulando...")
            continue

        print(f"Lendo dados de: {input_path}")
        df = pd.read_csv(input_path, dtype={'codigo_ibge': str})
        all_dfs.append(df)
    
    if not all_dfs:
        print("Nenhum dado para agregar.")
        return

    df_combined = pd.concat(all_dfs, ignore_index=True)
    
    agg_rules = {
        'familias_beneficiarias': 'mean',
        'valor_total': 'sum',
        'valor_medio': 'mean',
        'valor_por_familia': 'mean'
    }
    
    print("Agregando dados por município e ano...")
    df_annual = df_combined.groupby(['codigo_ibge', 'ano']).agg(agg_rules).reset_index()
    
    df_annual['familias_beneficiarias'] = df_annual['familias_beneficiarias'].round(0).astype(int)
    df_annual['valor_medio'] = df_annual['valor_medio'].round(2)
    df_annual['valor_por_familia'] = df_annual['valor_por_familia'].round(2)
    
    df_annual = df_annual.sort_values(by=['ano', 'codigo_ibge'])
    df_annual.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
    
    print(f"Agregação unificada concluída! Salvo em: {output_path}")
    print(f"Total de registros anuais: {len(df_annual)}")
    print(df_annual['ano'].value_counts())

if __name__ == "__main__":
    aggregate_annual()
