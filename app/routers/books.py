from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import get_current_user, get_current_admin_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Endpoint pour créer un nouveau livre (accessible uniquement aux administrateurs)
@router.post("/", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Crée un nouveau livre dans la base de données.  Accessible uniquement aux administrateurs.

    Args:
        book (schemas.BookCreate): Les données du livre à créer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        schemas.Book: Le livre nouvellement créé.

    Raises:
        HTTPException: Si un livre avec le même ISBN existe déjà.
    """
    # Vérifie si un livre avec le même ISBN existe déjà
    db_book = db.query(models.Book).filter(models.Book.isbn == book.isbn).first()
    if db_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists"
        )

    # Crée le nouveau livre
    db_book = models.Book(
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        publisher=book.publisher,
        publication_date=book.publication_date,
        number_of_copies=book.number_of_copies,
        available_copies=book.number_of_copies,
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    logger.info(f"Book created: {db_book.title} (ID: {db_book.id})")
    return db_book



# Endpoint pour récupérer tous les livres avec pagination, filtrage et tri
@router.get("/", response_model=List[schemas.Book])
async def get_books(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    isbn: Optional[str] = Query(None),
    sort: Optional[str] = Query(None, regex="^(title|author|publication_date)$"),
    order: Optional[str] = Query("asc", regex="^(asc|desc)$"),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère tous les livres de la base de données, avec pagination, filtrage et tri.

    Args:
        db (Session, optional): La session de base de données.
        skip (int, optional): Le nombre d'éléments à sauter (pour la pagination).
        limit (int, optional): Le nombre maximum d'éléments à retourner (pour la pagination).
        title (str, optional): Filtrer les livres par titre.
        author (str, optional): Filtrer les livres par auteur.
        isbn (str, optional): Filtrer les livres par ISBN.
        sort (str, optional): Le champ sur lequel trier les livres.
        order (str, optional): L'ordre de tri ('asc' ou 'desc').
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        List[schemas.Book]: La liste des livres соответств. aux critères de filtrage, tri et pagination.
    """
    query = db.query(models.Book)

    # Applique les filtres si des valeurs sont fournies
    if title:
        query = query.filter(models.Book.title.ilike(f"%{title}%"))  # Recherche insensible à la casse
    if author:
        query = query.filter(models.Book.author.ilike(f"%{author}%"))
    if isbn:
        query = query.filter(models.Book.isbn == isbn)

    # Applique le tri si un champ de tri est fourni
    if sort:
        if order == "asc":
            query = query.order_by(getattr(models.Book, sort))
        else:
            query = query.order_by(getattr(models.Book, sort).desc())
    else:
        query = query.order_by(models.Book.title)  # Tri par défaut par titre

    # Applique la pagination
    books = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(books)} books (skip: {skip}, limit: {limit})")
    return books



# Endpoint pour récupérer un livre par ID
@router.get("/{book_id}", response_model=schemas.Book)
async def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Récupère un livre par son ID.

    Args:
        book_id (int): L'ID du livre à récupérer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.

    Returns:
        schemas.Book: Le livre соответств. à l'ID fourni.

    Raises:
        HTTPException: Si le livre n'est pas trouvé.
    """
    # Récupère le livre
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )
    logger.info(f"Retrieved book with ID {book_id}: {db_book.title}")
    return db_book



# Endpoint pour modifier un livre (accessible uniquement aux administrateurs)
@router.put("/{book_id}", response_model=schemas.Book)
async def update_book(
    book_id: int,
    book: schemas.BookUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Modifie un livre existant dans la base de données. Accessible uniquement aux administrateurs.

    Args:
        book_id (int): L'ID du livre à modifier.
        book (schemas.BookUpdate): Les nouvelles données du livre.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        schemas.Book: Le livre modifié.

    Raises:
        HTTPException: Si le livre n'est pas trouvé ou si l'ISBN est déjà utilisé par un autre livre.
    """
    # Récupère le livre à modifier
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    # Vérifie si l'ISBN est déjà utilisé par un autre livre
    if book.isbn and book.isbn != db_book.isbn:
        isbn_exists = db.query(models.Book).filter(models.Book.isbn == book.isbn).first()
        if isbn_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="ISBN already exists"
            )

    # Met à jour les champs du livre
    if book.title:
        db_book.title = book.title
    if book.author:
        db_book.author = book.author
    if book.isbn:
        db_book.isbn = book.isbn
    if book.publisher:
        db_book.publisher = book.publisher
    if book.publication_date:
        db_book.publication_date = book.publication_date
    if book.number_of_copies:
        db_book.number_of_copies = book.number_of_copies
    if book.available_copies:
        db_book.available_copies = book.available_copies
    db.commit()
    db.refresh(db_book)
    logger.info(f"Book updated: {db_book.title} (ID: {db_book.id})")
    return db_book



# Endpoint pour supprimer un livre (accessible uniquement aux administrateurs)
@router.delete("/{book_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user),
):
    """
    Supprime un livre de la base de données. Accessible uniquement aux administrateurs.

    Args:
        book_id (int): L'ID du livre à supprimer.
        db (Session, optional): La session de base de données.
        current_user (models.User, optional): L'utilisateur actuellement authentifié.
            Dépend de get_current_admin_user pour vérifier les droits d'administrateur.

    Returns:
        dict: Un dictionnaire подтвержд. la suppression du livre.

    Raises:
        HTTPException: Si le livre n'est pas trouvé.
    """
    # Récupère le livre à supprimer
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book not found"
        )

    # Supprime le livre
    db.delete(db_book)
    db.commit()
    logger.info(f"Book deleted: {db_book.title} (ID: {book_id})")
    return {"message": "Book deleted successfully"}