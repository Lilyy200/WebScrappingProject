import sqlite3
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json

# Connexion à la base de données SQLite
conn = sqlite3.connect("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/tourism_paris.db")

# Charger les données de la base SQLite
data = pd.read_sql_query("SELECT district, sentiment_score FROM establishments", conn)

# Agréger les scores de sentiment par arrondissement
aggregated_data = data.groupby("district")["sentiment_score"].mean().reset_index()
aggregated_data.columns = ["district", "average_sentiment"]
#print(aggregated_data["district"])

# Charger le fichier GeoJSON des arrondissements de Paris
with open("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/arrondissements.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# Vérifier les correspondances entre les districts dans la base et le GeoJSON
geo_districts = [str(feature["properties"]["c_ar"]) + 'e' for feature in geo_data["features"]]  # Conversion en chaîne et ajout d'un 'e'
print("Districts GeoJSON (avec 'e') :", geo_districts)

# Afficher les districts disponibles dans les données agrégées
print("Districts disponibles dans aggregated_data :", aggregated_data["district"].tolist())

# Filtrer les arrondissements présents dans les deux sources
# aggregated_data = aggregated_data[aggregated_data["district"].astype(str).isin(geo_districts)]
# aggregated_data["district"] = aggregated_data["district"].astype(str)
#print(aggregated_data["district"])

# Création de la carte interactive
map_paris = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

# Ajout des arrondissements colorés par niveau de satisfaction
choropleth = folium.Choropleth(
    geo_data=geo_data,
    data=aggregated_data,
    columns=["district", "average_sentiment"],
    key_on="feature.properties.c_ar",  # Correspondance avec les données GeoJSON
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Niveau moyen de satisfaction"
).add_to(map_paris)

# Ajouter des info-bulles pour chaque arrondissement
for feature in geo_data["features"]:
    district_code = geo_districts
    #print(district_code)
    #print(aggregated_data["district"])
    district_name = feature["properties"]["l_ar"]

    print(f"District code dans GeoJSON : {district_code}")
    print(f"Districts disponibles dans aggregated_data : {aggregated_data['district'].tolist()}")

    sentiment = aggregated_data.loc[aggregated_data["district"] == district_code, "average_sentiment"].values
    #print(sentiment)
    sentiment = sentiment[0] if len(sentiment) > 0 else "Données manquantes"
    #print(sentiment)

    folium.GeoJson(
        feature,
        style_function=lambda x, sentiment=sentiment: {
            "fillColor": "#ffeda0" if sentiment == "Données manquantes" else choropleth.color_scale(sentiment),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7,
        },
        tooltip=folium.Tooltip(f"<b>Arrondissement:</b> {district_name}<br><b>Satisfaction moyenne:</b> {sentiment}"),
    ).add_to(map_paris)

# Sauvegarder la carte dans un fichier HTML
map_paris.save("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/paris_satisfaction_map.html")

print("Carte interactive sauvegardée sous paris_satisfaction_map.html")

# Fermer la connexion à la base de données
conn.close()

