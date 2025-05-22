from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings
import time
import logging

logger = logging.getLogger(__name__)

# URL de la base de données
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Création du moteur de la base de données
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)
# Création d'une "session locale".
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Définition de la base déclarative.
Base = declarative_base()


async def create_db_and_tables(retries: int = 10, delay_seconds: int = 5):
    """
    Crée toutes les tables définies dans les modèles SQLAlchemy.
    Cette fonction est appelée au démarrage de l'application.
    Inclut une logique de re-tentative pour la connexion à la base de données
    et la création des tables.
    """
    # Importez les modèles ici pour vous assurer qu'ils sont chargés et enregistrés
    # avec Base.metadata avant d'appeler create_all.
    # C'est une bonne pratique pour éviter les problèmes d'ordre d'importation.
    from app import models # Ceci assure que les modèles sont enregistrés

    for i in range(retries):
        try:
            logger.info(f"Tentative {i+1}/{retries} de création des tables de la base de données...")
            # La méthode create_all est synchrone, mais elle sera exécutée dans le contexte
            # asynchrone de l'événement de démarrage de FastAPI.
            Base.metadata.create_all(engine)
            logger.info("Tables de la base de données créées avec succès.")
            return # Sortir de la boucle si la création réussit
        except Exception as e:
            logger.warning(f"Erreur lors de la création des tables: {e}. Re-tentative dans {delay_seconds} secondes...")
            time.sleep(delay_seconds) # Attendre avant la prochaine tentative
    
    logger.error("Échec de la création des tables de la base de données après plusieurs tentatives.")
    raise Exception("Impossible de se connecter à la base de données ou de créer les tables.")


# Fonction pour obtenir une session de base de données (reste inchangée)
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
