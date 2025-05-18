FROM python:3.10

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Commande pour lancer l'app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

