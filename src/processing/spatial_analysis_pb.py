import geopandas as gpd
import pandas as pd
import os
import folium

def run_spatial_analysis():
    # Caminhos
    muni_path = "data/raw/municipios.gpkg"
    bf_path = "data/processed/bolsa_familia_all_annual.csv"
    schools_path = "data/raw/escolas_pb.gpkg"
    roads_path = "data/raw/rodovias_pb.gpkg"
    risk_path = "data/raw/areas_risco_pb.gpkg"
    output_gpkg = "data/processed/analise_espacial_pb_all.gpkg"
    output_html_unified = "reports/maps/mapa_paraiba_unificado_anos.html"
    
    if not os.path.exists(muni_path) or not os.path.exists(bf_path):
        print("Erro: Arquivos base não encontrados.")
        return

    os.makedirs(os.path.dirname(output_gpkg), exist_ok=True)
    os.makedirs(os.path.dirname(output_html_unified), exist_ok=True)

    print("Carregando malha municipal, dados agregados e infraestrutura...")
    muni = gpd.read_file(muni_path)
    bf = pd.read_csv(bf_path, dtype={'codigo_ibge': str})
    pb_muni = muni[muni['abbrev_state'] == 'PB'].copy()
    
    # 1. Escolas (Join Espacial)
    if os.path.exists(schools_path):
        schools = gpd.read_file(schools_path).to_crs(pb_muni.crs)
        schools_in_muni = gpd.sjoin(schools, pb_muni[['code_muni', 'geometry']], how='inner', predicate='within')
        school_counts = schools_in_muni.groupby('code_muni').size().reset_index(name='num_escolas')
        pb_muni = pb_muni.merge(school_counts, on='code_muni', how='left')
        pb_muni['num_escolas'] = pb_muni['num_escolas'].fillna(0).astype(int)
    else:
        pb_muni['num_escolas'] = 0

    # 2. Áreas de Risco (Intersecção)
    if os.path.exists(risk_path):
        print("Calculando intersecção com áreas de risco...")
        # Lemos o risco e renomeamos para evitar conflito de nomes idênticos no overlay
        risk = gpd.read_file(risk_path).to_crs("EPSG:5880")
        risk = risk.rename(columns={'code_muni': 'code_muni_risk', 'name_muni': 'name_muni_risk'})
        
        pb_muni_5880_temp = pb_muni.to_crs("EPSG:5880")
        
        # Intersecção espacial (overlay mantém as propriedades de ambos)
        # Usamos apenas as colunas necessárias de pb_muni para o cálculo
        risk_intersection = gpd.overlay(risk, pb_muni_5880_temp[['code_muni', 'geometry']], how='intersection')
        
        if not risk_intersection.empty:
            risk_intersection['area_risco_m2'] = risk_intersection.geometry.area
            # Agora agrupamos pelo code_muni que veio dos polígonos dos municípios
            risk_by_muni = risk_intersection.groupby('code_muni')['area_risco_m2'].sum().reset_index()
            risk_by_muni['area_risco_km2'] = risk_by_muni['area_risco_m2'] / 1_000_000
            
            pb_muni = pb_muni.merge(risk_by_muni[['code_muni', 'area_risco_km2']], on='code_muni', how='left')
            pb_muni['area_risco_km2'] = pb_muni['area_risco_km2'].fillna(0)
        else:
            pb_muni['area_risco_km2'] = 0
    else:
        pb_muni['area_risco_km2'] = 0

    # 3. Rodovias (Intersecção e Extensão)
    if os.path.exists(roads_path):
        print("Calculando extensão de rodovias por município...")
        roads_pb = gpd.read_file(roads_path).to_crs("EPSG:5880")
        pb_muni_5880_temp = pb_muni.to_crs("EPSG:5880")
        
        # Intersecção espacial: corta as linhas nos limites dos municípios
        roads_intersection = gpd.overlay(roads_pb, pb_muni_5880_temp[['code_muni', 'geometry']], how='intersection')
        roads_intersection['extensao_m'] = roads_intersection.geometry.length
        
        roads_by_muni = roads_intersection.groupby('code_muni')['extensao_m'].sum().reset_index()
        roads_by_muni['extensao_rodovias_km'] = roads_by_muni['extensao_m'] / 1_000
        
        pb_muni = pb_muni.merge(roads_by_muni[['code_muni', 'extensao_rodovias_km']], on='code_muni', how='left')
        pb_muni['extensao_rodovias_km'] = pb_muni['extensao_rodovias_km'].fillna(0)
    else:
        pb_muni['extensao_rodovias_km'] = 0

    # Centralização
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

        # Visão por Cores
        m = pb_year.explore(
            m=m,
            column='valor_total_mi',
            cmap='YlOrRd',
            scheme='NaturalBreaks',
            k=5,
            name=f"Cores - {year}",
            show=(year == 2025),
            tooltip=['name_muni', 'valor_total', 'num_escolas', 'area_risco_km2', 'extensao_rodovias_km'],
            popup=['name_muni', 'vizinhos_lista'],
            legend=True if year == 2025 else False,
            legend_kwds=dict(colorbar=False, fmt="{:.1f} Mi"),
            style_kwds=dict(color="black", weight=0.3, fillOpacity=0.7)
        )

        # Visão por Bolhas
        fg_bolhas = folium.FeatureGroup(name=f"Bolhas - {year}", show=False)
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
                fill_color='blue',
                fill_opacity=0.5,
                tooltip=f"{row['name_muni']} ({year}) | Repasse: R$ {row['valor_total']:,.0f} | Risco: {row['area_risco_km2']:.2f} km2"
            ).add_to(fg_bolhas)
        
        fg_bolhas.add_to(m)
        all_years_data.append(pb_year.drop(columns=['geometry_buffer']))

    # CAMADAS FIXAS
    # 1. Escolas
    pb_muni.explore(
        m=m,
        column='num_escolas',
        cmap='Greens',
        name="Infra: Escolas (F)",
        show=False,
        tooltip=['name_muni', 'num_escolas'],
        legend=True,
        legend_kwds=dict(colorbar=False),
        style_kwds=dict(color="black", weight=0.5, fillOpacity=0.6)
    )

    # 2. Rodovias
    if os.path.exists(roads_path):
        roads_pb = gpd.read_file(roads_path)
        roads_pb.explore(
            m=m, color='darkgray', name="Infra: Rodovias (F)", show=False,
            tooltip=['vl_br', 'nm_tipo_tr'], style_kwds=dict(weight=2, opacity=0.8)
        )

    # 3. Áreas de Risco (Polígonos originais)
    if os.path.exists(risk_path):
        risk_pb = gpd.read_file(risk_path)
        risk_pb.explore(
            m=m, color='red', name="Risco: Polígonos (IBGE)", show=False,
            tooltip=['name_muni', 'origem'], style_kwds=dict(fillOpacity=0.5, weight=1)
        )

    # Salvar resultados
    pd.concat(all_years_data).to_file(output_gpkg, driver="GPKG")
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(output_html_unified)
    print(f"Sucesso! Mapa consolidado com áreas de risco salvo em: {output_html_unified}")

if __name__ == "__main__":
    run_spatial_analysis()
