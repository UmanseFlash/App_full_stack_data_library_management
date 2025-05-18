from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# Définition de la base
Base = declarative_base()

loan_association_table = Table(
    "loan_association",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("member_id", ForeignKey("members.id"), primary_key=True),
    Column("loan_date", Date),
    Column("return_date", Date, nullable=True),
    Column("status", String, default="En cours"),
)


# Définition du modèle pour les utilisateurs (membres et bibliothécaires)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="member")  # 'member', 'librarian', 'admin'
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    created_at = Column(Date, nullable=False)
    last_login = Column(Date, nullable=True)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"


# Définition du modèle pour les livres
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    isbn = Column(String, unique=True, index=True, nullable=False)
    publisher = Column(String, nullable=True)
    publication_date = Column(Date, nullable=True)
    number_of_copies = Column(Integer, default=1, nullable=False)  # Nombre total d'exemplaires
    available_copies = Column(Integer, default=1,
                                  nullable=False)  # Nombre d'exemplaires disponibles

    # Ajout de la relation avec Member via la table d'association
    members = relationship(
        "Member", secondary=loan_association_table, back_populates="books"
    )

    def __repr__(self):
        return f"<Book(title='{self.title}', author='{self.author}', isbn='{self.isbn}')>"


# Définition du modèle pour les membres
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    membership_number = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    join_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True,
                           nullable=False)  # Clé étrangère vers la table User
    user = relationship("User", backref="member",
                            uselist=False)  # Relation one-to-one avec User

    # Ajout de la relation avec Book via la table d'association
    books = relationship(
        "Book", secondary=loan_association_table, back_populates="members"
    )

    def __repr__(self):
        return (
            f"<Member(membership_number='{self.membership_number}', "
            f"first_name='{self.first_name}', last_name='{self.last_name}')>"
        )