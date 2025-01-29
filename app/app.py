from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/restaurants')
def restaurant_map():
    return render_template('paris_restaurant_satisfaction_map.html')  

@app.route('/hotels')
def hotel_map():
    return render_template('paris_hotel_satisfaction_map.html')  

if __name__ == '__main__':
    app.run(debug=True)
