FROM python:3.10

WORKDIR /app

# Copie les requirements.txt spécifiques au frontend et installe les dépendances
COPY frontend_requirements.txt .
RUN pip install --no-cache-dir -r frontend_requirements.txt

# Copie le reste du code de l'application Flask
COPY . /app

# Commande pour lancer l'application Flask
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]