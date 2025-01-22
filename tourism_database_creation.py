import sqlite3
import pandas as pd
from textblob import TextBlob
import re
import os
from transformers import pipeline
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import nltk

# Télécharger les stopwords si nécessaire
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Supprimer la base de données existante si elle existe
if os.path.exists("tourism_paris.db"):
    os.remove("tourism_paris.db")
    print("Base de données existante supprimée.")

# Charger les données à partir du CSV
file_path = "paris_restaurants2.csv"
data = pd.read_csv(file_path)

# Nettoyer les données pour les valeurs manquantes
data['Note moyenne'] = data['Note moyenne'].fillna(data['Note moyenne'].mean())

# Fonction pour nettoyer le texte
def clean_text(text):
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Supprimer la ponctuation
    text = re.sub(r"\s+", " ", text)  # Supprimer les espaces multiples
    return text.strip().lower()

data['Cleaned Reviews'] = data['Reviews'].apply(clean_text)

# Fonction pour supprimer les stopwords
def remove_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return " ".join(filtered_words)

data['Processed Reviews'] = data['Cleaned Reviews'].apply(remove_stopwords)

# Fonction pour analyser le sentiment avec TextBlob
def analyze_sentiment_textblob(review):
    blob = TextBlob(review)
    sentiment_score = blob.sentiment.polarity  # Score entre -1 (négatif) et 1 (positif)
    return sentiment_score

data['Sentiment Score TextBlob'] = data['Cleaned Reviews'].apply(analyze_sentiment_textblob)

# Initialiser le pipeline Hugging Face pour l'analyse des sentiments
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Fonction pour analyser le sentiment avec Hugging Face
def analyze_sentiment_huggingface(review):
    if not review.strip():
        return None  # Retourne None si la revue est vide
    result = sentiment_pipeline(review[:512])[0]  # Truncate to 512 tokens if necessary
    sentiment = result['label']
    score = result['score']
    return sentiment, score

# Ajouter les colonnes pour les résultats de Hugging Face
data[['Sentiment Label HuggingFace', 'Sentiment Score HuggingFace']] = data['Reviews'].apply(
    lambda review: pd.Series(analyze_sentiment_huggingface(review))
)

# Fonction pour extraire les bigrams les plus fréquents
def extract_top_bigrams(reviews, n=2):
    vectorizer = CountVectorizer(ngram_range=(2, 2))
    X = vectorizer.fit_transform(reviews)
    bigrams = vectorizer.get_feature_names_out()
    counts = X.sum(axis=0).A1
    bigram_counts = Counter(dict(zip(bigrams, counts)))
    return bigram_counts.most_common(n)

# Ajouter les deux bigrams les plus fréquents par arrondissement
bigrams_by_district = (
    data.groupby('Arrondissement')['Processed Reviews']
    .apply(lambda reviews: extract_top_bigrams(reviews.dropna().tolist()))
    .to_dict()
)
data['Top Bigrams'] = data['Arrondissement'].map(bigrams_by_district)

# Créer une connexion SQLite
conn = sqlite3.connect("tourism_paris.db")
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
    processed_reviews TEXT,
    sentiment_score_textblob REAL,
    sentiment_label_huggingface TEXT,
    sentiment_score_huggingface REAL,
    top_bigrams TEXT
)
''')

# Insérer les données dans la table
for _, row in data.iterrows():
    cursor.execute('''
    INSERT INTO establishments (name, address, latitude, longitude, review_count, average_rating, reviews, district, cleaned_reviews, processed_reviews, sentiment_score_textblob, sentiment_label_huggingface, sentiment_score_huggingface, top_bigrams)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        row['Processed Reviews'],
        row['Sentiment Score TextBlob'],
        row['Sentiment Label HuggingFace'],
        row['Sentiment Score HuggingFace'],
        str(row['Top Bigrams'])
    ))

# Sauvegarder les changements et fermer la connexion
conn.commit()

# Vérifier les 5 premières lignes après ajout des sentiments
cursor.execute("SELECT name, address, latitude, longitude, district, average_rating, sentiment_label_huggingface, sentiment_score_huggingface, top_bigrams FROM establishments LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()

print("Analyse NLP terminée avec TextBlob, Hugging Face et extraction des bigrams. Résultats stockés dans la base de données.")
