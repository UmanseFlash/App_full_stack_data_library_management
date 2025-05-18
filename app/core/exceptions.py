from fastapi import HTTPException

class CustomException(HTTPException):
    """
    Exception personnalisée pour gérer les erreurs de l'application.
    Hérite de HTTPException de FastAPI pour pouvoir être utilisée
    de la même manière que les exceptions HTTP standard.
    """

    def __init__(self, status_code: int, detail: str):
        """
        Initialise une nouvelle instance de CustomException.

        Args:
            status_code (int): Le code d'état HTTP de l'erreur.
            detail (str): Un message descriptif de l'erreur.
        """
        super().__init__(status_code=status_code, detail=detail)


# Exemple d'utilisation (vous pouvez définir des exceptions spécifiques pour votre application)
class BookNotFoundException(CustomException):
    def __init__(self, book_id: int):
        super().__init__(
            status_code=404, detail=f"Book with ID {book_id} not found"
        )


class MemberNotFoundException(CustomException):
    def __init__(self, member_id: int):
        super().__init__(
            status_code=404, detail=f"Member with ID {member_id} not found"
        )