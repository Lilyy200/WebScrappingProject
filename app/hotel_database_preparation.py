import sqlite3
import pandas as pd
import folium
import json
import numpy as np

# Connexion à la base de données SQLite
conn = sqlite3.connect("hotel_paris.db")

# Charger les données de la base SQLite
data = pd.read_sql_query("SELECT district, sentiment_score_textblob, sentiment_label_huggingface, sentiment_score_huggingface, average_rating, top_bigrams FROM establishments", conn)

# Agréger les scores de sentiment, les notes moyennes et les bigrams par arrondissement
aggregated_data = data.groupby("district").agg(
    average_sentiment=('sentiment_score_textblob', 'mean'),
    average_sentiment_huggingface=('sentiment_score_huggingface', 'mean'),
    average_sentiment_label=('sentiment_label_huggingface', lambda x: x.value_counts().index[0]),
    average_rating=('average_rating', 'mean'),
    top_bigrams=('top_bigrams', lambda x: x.iloc[0]),
    restaurant_count=('district', 'count')  # Compte du nombre de restaurants
).reset_index()

# Charger le fichier GeoJSON des arrondissements de Paris
with open("arrondissements.geojson", "r", encoding="utf-8") as f:
    geo_data = json.load(f)

# Normaliser le format des districts dans aggregated_data
aggregated_data['district'] = aggregated_data['district'].str.replace("er", "", regex=False)
aggregated_data['district'] = aggregated_data['district'].str.replace("e", "", regex=False)
aggregated_data['district'] = aggregated_data['district'].astype(int)  # Convertir en entier pour correspondre au GeoJSON

# Création de la carte interactive
map_paris = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

# Ajout des arrondissements colorés par niveau de satisfaction
choropleth = folium.Choropleth(
    geo_data=geo_data,
    data=aggregated_data,
    columns=["district", "average_sentiment_huggingface"],
    key_on="feature.properties.c_ar",  # Correspondance avec les données GeoJSON
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Niveau moyen de satisfaction"
).add_to(map_paris)

# Ajouter des info-bulles pour chaque arrondissement
for feature in geo_data["features"]:
    district_code = int(feature["properties"]["c_ar"])  # Convertir en entier pour correspondre au format dans aggregated_data
    district_name = feature["properties"]["l_ar"]

    # Récupérer les informations pour le district correspondant
    row = aggregated_data.loc[aggregated_data["district"] == district_code]

    if not row.empty:
        sentiment = row["average_sentiment"].values[0]
        sentiment_huggingface = row["average_sentiment_huggingface"].values[0]
        sentiment_label = row["average_sentiment_label"].values[0]
        rating = row["average_rating"].values[0]
        restaurant_count = row["restaurant_count"].values[0]
        bigrams = eval(row["top_bigrams"].values[0])  # Convertir les bigrams de chaîne en liste de tuples
        bigrams_html = "<br>".join([f"{bigram[0]} ({bigram[1]} occurrences)" for bigram in bigrams])
    else:
        sentiment = "Données manquantes"
        sentiment_huggingface = "Données manquantes"
        sentiment_label = "Données manquantes"
        rating = "Données manquantes"
        restaurant_count = 0
        bigrams_html = "Données manquantes"

    # Ajouter le GeoJson avec les styles et les bigrams
    folium.GeoJson(
        feature,
        style_function=lambda x, sentiment=sentiment: {
            "fillColor": "#ffeda0" if sentiment == "Données manquantes" else choropleth.color_scale(sentiment),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.4,
        },
        tooltip=folium.Tooltip(
            f"<b>Arrondissement:</b> {district_name}<br>"
            f"<b>Satisfaction moyenne:</b> {sentiment}<br>"
            f"<b>Satisfaction moyenne Hugging Face:</b> {sentiment_huggingface}<br>"
            f"<b>Label de satisfaction Hugging Face:</b> {sentiment_label}<br>"
            f"<b>Note moyenne des restaurants:</b> {rating}<br>"
            f"<b>Nombre de restaurants:</b> {restaurant_count}<br>"
            f"<b>Bigrams fréquents:</b><br>{bigrams_html}"
        ),
    ).add_to(map_paris)

# Sauvegarder la carte dans un fichier HTML
map_paris.save("paris_hotel_satisfaction_map.html")

print("Carte interactive sauvegardée sous paris_hotel_satisfaction_map.html")

# Fermer la connexion à la base de données
conn.close()
