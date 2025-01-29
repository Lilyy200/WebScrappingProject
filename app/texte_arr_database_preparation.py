import sqlite3
import pandas as pd
import folium
import json
import os

# Connexion à la base de données SQLite
conn = sqlite3.connect("app/description_arr.db")
data = pd.read_sql_query("SELECT arrondissement, description FROM descriptionarr", conn)

# Charger le fichier GeoJSON des arrondissements de Paris
with open("app/arrondissements.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# Convertir les arrondissements en entier
data['arrondissement'] = data['arrondissement'].str.replace("st", "", regex=False)
data['arrondissement'] = data['arrondissement'].str.replace("nd", "", regex=False)
data['arrondissement'] = data['arrondissement'].str.replace("rd", "", regex=False)
data['arrondissement'] = data['arrondissement'].str.replace("th", "", regex=False)
data['arrondissement'] = data['arrondissement'].astype(int)  # s'assurer que c'est int

# Création de la carte interactive
map_paris = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

# Fonction de style
def style_function(feature):
    return {
        "fillColor": "#74c476", 
        "color": "black",
        "weight": 1,
        "fillOpacity": 0.4,
    }

# Ajouter des info-bulles pour chaque arrondissement
for feature in geo_data["features"]:
    district_code = str(feature["properties"]["c_ar"]) + " Ardt"  # Convert to string and match the format in aggregated_data
    district_name = feature["properties"]["l_ar"]

    # Récupérer les informations pour le district correspondant
    row = data.loc[data["arrondissement"] == int(feature["properties"]["c_ar"])]

    if not row.empty:
        description = row["description"].values[0]
    else:
        description = "Description non trouvée"

    # Ajouter le GeoJson avec les styles et les info-bulles
    folium.GeoJson(
        feature,
        style_function=style_function,
        tooltip=folium.Tooltip(
            f"<b>Arrondissement:</b> {district_name}<br>"
            f"<a href='/description/{district_code}'>Voir la description</a>"
        ),
    ).add_to(map_paris)

# Sauvegarder la carte dans un fichier HTML
map_paris.save("app/templates/map.html")
print("Carte sauvegardée dans 'app/templates/map.html'.")