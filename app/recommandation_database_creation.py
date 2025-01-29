import sqlite3
import pandas as pd
import os
import json
import re

# Supprimer la base de données existante si elle existe
if os.path.exists("app/recommandation_paris.db"):
    os.remove("app/recommandation_paris.db")
    print("Base de données existante supprimée.")

# Charger les données à partir du fichier JSON
file_path = "app/data/beautifulsoup/wikivoyage_paris_eat_sleep.json"
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Transformer les données JSON en une liste de dictionnaires
records = []
price_pattern = re.compile(r'€[\d,.]+')
updated_pattern = re.compile(r'\(updated .*?\)')

for district, categories in data.items():
    for category, entries in categories.items():
        places = entries.split("\n")
        for place in places:
            try:
                # Extraire latitude et longitude
                lat_long_match = re.search(r'([-+]?[0-9]*\.?[0-9]+)[, ]*([-+]?[0-9]*\.?[0-9]+)', place)
                latitude = float(lat_long_match.group(1)) if lat_long_match else None
                longitude = float(lat_long_match.group(2)) if lat_long_match else None
                
                # Nettoyage du texte après les coordonnées
                clean_text = place.replace(lat_long_match.group(0), "", 1).strip() if lat_long_match else place.strip()
                
                # Suppression des indications "(updated May 2022)" etc.
                clean_text = updated_pattern.sub("", clean_text).strip()
                
                # Extraction du nom et de l'adresse
                parts = clean_text.split(',')
                name = parts[0].strip() if len(parts) > 0 else "Nom inconnu"
                address = ', '.join(parts[1:]).strip() if len(parts) > 1 else "Adresse non spécifiée"
                
                # Extraction du prix
                price_match = price_pattern.findall(place)
                price = ', '.join(price_match) if price_match else "Prix non spécifié"
                
                # Nettoyage de la description pour éviter la répétition
                used_text = f"{name},{address},{price}"
                description = clean_text.replace(used_text, '').strip()
                description = description if description and description != name else "Description indisponible"
                
                records.append({
                    "name": name,
                    "address": address,
                    "latitude": latitude,
                    "longitude": longitude,
                    "district": district,
                    "category": category,
                    "price": price,
                    "description": description
                })
            except Exception as e:
                print(f"Erreur lors du traitement : {place} - {e}")

# Créer une connexion SQLite
conn = sqlite3.connect("app/recommandation_paris.db")
cursor = conn.cursor()

# Création de la table
cursor.execute('''
CREATE TABLE IF NOT EXISTS recommandation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    district TEXT,
    category TEXT,
    price TEXT,
    description TEXT
)
''')

# Insérer les données dans la table
for record in records:
    cursor.execute('''
    INSERT INTO recommandation (name, address, latitude, longitude, district, category, price, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record["name"],
        record["address"],
        record["latitude"],
        record["longitude"],
        record["district"],
        record["category"],
        record["price"],
        record["description"]
    ))

# Sauvegarder les changements et fermer la connexion
conn.commit()

# Vérifier les 5 premières lignes après ajout
cursor.execute("SELECT * FROM recommandation LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()

print("Données insérées dans la base de données avec succès.")