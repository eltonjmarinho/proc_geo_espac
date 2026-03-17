import pandas as pd
import json
import os

def convert_json_to_csv(years=[2023, 2024, 2025]):
    for year in years:
        input_path = f"data/raw/bolsa_familia_{year}.json"
        output_path = f"data/processed/bolsa_familia_{year}.csv"
        
        # Garantir que o diretório de destino existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"--- Processando Ano {year} ---")
        print(f"Lendo dados de: {input_path}")
        if not os.path.exists(input_path):
            print(f"Aviso: Arquivo {input_path} não encontrado. Pulando...")
            continue

        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            docs = data.get('response', {}).get('docs', [])
            
            if not docs:
                print(f"Nenhum dado encontrado no JSON de {year}.")
                continue
                
            df = pd.DataFrame(docs)
            df['codigo_ibge'] = df['codigo_ibge'].astype(str).str.zfill(6)
            
            column_mapping = {
                'codigo_ibge': 'codigo_ibge',
                'anomes_s': 'referencia',
                'qtd_familias_beneficiarias_bolsa_familia_s': 'familias_beneficiarias',
                'valor_repassado_bolsa_familia_s': 'valor_total',
                'pbf_vlr_medio_benef_f': 'valor_medio'
            }
            
            df = df.rename(columns=column_mapping)
            df['referencia'] = df['referencia'].astype(str)
            df['ano'] = df['referencia'].str[:4]
            df['mes'] = df['referencia'].str[4:]
            
            df['valor_total'] = pd.to_numeric(df['valor_total'], errors='coerce')
            df['familias_beneficiarias'] = pd.to_numeric(df['familias_beneficiarias'], errors='coerce')
            df['valor_por_familia'] = df['valor_total'] / df['familias_beneficiarias']
            
            cols = [
                'codigo_ibge', 'referencia', 'ano', 'mes', 
                'familias_beneficiarias', 'valor_total', 'valor_medio', 'valor_por_familia'
            ]
            df = df[cols]
            
            df.to_csv(output_path, index=False, sep=',', encoding='utf-8-sig')
            
            print(f"Conversão de {year} concluída! Salvo em: {output_path}")
            print(f"Linhas: {df.shape[0]}\n")
            
        except Exception as e:
            print(f"Erro durante a conversão de {year}: {e}")

if __name__ == "__main__":
    convert_json_to_csv()
