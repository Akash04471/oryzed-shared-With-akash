#!/usr/bin/env python
"""Minimal test app to check if Flask works"""

print("Starting imports...")
from flask import Flask
print("Flask imported successfully")

app = Flask(__name__)
print("Flask app created successfully")

@app.route("/")
def hello():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    print("App is ready to run on http://0.0.0.0:8080")
    print("Starting server...")
    app.run(host="0.0.0.0", port=8080, debug=True)
