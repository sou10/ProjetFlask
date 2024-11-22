from flask import Flask, render_template, redirect, url_for, request, session, jsonify, flash
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_session import Session
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from bson import ObjectId
from flask import render_template, request, redirect, url_for





# Charger les variables d'environnement
load_dotenv()

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration via variables d'environnement ou fichier config.py
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/cinema')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # Ajout d'une clé secrète sécurisée
app.config['SESSION_TYPE'] = 'filesystem'

# Initialisation des extensions
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
Session(app)

# Route d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        if not username or not password:
            flash('Veuillez remplir tous les champs', 'danger')
            return redirect(url_for('register'))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        user_collection = mongo.db.users
        if user_collection.find_one({'username': username}):
            flash('Nom d\'utilisateur déjà pris', 'danger')
            return redirect(url_for('register'))

        user_collection.insert_one({'username': username, 'password': hashed_pw})
        flash('Inscription réussie, vous pouvez vous connecter', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        user_collection = mongo.db.users
        user = user_collection.find_one({'username': username})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = username
            flash('Connexion réussie', 'success')
            return redirect(url_for('tickets'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('index'))

# Afficher les tickets
@app.route('/tickets')
def tickets():
    if 'username' in session:
        tickets_collection = mongo.db.tickets
        tickets = list(tickets_collection.find())
        return render_template('tickets.html', tickets=tickets)
    else:
        flash('Veuillez vous connecter pour voir les tickets', 'warning')
        return redirect(url_for('login'))

# API pour récupérer les tickets (ex: en JSON)
@app.route('/api/tickets', methods=['GET'])
def api_tickets():
    tickets_collection = mongo.db.tickets
    tickets = list(tickets_collection.find())
    ticket_list = [{'id': str(ticket['_id']), 'title': ticket['title'], 'price': ticket['price']} for ticket in tickets]
    return jsonify(ticket_list)

# Acheter un ticket
# Assuming you're using MongoDB and have a function to get ticket data
def get_ticket_by_id(ticket_id):
    # Replace with actual MongoDB query logic
    if ObjectId.is_valid(ticket_id):
        ticket = mongo.db.tickets.find_one({"_id": ObjectId(ticket_id)})
        return ticket
    return None

@app.route('/buy_ticket/<ticket_id>', methods=['GET', 'POST'])
def buy_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    
    if ticket is None:
        return render_template('404.html')

    if request.method == 'POST':
        try:
            quantity = int(request.form['quantity'])
            if quantity < 1 or quantity > 10:
                raise ValueError("Invalid quantity")
        except (ValueError, KeyError) as e:
            return f"Error in form data: {e}", 400

        total_price = ticket['price'] * quantity

        # Redirect to the purchase confirmation page
        return redirect(url_for('purchase_confirmation', ticket_id=ticket_id, quantity=quantity, total_price=total_price))

    return render_template('buy_ticket.html', ticket=ticket)

@app.route('/purchase_confirmation/<ticket_id>/<quantity>/<total_price>')
def purchase_confirmation(ticket_id, quantity, total_price):
    ticket = get_ticket_by_id(ticket_id)  # Fetch the ticket details by its ID
    if ticket is None:
        return render_template('404.html')  # Render a 404 page if ticket not found

    # Convert quantity and total_price to integers, if necessary
    quantity = int(quantity)
    total_price = float(total_price)

    # Pass the ticket and purchase details to the template
    return render_template('purchase_confirmation.html', ticket=ticket, quantity=quantity, total_price=total_price)

if __name__ == '__main__':
    # Permet d'exécuter l'application en mode debug uniquement en local
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug_mode)
