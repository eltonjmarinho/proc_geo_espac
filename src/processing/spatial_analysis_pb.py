import geopandas as gpd
import pandas as pd
import os

def run_spatial_analysis():
    # Caminhos
    muni_path = "data/raw/municipios.gpkg"
    bf_path = "data/processed/bolsa_familia_all_annual.csv"
    output_gpkg = "data/processed/analise_espacial_pb_all.gpkg"
    output_html_unified = "reports/maps/mapa_paraiba_unificado_anos.html"
    
    if not os.path.exists(muni_path) or not os.path.exists(bf_path):
        print("Erro: Arquivos base não encontrados.")
        return

    os.makedirs(os.path.dirname(output_gpkg), exist_ok=True)
    os.makedirs(os.path.dirname(output_html_unified), exist_ok=True)

    print("Carregando malha municipal e dados agregados...")
    muni = gpd.read_file(muni_path)
    bf = pd.read_csv(bf_path, dtype={'codigo_ibge': str})
    pb_muni = muni[muni['abbrev_state'] == 'PB'].copy()
    
    import folium
    # Centralização correta (usando centróide na projeção WGS84)
    pb_wgs84 = pb_muni.to_crs("EPSG:4326")
    center = [pb_wgs84.unary_union.centroid.y, pb_wgs84.unary_union.centroid.x]
    
    m = folium.Map(location=center, zoom_start=8, tiles="CartoDB positron")

    all_years_data = []
    years = sorted(bf['ano'].unique(), reverse=True)
    pb_muni_5880 = pb_muni.to_crs("EPSG:5880")

    for year in years:
        print(f"Processando camadas para o ano: {year}")
        bf_year = bf[bf['ano'] == year].copy()
        pb_year = pb_muni_5880.merge(bf_year, left_on='code_muni6', right_on='codigo_ibge', how='left')
        
        # Geometria e Proximidade
        pb_year['area_km2'] = pb_year.geometry.area / 1_000_000
        pb_year['perimetro_km'] = pb_year.geometry.length / 1_000
        centroids_projected = pb_year.geometry.centroid
        centroids_wgs84 = centroids_projected.to_crs("EPSG:4326")
        pb_year['centroid_lat'] = centroids_wgs84.y
        pb_year['centroid_lon'] = centroids_wgs84.x
        pb_year['valor_total_mi'] = pb_year['valor_total'] / 1_000_000

        pb_year['geometry_buffer'] = pb_year.geometry.buffer(10000)
        buffers_gdf = pb_year[['name_muni', 'code_muni6', 'geometry_buffer']].copy().set_geometry('geometry_buffer')
        neighbors_join = gpd.sjoin(buffers_gdf, pb_year[['name_muni', 'code_muni6', 'geometry']], how='inner', predicate='intersects')
        neighbors_join = neighbors_join[neighbors_join['code_muni6_left'] != neighbors_join['code_muni6_right']]
        neighbors_stats = neighbors_join.groupby('code_muni6_left').agg({
            'name_muni_right': [lambda x: ", ".join(sorted(x.unique())), 'count']
        }).reset_index()
        neighbors_stats.columns = ['code_muni6', 'vizinhos_lista', 'vizinhos_contagem']
        pb_year = pb_year.merge(neighbors_stats, on='code_muni6', how='left')
        pb_year['vizinhos_contagem'] = pb_year['vizinhos_contagem'].fillna(0).astype(int)
        pb_year['vizinhos_lista'] = pb_year['vizinhos_lista'].fillna('Nenhum')

        # 1. VISÃO POR CORES (POLÍGONOS)
        # Usamos o explore diretamente no mapa para manter a legenda e o controle de camadas nativo
        m = pb_year.explore(
            m=m,
            column='valor_total_mi',
            cmap='YlOrRd',
            scheme='NaturalBreaks',
            k=5,
            name=f"Cores - {year}",
            show=(year == 2025),
            tooltip=['name_muni', 'valor_total', 'vizinhos_contagem'],
            popup=['name_muni', 'vizinhos_lista'],
            legend=True if year == 2025 else False, # Legenda visível apenas para o ano inicial
            legend_kwds=dict(colorbar=False, fmt="{:.1f} Mi"),
            style_kwds=dict(color="black", weight=0.3, fillOpacity=0.7)
        )

        # 2. VISÃO POR BOLHAS (CENTROID)
        fg_bolhas = folium.FeatureGroup(name=f"Bolhas - {year}", show=False) # Inicia desmarcado para não poluir
        pb_centroids = pb_year.copy()
        pb_centroids.geometry = pb_centroids.geometry.centroid
        max_val = pb_centroids['valor_total'].max() if not pb_centroids['valor_total'].isna().all() else 1
        pb_centroids['bubble_radius'] = (pb_centroids['valor_total'] / max_val).pow(0.5) * 20 + 2

        for _, row in pb_centroids.iterrows():
            if pd.isna(row['valor_total']): continue
            folium.CircleMarker(
                location=[row['centroid_lat'], row['centroid_lon']],
                radius=row['bubble_radius'],
                color='black',
                weight=0.5,
                fill=True,
                fill_color='blue', # Cor diferente para diferenciar do mapa de calor se sobreposto
                fill_opacity=0.5,
                tooltip=f"{row['name_muni']} ({year}) | Repasse: R$ {row['valor_total']:,.0f} | Vizinhos: {row['vizinhos_contagem']}"
            ).add_to(fg_bolhas)
        
        fg_bolhas.add_to(m)
        all_years_data.append(pb_year.drop(columns=['geometry_buffer']))

    pd.concat(all_years_data).to_file(output_gpkg, driver="GPKG")
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(output_html_unified)
    print(f"Sucesso! Mapa unificado temporal salvo em: {output_html_unified}")

if __name__ == "__main__":
    run_spatial_analysis()

if __name__ == "__main__":
    run_spatial_analysis()
