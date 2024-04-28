from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_pymongo import PyMongo, ObjectId
import pandas as pd
import os
from flask_login import current_user
from flask import session
from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo
import plotly.graph_objs as go
from plotly.offline import plot
from werkzeug.security import generate_password_hash
from flask import url_for
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from flask_login import LoginManager, login_user
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from pymongo import MongoClient


app = Flask(__name__)
# app.config["MONGO_URI"] = "mongodb+srv://abhinavsmartkid:wLNjFMvZBfsYd7CU@schekka-final-proj.nfpzzlq.mongodb.net/"

# app.config["MONGO_URI"] = "mongodb+srv://abhinavsmartkid:wLNjFMvZBfsYd7CU@schekka-final-proj.nfpzzlq.mongodb.net/nbashottracker?retryWrites=true&w=majority&appName=schekka-final-proj"

# app.config["MONGO_URI"] = "mongodb+srv://abhinavsmartkid:rooting@schekka-final-proj.nfpzzlq.mongodb.net/"

app.config["MONGO_URI"] = "mongodb+srv://abhinavsmartkid:rooting@schekka-final-proj.nfpzzlq.mongodb.net/nbashottracker?retryWrites=true&w=majority"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'saiabhinav'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


import certifi


# mongo = MongoClient(
#     app.config['MONGO_URI'],
#     tlsCAFile=certifi.where(),
#     tlsAllowInvalidCertificates=True
# )

mongo = PyMongo(app, tls=True, tlsAllowInvalidCertificates=True)

# mongo = PyMongo(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

# Ensure you are in the application context when calling create_all
with app.app_context():
    db.create_all()


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            msg = 'Logged in successfully!'
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        user = User.query.filter_by(username=username).first()
        if user:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)

@app.route('/', methods=['GET', 'POST'])
def index():
    shot_years = [str(year) for year in range(2010, 2018)]  # List of years you have data for shots
    rebound_years = [str(year) for year in range(2013, 2016)]  # List of years you have data for rebounds
    if request.method == 'POST':
        if 'shot_year' in request.form:
            year = request.form['shot_year']
            return redirect(url_for('view_shots', year=year))
        elif 'rebound_year' in request.form:
            season = request.form['rebound_year']
            return redirect(url_for('view_rebounds', season=season))
    return render_template('index.html', shot_years=shot_years, rebound_years=rebound_years)

@app.route('/new_shot/<year>')
def new_shot(year):
    # Render a form to create a new shot entry
    return render_template('new_shot.html', year=year)

@app.route('/new_rebound/<season>')
def new_rebound(season):
    # Render a form to create a new rebound entry
    return render_template('new_rebound.html', season=season)

from flask import session

@app.route('/search', methods=['GET'])
def search():
    # Retrieve search parameters from request or session
    year = request.args.get('year', session.get('search_year'))
    player_name = request.args.get('player_name', session.get('search_player_name'))
    shot_type = request.args.get('shot_type', session.get('search_shot_type'))
    period = request.args.get('period', session.get('search_period'))

    # Store search criteria in the session
    session['search_criteria'] = {
        'year': year,
        'player_name': player_name,
        'shot_type': shot_type,
        'period': period
    }

    query = {}
    if year:
        query['season'] = int(year)
    if player_name:
        query['name'] = {'$regex': player_name, '$options': 'i'}
    if shot_type and shot_type != 'Any':
        query['shot_type'] = shot_type
    if period and period != 'Any':
        query['period'] = int(period)

    collection_name = f'shots_{year}' if year else 'shots'
    shots = mongo.db[collection_name].find(query)

    # When rendering the template, pass the stored search criteria as well
    # so that they can be used in the template if needed.
    return render_template('view_shots.html', shots=list(shots), year=year)



@app.route('/search_rebounds', methods=['GET'])
def search_rebounds():
    season = request.args.get('season')
    rebounder = request.args.get('rebounder')
    reb_type = request.args.get('reb_type')

    query = {}
    if season:
        query['season'] = int(season)
    if rebounder:
        query['rebounder'] = {'$regex': rebounder, '$options': 'i'}
    if reb_type and reb_type != 'Any':
        query['reb_type'] = reb_type

    # Store search criteria in the session
    session['search_criteria'] = {
        'season': season,
        'rebounder': rebounder,
        'reb_type': reb_type
    }

    collection_name = f'reb_{season}' if season else 'rebounds'
    rebounds = mongo.db[collection_name].find(query)
    return render_template('view_rebounds.html', rebounds=list(rebounds), season=season)



@app.route('/view/<year>')
def view_shots(year):
    collection_name = f'shots_{year}'
    shots = mongo.db[collection_name].find()
    return render_template('view_shots.html', shots=list(shots), year=year)



@app.route('/view_rebounds/<season>')
def view_rebounds(season):
    collection_name = f'reb_{season}'
    rebounds = mongo.db[collection_name].find()
    return render_template('view_rebounds.html', rebounds=list(rebounds), season=season)

@app.route('/add/<year>', methods=['POST'])
def add_shot(year):
    shot = {
        "name": request.form.get('name'),
        "team_name": request.form.get('team_name'),
        "game_date": request.form.get('game_date'),
        "season": request.form.get('season'),
        "period": int(request.form.get('period')),
        "minutes_remaining": int(request.form.get('minutes_remaining')),
        "seconds_remaining": int(request.form.get('seconds_remaining')),
        "shot_made_flag": int(request.form.get('shot_made_flag')),
        "action_type": request.form.get('action_type'),
        "shot_type": request.form.get('shot_type'),
        "shot_distance": int(request.form.get('shot_distance')),
        "opponent": request.form.get('opponent'),
        "x": int(request.form.get('x')),
        "y": int(request.form.get('y'))
    }
    collection_name = f'shots_{year}'
    mongo.db[collection_name].insert_one(shot)
    return redirect(url_for('view_shots', year=year))

@app.route('/add_rebound/<season>', methods=['POST'])
def add_rebound(season):
    rebound = {
        "rebounder": request.form.get('rebounder'),
        "player_id": int(request.form.get('player_id')),
        "rebounding_team_name": request.form.get('rebounding_team_name'),
        "matchup": request.form.get('matchup'),
        "game_date": request.form.get('game_date'),
        "season": int(request.form.get('season')),
        "game_id": int(request.form.get('game_id')),
        "period": int(request.form.get('period')),
        "minutes": int(request.form.get('minutes')),
        "seconds": int(request.form.get('seconds')),
        "shot_type": request.form.get('shot_type'),
        "reb_type": request.form.get('reb_type'),
        "shot_dist": float(request.form.get('shot_dist')),
        "reb_dist": float(request.form.get('reb_dist')),
        "num_contested": int(request.form.get('num_contested')),
        "shooter": request.form.get('shooter'),
        "shooter_player_id": int(request.form.get('shooter_player_id'))
    }
    collection_name = f'reb_{season}'
    mongo.db[collection_name].insert_one(rebound)
    return redirect(url_for('view_rebounds', season=season))

@app.route('/edit/<year>/<shot_id>')
def edit_shot(year, shot_id):
    collection_name = f'shots_{year}'
    shot = mongo.db[collection_name].find_one({'_id': ObjectId(shot_id)})
    search_criteria = session.get('search_criteria', {})
    # Pass the search parameters to the template to use in the form action or elsewhere
    return render_template('edit_shot.html', shot=shot, year=year, search_criteria=search_criteria)


@app.route('/edit_rebound/<season>/<rebound_id>')
def edit_rebound(season, rebound_id):
    collection_name = f'reb_{season}'
    rebound = mongo.db[collection_name].find_one({'_id': ObjectId(rebound_id)})
    # Include this when rendering the template
    search_criteria = session.get('search_criteria', {})
    return render_template('edit_rebound.html', rebound=rebound, season=season, search_criteria=search_criteria)

@app.route('/update/<year>/<shot_id>', methods=['POST'])
def update_shot(year, shot_id):
    shot_made_flag = 'shot_made_flag' in request.form
    shot_data = {
        "name": request.form.get('name'),
        "team_name": request.form.get('team_name'),
        "game_date": request.form.get('game_date'),
        "season": request.form.get('season'),
        "period": int(request.form.get('period')),
        "minutes_remaining": int(request.form.get('minutes_remaining')),
        "seconds_remaining": int(request.form.get('seconds_remaining')),
        "shot_made_flag": int(shot_made_flag),
        "action_type": request.form.get('action_type'),
        "shot_type": request.form.get('shot_type'),
        "shot_distance": int(request.form.get('shot_distance')),
        "opponent": request.form.get('opponent'),
        "x": int(request.form.get('x')),
        "y": int(request.form.get('y'))
    }

    # Update the document in MongoDB.
    collection_name = f'shots_{year}'
    mongo.db[collection_name].update_one({'_id': ObjectId(shot_id)}, {'$set': shot_data})

    # Redirect back to the search results using the search criteria from the form or session
    search_criteria = session.get('search_criteria', {})
    return redirect(url_for('search', **search_criteria))


@app.route('/update_rebound/<season>/<rebound_id>', methods=['POST'])
def update_rebound(season, rebound_id):
    # It's important to ensure that each field is appropriately cast to the correct type.
    # The fields 'player_id', 'game_id', 'period', 'minutes', 'seconds', 'num_contested',
    # and 'shooter_player_id' are integers, 'shot_dist' and 'reb_dist' are floats, and the rest are strings.
    rebound_data = {
        "rebounder": request.form.get('rebounder'),
        "player_id": int(request.form.get('player_id')),
        "rebounding_team_name": request.form.get('rebounding_team_name'),
        "matchup": request.form.get('matchup'),
        "game_date": request.form.get('game_date'),
        "season": int(request.form.get('season')),
        "game_id": int(request.form.get('game_id')),
        "period": int(request.form.get('period')),
        "minutes": int(request.form.get('minutes')),
        "seconds": int(request.form.get('seconds')),
        "shot_type": request.form.get('shot_type'),
        "reb_type": request.form.get('reb_type'),
        "shot_dist": float(request.form.get('shot_dist')),
        "reb_dist": float(request.form.get('reb_dist')),
        "num_contested": int(request.form.get('num_contested')),
        "shooter": request.form.get('shooter'),
        "shooter_player_id": int(request.form.get('shooter_player_id'))
    }
    
    # Update the document in MongoDB.
    collection_name = f'reb_{season}'
    mongo.db[collection_name].update_one({'_id': ObjectId(rebound_id)}, {'$set': rebound_data})

    # Redirect back to search results using criteria from session
    search_criteria = session.get('search_criteria', {})
    return redirect(url_for('search_rebounds', **search_criteria))

@app.route('/delete/<year>/<shot_id>')
def delete_shot(year, shot_id):
    collection_name = f'shots_{year}'
    mongo.db[collection_name].delete_one({'_id': ObjectId(shot_id)})
    return redirect(url_for('view_shots', year=year))

@app.route('/delete_rebound/<season>/<rebound_id>')
def delete_rebound(season, rebound_id):
    # Define the collection name based on the season.
    collection_name = f'reb_{season}'
    
    # Delete the specified document using the rebound_id.
    mongo.db[collection_name].delete_one({'_id': ObjectId(rebound_id)})
    
    # Redirect to the view that shows the updated list of rebounds.
    return redirect(url_for('search_rebounds', season=season))


if __name__ == '__main__':
    app.run(debug=True)

