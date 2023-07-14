from flask import Flask


app = Flask("sports_book_rest_api")

# Load config to app
app.config.from_pyfile("src/config/config.py")

@app.route("/", methods=["GET", "OPTIONS"])
def root_uri():
    return "Hello World"