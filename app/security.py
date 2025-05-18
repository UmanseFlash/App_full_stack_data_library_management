from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.core.config import settings

# Configuration de Passlib pour la gestion des mots de passe
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# Configuration de OAuth2 pour l'authentification et l'autorisation
# Le tokenUrl est l'endpoint que le client utilisera pour obtenir un token d'accès.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



# Fonction pour vérifier le mot de passe
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie si le mot de passe en clair correspond au hachage stocké.

    Args:
        plain_password (str): Le mot de passe en clair à vérifier.
        hashed_password (str): Le hachage du mot de passe stocké.

    Returns:
        bool: True si le mot de passe correspond, False sinon.
    """
    return pwd_context.verify(plain_password, hashed_password)


# Fonction pour obtenir le hachage d'un mot de passe
def get_password_hash(password: str) -> str:
    """
    Hashe le mot de passe en clair à l'aide de Passlib.

    Args:
        password (str): Le mot de passe en clair à hasher.

    Returns:
        str: Le hachage du mot de passe.
    """
    return pwd_context.hash(password)


# Fonction pour créer un token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT pour un utilisateur.

    Args:
        data (dict): Les données à inclure dans le token (par exemple, l'ID de l'utilisateur).
        expires_delta (Optional[timedelta]): La durée de validité du token.
            Si None, utilise la valeur par défaut configurée.

    Returns:
        str: Le token JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


# Fonction pour décoder un token JWT
def decode_access_token(token: str) -> dict:
    """
    Décode un token JWT et retourne son payload.

    Args:
        token (str): Le token JWT à décoder.

    Returns:
        dict: Le payload du token.

    Raises:
        HTTPException: Si le token est invalide ou a expiré.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )  # Utilise la clé secrète et l'algorithme depuis la configuration
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )



# Fonction pour obtenir l'utilisateur actuel à partir du token
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    """
    Obtient l'utilisateur actuel à partir du token JWT fourni dans l'en-tête Authorization.

    Args:
        token (str, optional): Le token JWT.  Dépend de oauth2_scheme pour l'obtenir
                                depuis l'en-tête de la requête.
        db (Session, optional): La session de base de données.  Dépend de get_db pour l'obtenir.

    Returns:
        models.User: L'objet utilisateur correspondant au token.

    Raises:
        HTTPException: Si le token est invalide, a expiré, ou si l'utilisateur n'existe pas.
    """
    payload = decode_access_token(token)  # Décode le token
    username: str = payload.get("sub")  # Récupère le nom d'utilisateur du payload
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = (
        db.query(models.User).filter(models.User.username == username).first()
    )  # Récupère l'utilisateur depuis la base de données
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user



# Fonction pour obtenir l'utilisateur actuel avec les droits d'administrateur
async def get_current_admin_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """
    Obtient l'utilisateur actuel et vérifie s'il a le rôle d'administrateur.

    Args:
        current_user (models.User, optional): L'utilisateur actuel, obtenu via get_current_user.

    Returns:
        models.User: L'objet utilisateur si l'utilisateur est un administrateur.

    Raises:
        HTTPException: Si l'utilisateur n'est pas un administrateur.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current_user