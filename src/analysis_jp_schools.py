import geobr
import geopandas as gpd
import os
import folium

def analyze_jp_schools():
    code_jp = 2507507  # João Pessoa
    output_html = "reports/maps/mapa_joao_pessoa_escolas.html"
    schools_path = "data/raw/escolas_pb.gpkg"
    
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    
    print("Baixando setores censitários de João Pessoa (IBGE 2010)...")
    try:
        tracts = geobr.read_census_tract(code_tract=code_jp, year=2010)
    except Exception as e:
        print(f"Erro ao baixar setores: {e}")
        return

    print("Carregando escolas e rodovias...")
    roads_path = "data/raw/rodovias_pb.gpkg"
    if os.path.exists(schools_path) and os.path.exists(roads_path):
        schools = gpd.read_file(schools_path).to_crs("EPSG:5880")
        roads = gpd.read_file(roads_path).to_crs("EPSG:5880")
        tracts = tracts.to_crs("EPSG:5880")
    else:
        print("Erro: Arquivos de escolas ou rodovias não encontrados.")
        return

    print("Calculando distância das escolas à rodovia mais próxima...")
    schools_with_dist = gpd.sjoin_nearest(schools, roads[['geometry']], distance_col="dist_rodovia", how="left")
    schools_with_dist = schools_with_dist.drop(columns=['index_right'], errors='ignore')
    
    def format_school_name(row):
        dist = row['dist_rodovia']
        if dist < 1000:
            return f"{row['name_school']} ({dist:.0f}m)"
        else:
            return f"{row['name_school']} ({dist/1000:.1f}km)"
            
    schools_with_dist['name_with_dist'] = schools_with_dist.apply(format_school_name, axis=1)

    print("Realizando join espacial (Escolas em Setores Censitários)...")
    schools_in_tracts = gpd.sjoin(schools_with_dist, tracts[['code_tract', 'geometry']], how='inner', predicate='within')
    
    tract_stats = schools_in_tracts.groupby('code_tract').agg({
        'name_with_dist': [lambda x: "<br>".join(sorted(x.unique().tolist())), 'count']
    }).reset_index()
    tract_stats.columns = ['code_tract', 'lista_escolas', 'num_escolas']
    
    tracts = tracts.to_crs("EPSG:4326")
    tracts = tracts.merge(tract_stats, on='code_tract', how='left')
    tracts['num_escolas'] = tracts['num_escolas'].fillna(0).astype(int)
    tracts['lista_escolas'] = tracts['lista_escolas'].fillna('Nenhuma escola encontrada.')
    
    print(f"Gerando mapa interativo em: {output_html}")
    m = tracts.explore(
        column='num_escolas',
        cmap='Blues',
        name="Escolas por Setor",
        tooltip=['code_tract', 'num_escolas'],
        popup=['num_escolas', 'lista_escolas'],
        legend=True,
        legend_kwds=dict(colorbar=False),
        style_kwds=dict(color="black", weight=0.3, fillOpacity=0.7)
    )

    top10_closest = schools_in_tracts.nsmallest(10, 'dist_rodovia')
    top10_furthest = schools_in_tracts.nlargest(10, 'dist_rodovia')
    
    def get_list_html(df, title):
        html = f"<b>{title}</b><br><ul style='margin: 5px; padding-left: 15px; font-size: 11px;'>"
        for _, row in df.iterrows():
            dist_str = f"{row['dist_rodovia']:.0f}m" if row['dist_rodovia'] < 1000 else f"{row['dist_rodovia']/1000:.1f}km"
            html += f"<li><a href='#' onclick='highlightTract(\"{row['code_tract']}\"); return false;' style='color:inherit; text-decoration:none; cursor:pointer;'>{row['name_school']} ({dist_str})</a></li>"
        html += "</ul>"
        return html

    closest_html = get_list_html(top10_closest, "Top 10 Mais Próximas")
    furthest_html = get_list_html(top10_furthest, "Top 10 Mais Distantes")

    # Injetar HTML e JAVASCRIPT usando replace() para não conflitar com {}
    ranking_template = """
    <div style="
        position: fixed; bottom: 30px; left: 30px; width: 320px; height: auto; 
        background-color: white; border:2px solid #ccc; z-index:9999; font-size:13px;
        padding: 12px; opacity: 0.95; border-radius: 8px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        overflow-y: auto; max-height: 500px;
    ">
        <h4 style="margin: 0 0 10px 0; color: #333; border-bottom: 1px solid #ddd;">Localizador de Escolas</h4>
        <details open>
            <summary style="cursor:pointer; font-weight:bold; color:blue">Top 10 Mais Próximas</summary>
            [[closest_list]]
        </details>
        <details style="margin-top:10px">
            <summary style="cursor:pointer; font-weight:bold; color:red">Top 10 Mais Distantes</summary>
            [[furthest_list]]
        </details>
        <p style="font-size: 10px; color: #666; margin-top: 10px;">* Clique no nome para destacar o setor no mapa.</p>
    </div>
    
    <script>
        var lastLayer = null;
        function highlightTract(tractId) {
            var map = null;
            for (var key in window) {
                if (window[key] instanceof L.Map) { map = window[key]; break; }
            }
            if (!map) return;

            map.eachLayer(function(layer) {
                if (layer.feature && layer.feature.properties && layer.feature.properties.code_tract == tractId) {
                    if (lastLayer) {
                        lastLayer.setStyle({ color: 'black', weight: 0.3, fillOpacity: 0.7 });
                    }
                    map.fitBounds(layer.getBounds(), { padding: [50, 50] });
                    
                    var count = 0;
                    var interval = setInterval(function() {
                        layer.setStyle({ color: count % 2 == 0 ? 'red' : 'yellow', weight: 8, fillOpacity: 0.9 });
                        if (++count > 10) {
                            clearInterval(interval);
                            layer.setStyle({ color: 'red', weight: 5, fillOpacity: 0.8 });
                        }
                    }, 200);
                    
                    layer.openTooltip();
                    lastLayer = layer;
                }
            });
        }
    </script>
    """
    ranking_panel = ranking_template.replace("[[closest_list]]", closest_html).replace("[[furthest_list]]", furthest_html)
    
    m.get_root().html.add_child(folium.Element(ranking_panel))
    folium.LayerControl(collapsed=False).add_to(m)
    m.save(output_html)
    print("Sucesso!")

if __name__ == "__main__":
    analyze_jp_schools()
