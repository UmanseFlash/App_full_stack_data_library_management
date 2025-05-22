from flask import Flask, render_template, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

# Définir le chemin vers le dossier static
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# Route pour servir le fichier index.html
@app.route("/")
def serve_index():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', today=today)

# Route pour servir les fichiers statiques (CSS, JS)
@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Sert les fichiers statiques (JavaScript, CSS, etc.).
    """
    return send_from_directory(STATIC_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)