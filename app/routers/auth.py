from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import (
    verify_password,
    create_access_token,
    get_password_hash,
    get_current_user
)
from datetime import timedelta
from app.core.config import settings
from datetime import date
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Endpoint pour l'inscription d'un nouvel utilisateur
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Enregistre un nouvel utilisateur dans la base de données.

    Args:
        user (schemas.UserCreate): Les données de l'utilisateur à enregistrer.
        db (Session, optional): La session de base de données.

    Returns:
        schemas.User: L'utilisateur nouvellement créé.

    Raises:
        HTTPException: Si le nom d'utilisateur ou l'email est déjà pris.
    """
    # Vérifie si le nom d'utilisateur est déjà utilisé
    db_user_by_username = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Vérifie si l'email est déjà utilisé
    db_user_by_email = (
        db.query(models.User).filter(models.User.email == user.email).first()
    )
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash le mot de passe avant de l'enregistrer
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        created_at=date.today(),  # Utilisez la date actuelle
        role="member" #Rôle par défaut
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User registered: {db_user.username}")
    return db_user



# Endpoint pour la connexion d'un utilisateur et l'obtention d'un token JWT
@router.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Connecte un utilisateur et retourne un token JWT.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Les données du formulaire de connexion
            (nom d'utilisateur et mot de passe).
        db (Session, optional): La session de base de données.

    Returns:
        dict: Un dictionnaire contenant le token d'accès et le type de token.

    Raises:
        HTTPException: Si les informations d'identification sont invalides.
    """
    # Vérifie si l'utilisateur existe
    user = (
        db.query(models.User).filter(models.User.username == form_data.username).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Vérifie si le mot de passe est correct
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Crée le token JWT
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    user.last_login = date.today()
    db.commit()
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


# Endpoint pour récupérer les informations de l'utilisateur actuel
@router.get("/me", response_model=schemas.User)
async def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Retourne les informations de l'utilisateur actuellement authentifié.

    Args:
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_user.

    Returns:
        schemas.User: Les informations de l'utilisateur actuel.
    """
    logger.info(f"User profile accessed: {current_user.username}")
    return current_user