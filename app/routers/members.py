from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user
from datetime import date
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Endpoint pour créer un nouveau membre (accessible uniquement aux administrateurs)
@router.post("/", response_model=schemas.Member, status_code=status.HTTP_201_CREATED)
async def create_member(
    member: schemas.MemberCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Crée un nouveau membre dans la base de données. Accessible uniquement aux administrateurs.

    Args:
        member (schemas.MemberCreate): Les données du membre à créer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        schemas.Member: Le membre nouvellement créé.

    Raises:
        HTTPException: Si le numéro de membre ou l'email est déjà utilisé.
    """
    # Vérifie si le numéro de membre est déjà utilisé
    db_member_by_membership_number = (
        db.query(models.Member)
        .filter(models.Member.membership_number == member.membership_number)
        .first()
    )
    if db_member_by_membership_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Membership number already taken",
        )

    # Vérifie si l'email est déjà utilisé
    db_member_by_email = (
        db.query(models.Member).filter(models.Member.email == member.email).first()
    )
    if db_member_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    # verifier si l'user_id existe
    user = db.query(models.User).filter(models.User.id == member.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Crée le nouveau membre
    db_member = models.Member(
        membership_number=member.membership_number,
        first_name=member.first_name,
        last_name=member.last_name,
        email=member.email,
        phone_number=member.phone_number,
        address=member.address,
        join_date=member.join_date,
        user_id=member.user_id,
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    logger.info(f"Member created: {db_member.first_name} {db_member.last_name} (ID: {db_member.id})")
    return db_member



# Endpoint pour récupérer tous les membres avec pagination, filtrage et tri
@router.get("/", response_model=List[schemas.Member])
async def get_members(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    first_name: Optional[str] = Query(None),
    last_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, regex="^(first_name|last_name|join_date)$"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère tous les membres de la base de données, avec pagination, filtrage et tri.

    Args:
        db (Session, optional): La session de base de données.
        skip (int, optional): Le nombre d'éléments à sauter (pour la pagination).
        limit (int, optional): Le nombre maximum d'éléments à retourner (pour la pagination).
        first_name (str, optional): Filtrer les membres par prénom.
        last_name (str, optional): Filtrer les membres par nom de famille.
        email (str, optional): Filtrer les membres par email.
        sort (str, optional): Le champ sur lequel trier les membres.
        order (str, optional): L'ordre de tri ('asc' ou 'desc').
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        List[schemas.Member]: La liste des membres соответств. aux critères de filtrage, tri et pagination.
    """
    query = db.query(models.Member)

    # Applique les filtres si des valeurs sont fournies
    if first_name:
        query = query.filter(
            models.Member.first_name.ilike(f"%{first_name}%")
        )  # Recherche insensible à la casse
    if last_name:
        query = query.filter(
            models.Member.last_name.ilike(f"%{last_name}%")
        )  # Recherche insensible à la casse
    if email:
        query = query.filter(models.Member.email.ilike(f"%{email}%"))

    # Applique le tri si un champ de tri est fourni
    if sort:
        if order == "asc":
            query = query.order_by(getattr(models.Member, sort))
        else:
            query = query.order_by(getattr(models.Member, sort).desc())
    else:
        query = query.order_by(models.Member.last_name, models.Member.first_name)  # Tri par défaut

    # Applique la pagination
    members = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(members)} members (skip: {skip}, limit: {limit})")
    return members



# Endpoint pour récupérer un membre par ID
@router.get("/{member_id}", response_model=schemas.Member)
async def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère un membre par son ID.

    Args:
        member_id (int): L'ID du membre à récupérer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        schemas.Member: Le membre соответств. à l'ID fourni.

    Raises:
        HTTPException: Si le membre n'est pas trouvé.
    """
    # Récupère le membre
    db_member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )
    logger.info(f"Retrieved member with ID {member_id}: {db_member.first_name} {db_member.last_name}")
    return db_member



# Endpoint pour modifier un membre (accessible uniquement aux administrateurs)
@router.put("/{member_id}", response_model=schemas.Member)
async def update_member(
    member_id: int,
    member: schemas.MemberUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Modifie un membre existant dans la base de données. Accessible uniquement aux administrateurs.

    Args:
        member_id (int): L'ID du membre à modifier.
        member (schemas.MemberUpdate): Les nouvelles données du membre.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        schemas.Member: Le membre modifié.

    Raises:
        HTTPException: Si le membre n'est pas trouvé ou si l'email/numéro de membre est déjà utilisé.
    """
    # Récupère le membre à modifier
    db_member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    # Vérifie si l'email est déjà utilisé par un autre membre
    if member.email and member.email != db_member.email:
        email_exists = (
            db.query(models.Member).filter(models.Member.email == member.email).first()
        )
        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

    # Vérifie si le numéro de membre est déjà utilisé par un autre membre
    if (
        member.membership_number
        and member.membership_number != db_member.membership_number
    ):
        membership_number_exists = (
            db.query(models.Member)
            .filter(models.Member.membership_number == member.membership_number)
            .first()
        )
        if membership_number_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Membership number already taken",
            )
    if member.user_id and member.user_id != db_member.user_id:
        user_exists = db.query(models.User).filter(models.User.id == member.user_id).first()
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    # Met à jour les champs du membre
    if member.membership_number:
        db_member.membership_number = member.membership_number
    if member.first_name:
        db_member.first_name = member.first_name
    if member.last_name:
        db_member.last_name = member.last_name
    if member.email:
        db_member.email = member.email
    if member.phone_number:
        db_member.phone_number = member.phone_number
    if member.address:
        db_member.address = member.address
    if member.join_date:
        db_member.join_date = member.join_date
    if member.user_id:
        db_member.user_id = member.user_id
    db.commit()
    db.refresh(db_member)
    logger.info(f"Member updated: {db_member.first_name} {db_member.last_name} (ID: {db_member.id})")
    return db_member



# Endpoint pour supprimer un membre (accessible uniquement aux administrateurs)
@router.delete("/{member_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Supprime un membre de la base de données. Accessible uniquement aux administrateurs.

    Args:
        member_id (int): L'ID du membre à supprimer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        dict: Un dictionnaire подтвержд. la suppression du membre.

    Raises:
        HTTPException: Si le membre n'est pas trouvé.
    """
    # Récupère le membre à supprimer
    db_member = db.query(models.Member).filter(models.Member.id == member_id).first()
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    # Supprime le membre
    db.delete(db_member)
    db.commit()
    logger.info(f"Member deleted: {db_member.first_name} {db_member.last_name} (ID: {member_id})")
    return {"message": "Member deleted successfully"}