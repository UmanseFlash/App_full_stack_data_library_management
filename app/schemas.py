from datetime import date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator

# Schéma pour la création d'un utilisateur
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    created_at: date = Field(default_factory=date.today)

    @validator("username")
    def validate_username(cls, value):
        if not value.isalnum():
            raise ValueError("Username must contain only alphanumeric characters")
        return value


# Schéma pour la représentation d'un utilisateur
class User(UserCreate):
    id: int
    role: str
    last_login: Optional[date]

    class Config:
        from_attributes = True  # Pydantic v2


# Schéma pour la connexion d'un utilisateur
class UserLogin(BaseModel):
    username: str
    password: str



# Schéma pour la création d'un livre
class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=200)
    isbn: str = Field(..., min_length=10, max_length=13)
    publisher: Optional[str] = Field(None, max_length=200)
    publication_date: Optional[date]
    number_of_copies: int = Field(1, ge=1)
    available_copies: int = Field(1, ge=0)

    @validator("isbn")
    def validate_isbn(cls, value):
        if not value.isdigit():
            raise ValueError("ISBN must contain only digits")
        return value



# Schéma pour la représentation d'un livre
class Book(BookCreate):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2



# Schéma pour la mise à jour d'un livre
class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=200)
    isbn: Optional[str] = Field(None, min_length=10, max_length=13)
    publisher: Optional[str] = Field(None, max_length=200)
    publication_date: Optional[date]
    number_of_copies: Optional[int] = Field(None, ge=1)
    available_copies: Optional[int] = Field(None, ge=0)

    @validator("isbn")
    def validate_isbn(cls, value):
        if value is None:  # Permettre à isbn d'être None
            return None
        if not value.isdigit():
            raise ValueError("ISBN must contain only digits")
        return value


# Schéma pour la création d'un membre
class MemberCreate(BaseModel):
    membership_number: str = Field(..., min_length=5, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)
    join_date: date = Field(default_factory=date.today)
    user_id: int  # Clé étrangère vers l'utilisateur


# Schéma pour la représentation d'un membre
class Member(MemberCreate):
    id: int

    class Config:
        from_attributes = True  # Pydantic v2


# Schéma pour la mise à jour d'un membre
class MemberUpdate(BaseModel):
    membership_number: Optional[str] = Field(None, min_length=5, max_length=20)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr]
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)
    join_date: Optional[date] = Field(None)
    user_id: Optional[int]



# Schéma pour la création d'un emprunt
class LoanCreate(BaseModel):
    book_id: int
    member_id: int
    loan_date: date = Field(default_factory=date.today)
    return_date: Optional[date]
    status: str = "En cours"  # Valeur par défaut

# Schéma pour la représentation d'un emprunt
class Loan(LoanCreate):
    id: int
    class Config:
        from_attributes = True  # Pydantic v2

# Schéma pour la représentation d'un emprunt avec les détails du livre et du membre
class LoanWithDetails(BaseModel):
    id: int
    book: Book
    member: Member
    loan_date: date
    return_date: Optional[date]
    status: str

    class Config:
        from_attributes = True  # Pydantic v2
