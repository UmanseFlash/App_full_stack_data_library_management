## Système de Gestion de Bibliothèque Simplifié

Objectif : Créer une application web pour gérer les livres, les membres et les emprunts d'une bibliothèque.

#### Fonctionnalités principales :
Enregistrement des livres, gestion des emprunts et des retours, recherche de livres, gestion des utilisateurs avec authentification.


#### Choix techniques:

FastAPI (Backend API)

Pourquoi : C'est un framework web Python moderne, rapide (grâce à Starlette et Pydantic), et très performant pour construire des APIs. Il offre une validation automatique des requêtes et des réponses (grâce à Pydantic), et génère une documentation interactive (Swagger UI/ReDoc) prête à l'emploi, ce qui est excellent pour le développement et le test. Son approche asynchrone (async/await) le rend efficace pour gérer de nombreuses requêtes concurrentes.

Flask (Frontend Server)

Pourquoi : Bien que l'API soit en FastAPI, Flask a été choisi comme un serveur web léger et simple pour servir les fichiers statiques du frontend (HTML, CSS, JS).

PostgreSQL (Base de Données)

Pourquoi : C'est un système de gestion de base de données relationnelle (SGBDR) open-source, robuste, fiable et très performant. Il est largement utilisé en production et offre une grande flexibilité, une forte intégrité des données et de nombreuses fonctionnalités avancées. Il est idéal pour stocker des données structurées comme celles d'une bibliothèque.

SQLAlchemy

Pourquoi : SQLAlchemy est la bibliothèque ORM la plus populaire en Python. Elle permet d'interagir avec la base de données en utilisant des objets Python (tes modèles User, Book, Member) plutôt que d'écrire des requêtes SQL brutes. Cela rend le code plus lisible, plus maintenable et moins sujet aux erreurs SQL. Elle gère également la création des tables (Base.metadata.create_all(engine)).


Pydantic (Validation des Données et Sérialisation)

Pourquoi : Pydantic est une bibliothèque de validation de données et de paramétrage basée sur les "type hints" de Python. Elle est intégrée nativement à FastAPI. Elle assure que les données reçues par ton API (requêtes) et envoyées par ton API (réponses) sont conformes aux schémas que tu as définis (schemas.py). Cela réduit considérablement la quantité de code de validation manuel et aide à prévenir les erreurs.

JWT (JSON Web Tokens - Authentification)

Pourquoi : JWT est une méthode standard et sécurisée pour l'authentification. Une fois qu'un utilisateur se connecte, l'API lui délivre un token JWT. Ce token est ensuite envoyé avec chaque requête subséquente pour prouver l'identité de l'utilisateur sans avoir à renvoyer les identifiants à chaque fois. C'est sans état, ce qui est bien adapté aux APIs RESTful.

JavaScript (Interactivité Frontend)

Pourquoi : Le JavaScript est le langage du navigateur. Il est utilisé pour rendre ton frontend dynamique : gérer les formulaires, envoyer des requêtes HTTP à ton API (avec fetch), manipuler le DOM pour afficher les données, gérer la navigation entre les sections, et implémenter la logique d'authentification côté client.