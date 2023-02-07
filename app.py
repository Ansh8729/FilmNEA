import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Harihar Rengan for Head of CS Soc<p>"

@app.route("/movies")
def ant_man():
    return render_template('movies.html')

@app.route("/tv")
def tlou():
    return render_template('tv.html')
