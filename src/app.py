from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from src.config import config

app = Flask("sports_book_rest_api")

# Load config to app
app.config.from_pyfile("src/config/config.py")

db = SQLAlchemy(app)

@app.route("/", methods=["GET", "OPTIONS"])
def root_uri():
    return "Hello World"