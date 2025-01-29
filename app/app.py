from flask import Flask, render_template, jsonify, request
import sqlite3

app = Flask(__name__)

# Route de base qui affiche la carte
@app.route('/')
def index():
    return render_template('index.html')  # Changez de index.html à map.html

# Route pour les restaurants
@app.route('/restaurants')
def restaurant_map():
    return render_template('paris_restaurant_satisfaction_map.html')  

# Route pour les hôtels
@app.route('/hotels')
def hotel_map():
    return render_template('paris_hotel_satisfaction_map.html')  

# Route pour la description dynamique
@app.route('/description')
def description():
    return render_template('description.html')

# Nouveau endpoint d’API pour récupérer la description
@app.route('/api/description/<int:arrondissement>')
def api_description(arrondissement):
    """
    Récupère la description de l’arrondissement depuis la base,
    et retourne un JSON.
    """
    conn = sqlite3.connect("app/description_arr.db")
    cursor = conn.cursor()

    cursor.execute("SELECT description FROM descriptionarr WHERE arrondissement = ?", (arrondissement,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"arrondissement": arrondissement, "description": row[0]})
    else:
        return jsonify({"arrondissement": arrondissement, "description": "Aucune description trouvée."})

@app.route('/recommandations')
def get_recommendations():
    district = request.args.get('district', '').strip()
    
    if not district:
        print("⚠️ Aucun district reçu !")  # Ajout de logs
        return jsonify([])  # Retourne une liste vide si aucun district

    print(f"Requête reçue pour district: {district}")  # Log

    conn = sqlite3.connect("app/recommandation_paris.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, address, category, price, description FROM recommandation WHERE district = ?", (district,))
    results = cursor.fetchall()
    conn.close()

    recommendations = [{
        "name": row[0],
        "address": row[1],
        "category": row[2],
        "price": row[3],
        "description": row[4]
    } for row in results]

    print(f"Résultats trouvés ({len(recommendations)}): {recommendations}")  # Vérifier les résultats

    return jsonify(recommendations)


if __name__ == '__main__':
    app.run(debug=True)
