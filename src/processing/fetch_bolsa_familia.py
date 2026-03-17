import requests
import json
import os

def fetch_bolsa_familia(years=[2023, 2024, 2025]):
    for year in years:
        url = f"https://aplicacoes.mds.gov.br/sagi/servicos/misocial/?fq=anomes_s:{year}*&fl=codigo_ibge%2Canomes_s%2Cqtd_familias_beneficiarias_bolsa_familia_s%2Cvalor_repassado_bolsa_familia_s%2Cpbf_vlr_medio_benef_f&fq=valor_repassado_bolsa_familia_s%3A*&q=*%3A*&rows=100000&sort=anomes_s%20desc%2C%20codigo_ibge%20asc&wt=json&omitHeader=true"
        
        output_path = f"data/raw/bolsa_familia_{year}.json"
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"Baixando dados de {year}: {url}")
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f"Dados de {year} salvos com sucesso em: {output_path}")
            print(f"Total de registros: {len(data.get('response', {}).get('docs', []))}")
            
        except Exception as e:
            print(f"Erro ao baixar os dados de {year}: {e}")

if __name__ == "__main__":
    fetch_bolsa_familia()
