import sqlite3
import pandas as pd
from textblob import TextBlob
import re
import os

# Supprimer la base de données existante si elle existe
if os.path.exists("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/tourism_paris.db"):
    os.remove("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/tourism_paris.db")
    print("Base de données existante supprimée.")

# Charger les données à partir du CSV
file_path = "C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/paris_restaurants2.csv"
data = pd.read_csv(file_path)

# Nettoyer les données pour les valeurs manquantes
data['Note moyenne'] = data['Note moyenne'].fillna(data['Note moyenne'].mean())

# Fonction pour nettoyer le texte
def clean_text(text):
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Supprimer la ponctuation
    text = re.sub(r"\s+", " ", text)  # Supprimer les espaces multiples
    return text.strip().lower()

data['Cleaned Reviews'] = data['Reviews'].apply(clean_text)

# Fonction pour analyser le sentiment avec TextBlob
def analyze_sentiment(review):
    blob = TextBlob(review)
    sentiment_score = blob.sentiment.polarity  # Score entre -1 (négatif) et 1 (positif)
    return sentiment_score

data['Sentiment Score'] = data['Cleaned Reviews'].apply(analyze_sentiment)

# Créer une connexion SQLite
conn = sqlite3.connect("C:/Document/Christelle/S9/Webscraping and Applied ML/WebScrappingProject/tourism_paris.db")
cursor = conn.cursor()

# Création de la table avec toutes les colonnes nécessaires
cursor.execute('''
CREATE TABLE IF NOT EXISTS establishments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    review_count INTEGER,
    average_rating REAL,
    reviews TEXT,
    district TEXT,
    cleaned_reviews TEXT,
    sentiment_score REAL
)
''')

# Insérer les données dans la table
for _, row in data.iterrows():
    cursor.execute('''
    INSERT INTO establishments (name, address, latitude, longitude, review_count, average_rating, reviews, district, cleaned_reviews, sentiment_score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row['Nom'],
        row['Adresse'],
        row['Latitude'],
        row['Longitude'],
        row['Nombre d\'avis'],
        row['Note moyenne'],
        row['Reviews'],
        row['Arrondissement'],
        row['Cleaned Reviews'],
        row['Sentiment Score']
    ))

# Sauvegarder les changements et fermer la connexion
conn.commit()

# Vérifier les 5 premières lignes après ajout des sentiments
cursor.execute("SELECT name, address, latitude, longitude, district, average_rating, sentiment_score FROM establishments LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()

print("Analyse NLP terminée et résultats stockés dans la base de données.")


