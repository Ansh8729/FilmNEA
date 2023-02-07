import sqlite3
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def form():
    return render_template('index.html')

@app.route("/movies")
def ant_man():
    return render_template('movies.html')

@app.route("/tv")
def tlou():
    return render_template('tv.html')


