from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import get_current_user
from datetime import date
import logging
from sqlalchemy.orm import joinedload

router = APIRouter()
logger = logging.getLogger(__name__)


# Fonction utilitaire pour vérifier la disponibilité d'un livre
def check_book_availability(db: Session, book_id: int) -> bool:
    """
    Vérifie si un livre est disponible pour l'emprunt.

    Args:
        db (Session): La session de base de données.
        book_id (int): L'ID du livre à vérifier.

    Returns:
        bool: True si le livre est disponible, False sinon.
    """
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    return book.available_copies > 0



# Endpoint pour créer un nouvel emprunt
@router.post("/", response_model=schemas.LoanWithDetails, status_code=status.HTTP_201_CREATED)
async def create_loan(
    loan: schemas.LoanCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Crée un nouvel emprunt (lie un livre à un membre).

    Args:
        loan (schemas.LoanCreate): Les données de l'emprunt à créer (book_id, member_id).
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        schemas.LoanWithDetails: L'emprunt nouvellement créé, avec les détails du livre et du membre.

    Raises:
        HTTPException: Si le livre n'est pas trouvé, n'est pas disponible,
            ou si le membre n'est pas trouvé.
    """
    # Vérifie si le livre existe et est disponible
    if not check_book_availability(db, loan.book_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book not available for loan",
        )

    # Vérifie si le membre existe
    member = db.query(models.Member).filter(models.Member.id == loan.member_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    # Crée l'emprunt en utilisant la table d'association
    book = db.query(models.Book).filter(models.Book.id == loan.book_id).first()
    book.available_copies -= 1  # Décrémente le nombre d'exemplaires disponibles
    book.members.append(member)  # Ajoute le membre à la liste des emprunteurs du livre

    # Crée un enregistrement dans la table d'association pour stocker les détails de l'emprunt
    loan_association = models.loan_association_table.insert().values(
        book_id=loan.book_id,
        member_id=loan.member_id,
        loan_date=loan.loan_date,
        status="En cours",
    )
    db.execute(loan_association)

    db.commit()

    # Récupère l'emprunt avec les détails du livre et du membre pour la réponse
    created_loan = (
        db.query(models.loan_association_table)
        .filter(
            models.loan_association_table.c.book_id == loan.book_id,
            models.loan_association_table.c.member_id == loan.member_id,
        )
        .first()
    )

    # Construire manuellement le schéma LoanWithDetails
    loan_with_details = schemas.LoanWithDetails(
        id=created_loan[0],  # L'ID de l'emprunt dans la table d'association n'est pas directement exposé.
        book=schemas.Book.from_orm(book),
        member=schemas.Member.from_orm(member),
        loan_date=created_loan[2],
        return_date=created_loan[3],
        status=created_loan[4],
    )

    logger.info(
        f"Loan created: Book ID {loan.book_id} - Member ID {loan.member_id} - Status: En cours"
    )
    return loan_with_details



# Endpoint pour récupérer tous les emprunts
@router.get("/", response_model=List[schemas.LoanWithDetails])
async def get_loans(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None,
                                            description="Filter by loan status: 'En cours', 'Retourné', 'En retard'"),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère tous les emprunts, avec pagination et filtrage par statut.

    Args:
        db (Session, optional): La session de base de données.
        skip (int, optional): Le nombre d'éléments à sauter (pour la pagination).
        limit (int, optional): Le nombre maximum d'éléments à retourner (pour la pagination).
        status_filter (str, optional): Filtrer les emprunts par statut ('En cours', 'Retourné', 'En retard').
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        List[schemas.LoanWithDetails]: La liste des emprunts соответств. aux critères de filtrage et pagination.
    """
    query = (
        db.query(models.loan_association_table)
        .options(
            joinedload(models.Book), joinedload(models.Member)
        )  # Charger les détails du livre et du membre
    )

    if status_filter:
        query = query.filter(models.loan_association_table.c.status == status_filter)

    # Applique la pagination
    loans = query.offset(skip).limit(limit).all()

    # Construire la réponse manuellement pour inclure les détails du livre et du membre
    loans_with_details = []
    for loan in loans:
        book = db.query(models.Book).filter(models.Book.id == loan[1]).first()
        member = db.query(models.Member).filter(models.Member.id == loan[2]).first()
        loan_with_details = schemas.LoanWithDetails(
            id=loan[0],
            book=schemas.Book.from_orm(book),
            member=schemas.Member.from_orm(member),
            loan_date=loan[2],
            return_date=loan[3],
            status=loan[4],
        )
        loans_with_details.append(loan_with_details)

    logger.info(f"Retrieved {len(loans_with_details)} loans (skip: {skip}, limit: {limit})")
    return loans_with_details



# Endpoint pour récupérer un emprunt par ID
@router.get("/{loan_id}", response_model=schemas.LoanWithDetails)
async def get_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère un emprunt par son ID.

    Args:
        loan_id (int): L'ID de l'emprunt à récupérer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        schemas.LoanWithDetails: L'emprunt соответств. à l'ID fourni.

    Raises:
        HTTPException: Si l'emprunt n'est pas trouvé.
    """

    loan = (
        db.query(models.loan_association_table)
        .filter(models.loan_association_table.c.book_id == loan_id)
        .first()
    )
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )

    book = db.query(models.Book).filter(models.Book.id == loan[1]).first()
    member = db.query(models.Member).filter(models.Member.id == loan[2]).first()
    loan_with_details = schemas.LoanWithDetails(
        id=loan[0],
        book=schemas.Book.from_orm(book),
        member=schemas.Member.from_orm(member),
        loan_date=loan[2],
        return_date=loan[3],
        status=loan[4],
    )
    logger.info(f"Retrieved loan with ID {loan_id}")
    return loan_with_details



# Endpoint pour retourner un livre (mettre à jour la date de retour)
@router.put("/{loan_id}", response_model=schemas.LoanWithDetails)
async def return_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Enregistre le retour d'un livre (met à jour la date de retour de l'emprunt).

    Args:
        loan_id (int): L'ID de l'emprunt dont le livre est retourné.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
       schemas.LoanWithDetails: L'emprunt mis à jour avec la date de retour.

    Raises:
        HTTPException: Sil'emprunt n'est pas trouvé ou si le livre a déjà été retourné.
    """
    # loan = db.query(models.Loan).filter(models.Loan.id == loan_id).first()
    loan_to_return = (
        db.query(models.loan_association_table)
        .filter(models.loan_association_table.c.book_id == loan_id)
        .first()
    )

    if not loan_to_return:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found"
        )

    if loan_to_return[3]:  # Vérifie si la date de retour est déjà définie
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book already returned",
        )

    # Met à jour la date de retour
    # loan.return_date = date.today()
    # loan.status = "Retourné"
    update_statement = (
        models.loan_association_table.update()
        .where(models.loan_association_table.c.book_id == loan_id)
        .values(return_date=date.today(), status="Retourné")
    )
    db.execute(update_statement)

    # Incrémente le nombre d'exemplaires disponibles du livre
    book = db.query(models.Book).filter(models.Book.id == loan_to_return[1]).first()
    book.available_copies += 1
    db.commit()

    # Récupère l'emprunt mis à jour avec les détails
    loan = (
        db.query(models.loan_association_table)
        .filter(models.loan_association_table.c.book_id == loan_id)
        .first()
    )
    book = db.query(models.Book).filter(models.Book.id == loan[1]).first()
    member = db.query(models.Member).filter(models.Member.id == loan[2]).first()
    loan_with_details = schemas.LoanWithDetails(
        id=loan[0],
        book=schemas.Book.from_orm(book),
        member=schemas.Member.from_orm(member),
        loan_date=loan[2],
        return_date=loan[3],
        status=loan[4],
    )
    logger.info(f"Loan returned: Loan ID {loan_id}")
    return loan_with_details


# Endpoint pour récupérer les emprunts en retard
@router.get("/overdue/", response_model=List[schemas.LoanWithDetails])
async def get_overdue_loans(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    """
    Récupère tous les emprunts en retard (dont la date de retour prévue est dépassée).

    Args:
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        List[schemas.LoanWithDetails]: La liste des emprunts en retard.
    """
    today = date.today()
   
    # Requête pour récupérer les emprunts en retard en utilisant la table d'association
    overdue_loans = (
        db.query(models.loan_association_table)
        .filter(
            models.loan_association_table.c.return_date < today,
            models.loan_association_table.c.status == "En cours",
        )
        .all()
    )

    loans_with_details = []
    for loan in overdue_loans:
        book = db.query(models.Book).filter(models.Book.id == loan[1]).first()
        member = db.query(models.Member).filter(models.Member.id == loan[2]).first()
        loan_with_details = schemas.LoanWithDetails(
            id=loan[0],
            book=schemas.Book.from_orm(book),
            member=schemas.Member.from_orm(member),
            loan_date=loan[2],
            return_date=loan[3],
            status=loan[4],
        )
        loans_with_details.append(loan_with_details)
    logger.info(f"Retrieved {len(loans_with_details)} overdue loans")
    return loans_with_details