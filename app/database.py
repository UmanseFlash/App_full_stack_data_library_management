from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings  # Importez les paramètres de configuration

# URL de la base de données
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL # Utilisation de l'URL depuis la configuration

# Création du moteur de la base de données
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
# Création d'une "session locale".
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Définition de la base déclarative.
Base = declarative_base()


# Fonction pour créer les tables dans la base de données
async def create_db_and_tables():
    """
    Crée toutes les tables définies dans les modèles SQLAlchemy.
    Cette fonction doit être appelée au démarrage de l'application.
    """
    # Base.metadata.create_all(engine)  # Ceci est l'ancienne façon synchrone.
    # Utilisation de run_sync pour exécuter l'opération synchrone dans un contexte asynchrone
    from sqlalchemy.ext.asyncio import AsyncEngine
    if isinstance(engine, AsyncEngine):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        Base.metadata.create_all(engine)


# Fonction pour obtenir une session de base de données
async def get_db():
    """
    Générateur qui fournit une session de base de données à chaque requête.
    La session est fermée automatiquement après la fin de la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()