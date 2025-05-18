from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Configuration de l'application.  Les paramètres sont chargés depuis l'environnement.
    """
    ENV: str = "development"  # Environnement de l'application (development, production, testing)
    DEBUG: bool = True  # Mode débogage
    PROJECT_NAME: str = "Bibliothèque API"  # Nom du projet
    VERSION: str = "0.1.0"  # Version de l'API
    # Base URL de l'application, utilisé pour générer des URLs absolues
    BASE_URL: str = "http://localhost:8000"
    # Configuration de la base de données
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: Optional[str] = "password"  # À définir via une variable d'environnement en production
    DB_NAME: str = "library_db"
    # Construction de l'URL de la base de données
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # Clé secrète pour l'encodage et le décodage des tokens JWT
    JWT_SECRET_KEY: str = "secret"  # À changer en production
    JWT_ALGORITHM: str = "HS256"  # Algorithme utilisé pour l'encodage JWT
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # Durée de validité des tokens (7 jours par défaut)

    class Config:
        # Indique à Pydantic de charger les variables d'environnement
        # et de les mapper aux attributs de la classe Settings.
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Préfixe pour les variables d'environnement
        # Toutes les variables d'environnement doivent commencer par ce préfixe
        # pour être prises en compte.
        env_prefix = "APP_"

# Instance unique de la classe Settings, utilisée pour accéder aux paramètres
settings = Settings()