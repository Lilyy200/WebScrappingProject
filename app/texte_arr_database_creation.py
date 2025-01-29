import sqlite3
import pandas as pd
import os


# Supprimer la base de données existante si elle existe
if os.path.exists("app\description_arr.db"):
    os.remove("app\description_arr.db")
    print("Base de données existante supprimée.")

# Charger les données à partir du CSV
file_path = "app/data/beautifulsoup/arrondissements_paris.csv"
data = pd.read_csv(file_path)



# Créer une connexion SQLite
conn = sqlite3.connect("app\description_arr.db")
cursor = conn.cursor()

# Création de la table avec toutes les colonnes nécessaires
cursor.execute('''
CREATE TABLE IF NOT EXISTS descriptionarr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arrondissement TEXT,
    description TEXT
)
''')

# Insérer les données dans la table
for _, row in data.iterrows():
    cursor.execute('''
    INSERT INTO descriptionarr (arrondissement, description)
    VALUES (?, ?)
    ''', (
        row['Arrondissement'],
        row['Texte']
    ))

# Sauvegarder les changements et fermer la connexion
conn.commit()

# Vérifier les 5 premières lignes après ajout des sentiments
cursor.execute("SELECT arrondissement, description FROM descriptionarr LIMIT 2")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()

print("Résultats stockés dans la base de données.")
