import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import books, members, loans, auth
#from app.routers import books, members, loans, auth
from app.database import create_db_and_tables
from app.core.exceptions import CustomException
from app.core.config import settings
from fastapi.responses import JSONResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bibliothèque API",
    description="API pour la gestion d'une bibliothèque",
    version="0.1.0",
    # Désactivez la documentation interactive en production
    docs_url=None if settings.ENV == "production" else "/docs",
    redoc_url=None if settings.ENV == "production" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Gestionnaire d'événements pour la startup de l'application
@app.on_event("startup")
async def on_startup():
    """
    Fonction appelée au démarrage de l'application.
    Crée les tables de la base de données.
    """
    await create_db_and_tables()
    logger.info("Application démarrée et tables de la base de données créées.")



# Gestionnaire d'erreurs global pour les exceptions HTTP de Starlette
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    Gestionnaire d'erreurs pour les exceptions HTTP standard (comme 404, etc.).
    Retourne une réponse JSON avec le code d'erreur et le message.
    """
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        {"detail": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code,
    )


# Gestionnaire d'erreurs global pour les exceptions de validation de Pydantic
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Gestionnaire d'erreurs pour les erreurs de validation des données (Pydantic).
    Retourne une réponse JSON avec les détails de l'erreur.
    """
    logger.error(f"Validation Error: {exc}")
    return JSONResponse(
        {"detail": exc.errors(), "status_code": 422}, status_code=422
    )

# Gestionnaire d'erreurs global pour les exceptions personnalisées de l'application
@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc):
    """
    Gestionnaire d'erreurs pour les exceptions personnalisées de l'application.
    Retourne une réponse JSON avec le code d'erreur et le message.
    """
    logger.error(f"Custom Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        {"detail": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code,
    )



# Inclure les routeurs (endpoints) de l'API
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(books.router, prefix="/books", tags=["Livres"])
app.include_router(members.router, prefix="/members", tags=["Membres"])
app.include_router(loans.router, prefix="/loans", tags=["Emprunts"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )