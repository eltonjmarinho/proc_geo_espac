import pandas as pd
import os

def filter_latest_by_year(years=[2023, 2024, 2025]):
    all_dfs = []
    output_path = "data/processed/bolsa_familia_all_latest.csv"
    
    for year in years:
        input_path = f"data/processed/bolsa_familia_{year}.csv"
        if not os.path.exists(input_path):
            print(f"Aviso: Arquivo {input_path} não encontrado. Pulando...")
            continue

        print(f"Lendo dados de: {input_path}")
        df = pd.read_csv(input_path, dtype={'codigo_ibge': str})
        
        df['ano'] = pd.to_numeric(df['ano'])
        df['mes'] = pd.to_numeric(df['mes'])
        
        # Ordenar e pegar o último mês de cada município no ano
        df_sorted = df.sort_values(by=['codigo_ibge', 'ano', 'mes'], ascending=[True, True, False])
        df_latest = df_sorted.drop_duplicates(subset=['codigo_ibge', 'ano'], keep='first')
        
        all_dfs.append(df_latest)
    
    if all_dfs:
        df_final = pd.concat(all_dfs, ignore_index=True)
        df_final = df_final.sort_values(by=['ano', 'mes', 'codigo_ibge'], ascending=[False, False, True])
        df_final.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
        
        print(f"Filtragem unificada concluída! Salvo em: {output_path}")
        print(f"Total de registros filtrados: {len(df_final)}")
        print("\nDistribuição por Ano:")
        print(df_final['ano'].value_counts())
    else:
        print("Nenhum dado para processar.")

if __name__ == "__main__":
    filter_latest_by_year()
