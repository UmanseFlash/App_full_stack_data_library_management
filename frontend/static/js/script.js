const API_BASE_URL = 'http://localhost:8000'; // URL de ton API FastAPI

// Fonction utilitaire pour envoyer des requêtes à l'API
async function apiRequest(url, method = 'GET', data = null, needsAuth = false) {
    const headers = {
        'Content-Type': 'application/json',
    };

    const token = localStorage.getItem('jwt_token');
    if (needsAuth && token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers,
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${url}`, options);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Erreur API:', error);
        throw error; // Propager l'erreur pour un traitement spécifique dans l'UI
    }
}

// Gestion de l'affichage des sections
function showSection(sectionId) {
    const sections = ['login-section', 'register-section', 'books-section', 'members-section', 'loans-section'];
    sections.forEach(id => {
        document.getElementById(id).classList.add('hidden');
    });
    document.getElementById(sectionId).classList.remove('hidden');

    // Mettre à jour l'état des boutons de navigation
    const navButtons = document.querySelectorAll('nav button');
    navButtons.forEach(btn => btn.classList.remove('bg-blue-600', 'text-white')); // Supprimer la classe active
    const activeBtn = document.getElementById(`nav-${sectionId.replace('-section', '')}`);
    if (activeBtn) {
        activeBtn.classList.add('bg-blue-600', 'text-white'); // Ajouter la classe active
    }
}

// Vérifier l'état de connexion au chargement de la page
function checkLoginStatus() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        document.getElementById('nav-login').classList.add('hidden');
        document.getElementById('nav-register').classList.add('hidden');
        document.getElementById('nav-logout').classList.remove('hidden');
        // Tenter de récupérer les infos utilisateur pour vérifier le token
        apiRequest('/auth/me', 'GET', null, true)
            .then(user => {
                console.log("Utilisateur connecté:", user);
                // Afficher une section par défaut après connexion
                showSection('books-section');
                loadBooks(); // Charger les livres après connexion
            })
            .catch(() => {
                // Token invalide ou expiré
                localStorage.removeItem('jwt_token');
                document.getElementById('nav-login').classList.remove('hidden');
                document.getElementById('nav-register').classList.remove('hidden');
                document.getElementById('nav-logout').classList.add('hidden');
                showSection('login-section');
            });
    } else {
        document.getElementById('nav-login').classList.remove('hidden');
        document.getElementById('nav-register').classList.remove('hidden');
        document.getElementById('nav-logout').classList.add('hidden');
        showSection('login-section');
    }
}


// --- Gestion de l'Authentification ---

// Formulaire de connexion
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const messageDiv = document.getElementById('login-message');
    messageDiv.textContent = '';

    try {
        // FastAPI s'attend à un formulaire x-www-form-urlencoded pour OAuth2PasswordRequestForm
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
        }

        const data = await response.json();
        localStorage.setItem('jwt_token', data.access_token);
        messageDiv.textContent = 'Connexion réussie !';
        messageDiv.classList.remove('text-red-500');
        messageDiv.classList.add('text-green-500');
        checkLoginStatus(); // Mettre à jour l'état de la navigation
    } catch (error) {
        messageDiv.textContent = `Erreur de connexion: ${error.message}`;
        messageDiv.classList.remove('text-green-500');
        messageDiv.classList.add('text-red-500');
    }
});

// Formulaire d'inscription
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const messageDiv = document.getElementById('register-message');
    messageDiv.textContent = '';

    try {
        const response = await apiRequest('/auth/register', 'POST', data);
        messageDiv.textContent = 'Inscription réussie ! Vous pouvez maintenant vous connecter.';
        messageDiv.classList.remove('text-red-500');
        messageDiv.classList.add('text-green-500');
        form.reset(); // Réinitialiser le formulaire
        showSection('login-section'); // Rediriger vers la page de connexion
    } catch (error) {
        messageDiv.textContent = `Erreur d'inscription: ${error.message}`;
        messageDiv.classList.remove('text-green-500');
        messageDiv.classList.add('text-red-500');
    }
});

// Bouton de déconnexion
document.getElementById('nav-logout').addEventListener('click', () => {
    localStorage.removeItem('jwt_token');
    checkLoginStatus();
    alert('Vous avez été déconnecté.'); // Utilisation d'alert pour la simplicité, à remplacer par une modale
});


// --- Gestion des Livres ---
let booksCurrentPage = 1;
const booksLimit = 10;

async function loadBooks(searchQuery = '') {
    const container = document.getElementById('books-list-container');
    container.innerHTML = '<p class="text-gray-600">Chargement des livres...</p>';
    const pageInfo = document.getElementById('books-page-info');

    let url = `/books?skip=${(booksCurrentPage - 1) * booksLimit}&limit=${booksLimit}`;
    if (searchQuery) {
        url += `&title=${encodeURIComponent(searchQuery)}&author=${encodeURIComponent(searchQuery)}&isbn=${encodeURIComponent(searchQuery)}`;
    }

    try {
        const books = await apiRequest(url, 'GET', null, true);
        renderBooks(books);
        pageInfo.textContent = `Page ${booksCurrentPage}`;
    } catch (error) {
        container.innerHTML = `<p class="text-red-500">Erreur lors du chargement des livres: ${error.message}</p>`;
    }
}

function renderBooks(books) {
    const container = document.getElementById('books-list-container');
    if (books.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Aucun livre trouvé.</p>';
        return;
    }

    const table = document.createElement('table');
    table.classList.add('w-full', 'table-auto', 'rounded-lg', 'overflow-hidden');
    table.innerHTML = `
        <thead>
            <tr class="bg-blue-100">
                <th class="px-4 py-2">ID</th>
                <th class="px-4 py-2">Titre</th>
                <th class="px-4 py-2">Auteur</th>
                <th class="px-4 py-2">ISBN</th>
                <th class="px-4 py-2">Exemplaires</th>
                <th class="px-4 py-2">Disponibles</th>
                <th class="px-4 py-2">Actions</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');

    books.forEach(book => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td class="border px-4 py-2">${book.id}</td>
            <td class="border px-4 py-2">${book.title}</td>
            <td class="border px-4 py-2">${book.author}</td>
            <td class="border px-4 py-2">${book.isbn}</td>
            <td class="border px-4 py-2">${book.number_of_copies}</td>
            <td class="border px-4 py-2">${book.available_copies}</td>
            <td class="border px-4 py-2">
                <button data-id="${book.id}" class="px-4 py-2 rounded-md font-semibold transition duration-200 ease-in-out bg-blue-600 text-white hover:bg-blue-700 text-sm edit-book-btn">Éditer</button>
                <button data-id="${book.id}" class="px-4 py-2 rounded-md font-semibold transition duration-200 ease-in-out bg-red-500 text-white hover:bg-red-600 text-sm delete-book-btn ml-1">Supprimer</button>
            </td>
        `;
    });
    container.innerHTML = '';
    container.appendChild(table);

    // Ajouter les écouteurs d'événements pour les boutons d'édition et de suppression
    document.querySelectorAll('.edit-book-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            alert(`Fonctionnalité d'édition pour le livre ID: ${e.target.dataset.id} à implémenter.`);
            // showEditBookModal(e.target.dataset.id);
        });
    });
    document.querySelectorAll('.delete-book-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            if (confirm(`Êtes-vous sûr de vouloir supprimer le livre ID: ${e.target.dataset.id} ?`)) {
                try {
                    await apiRequest(`/books/${e.target.dataset.id}`, 'DELETE', null, true);
                    alert('Livre supprimé avec succès !');
                    loadBooks(); // Recharger la liste
                } catch (error) {
                    alert(`Erreur lors de la suppression: ${error.message}`);
                }
            }
        });
    });
}

// Pagination des livres
document.getElementById('books-prev-page').addEventListener('click', () => {
    if (booksCurrentPage > 1) {
        booksCurrentPage--;
        loadBooks(document.getElementById('books-search-query').value);
    }
});
document.getElementById('books-next-page').addEventListener('click', () => {
    booksCurrentPage++;
    loadBooks(document.getElementById('books-search-query').value);
});

// Recherche de livres
document.getElementById('books-search-btn').addEventListener('click', () => {
    booksCurrentPage = 1;
    loadBooks(document.getElementById('books-search-query').value);
});

// Afficher le modal d'ajout de livre
document.getElementById('books-add-btn').addEventListener('click', () => {
    document.getElementById('add-book-modal').classList.remove('hidden');
    document.getElementById('add-book-form').reset();
    document.getElementById('add-book-message').textContent = '';
});

// Annuler l'ajout de livre
document.getElementById('cancel-add-book').addEventListener('click', () => {
    document.getElementById('add-book-modal').classList.add('hidden');
});

// Soumettre le formulaire d'ajout de livre
document.getElementById('add-book-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    // Convertir les nombres en entiers
    data.number_of_copies = parseInt(data.number_of_copies);
    data.available_copies = parseInt(data.number_of_copies); // Au début, disponibles = total
    const messageDiv = document.getElementById('add-book-message');
    messageDiv.textContent = '';

    try {
        await apiRequest('/books/', 'POST', data, true);
        messageDiv.textContent = 'Livre ajouté avec succès !';
        messageDiv.classList.remove('text-red-500');
        messageDiv.classList.add('text-green-500');
        form.reset();
        document.getElementById('add-book-modal').classList.add('hidden');
        loadBooks(); // Recharger la liste des livres
    } catch (error) {
        messageDiv.textContent = `Erreur lors de l'ajout: ${error.message}`;
        messageDiv.classList.remove('text-green-500');
        messageDiv.classList.add('text-red-500');
    }
});


// --- Gestion des Membres ---
let membersCurrentPage = 1;
const membersLimit = 10;

async function loadMembers(searchQuery = '') {
    const container = document.getElementById('members-list-container');
    container.innerHTML = '<p class="text-gray-600">Chargement des membres...</p>';
    const pageInfo = document.getElementById('members-page-info');

    let url = `/members?skip=${(membersCurrentPage - 1) * membersLimit}&limit=${membersLimit}`;
    if (searchQuery) {
        url += `&first_name=${encodeURIComponent(searchQuery)}&last_name=${encodeURIComponent(searchQuery)}&email=${encodeURIComponent(searchQuery)}`;
    }

    try {
        const members = await apiRequest(url, 'GET', null, true);
        renderMembers(members);
        pageInfo.textContent = `Page ${membersCurrentPage}`;
    } catch (error) {
        container.innerHTML = `<p class="text-red-500">Erreur lors du chargement des membres: ${error.message}</p>`;
    }
}

function renderMembers(members) {
    const container = document.getElementById('members-list-container');
    if (members.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Aucun membre trouvé.</p>';
        return;
    }

    const table = document.createElement('table');
    table.classList.add('w-full', 'table-auto', 'rounded-lg', 'overflow-hidden');
    table.innerHTML = `
        <thead>
            <tr class="bg-blue-100">
                <th class="px-4 py-2">ID</th>
                <th class="px-4 py-2">N° Adhérent</th>
                <th class="px-4 py-2">Prénom</th>
                <th class="px-4 py-2">Nom</th>
                <th class="px-4 py-2">Email</th>
                <th class="px-4 py-2">Actions</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');

    members.forEach(member => {
        const row = tbody.insertCell();
        row.innerHTML = `
            <td class="border px-4 py-2">${member.id}</td>
            <td class="border px-4 py-2">${member.membership_number}</td>
            <td class="border px-4 py-2">${member.first_name}</td>
            <td class="border px-4 py-2">${member.last_name}</td>
            <td class="border px-4 py-2">${member.email}</td>
            <td class="border px-4 py-2">
                <button data-id="${member.id}" class="px-4 py-2 rounded-md font-semibold transition duration-200 ease-in-out bg-blue-600 text-white hover:bg-blue-700 text-sm edit-member-btn">Éditer</button>
                <button data-id="${member.id}" class="px-4 py-2 rounded-md font-semibold transition duration-200 ease-in-out bg-red-500 text-white hover:bg-red-600 text-sm delete-member-btn ml-1">Supprimer</button>
            </td>
        `;
    });
    container.innerHTML = '';
    container.appendChild(table);

    // Ajouter les écouteurs d'événements pour les boutons d'édition et de suppression
    document.querySelectorAll('.edit-member-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            alert(`Fonctionnalité d'édition pour le membre ID: ${e.target.dataset.id} à implémenter.`);
            // showEditMemberModal(e.target.dataset.id);
        });
    });
    document.querySelectorAll('.delete-member-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            if (confirm(`Êtes-vous sûr de vouloir supprimer le membre ID: ${e.target.dataset.id} ?`)) {
                try {
                    await apiRequest(`/members/${e.target.dataset.id}`, 'DELETE', null, true);
                    alert('Membre supprimé avec succès !');
                    loadMembers(); // Recharger la liste
                } catch (error) {
                    alert(`Erreur lors de la suppression: ${error.message}`);
                }
            }
        });
    });
}

// Pagination des membres
document.getElementById('members-prev-page').addEventListener('click', () => {
    if (membersCurrentPage > 1) {
        membersCurrentPage--;
        loadMembers(document.getElementById('members-search-query').value);
    }
});
document.getElementById('members-next-page').addEventListener('click', () => {
    membersCurrentPage++;
    loadMembers(document.getElementById('members-search-query').value);
});

// Recherche de membres
document.getElementById('members-search-btn').addEventListener('click', () => {
    membersCurrentPage = 1; // Réinitialiser la page lors d'une nouvelle recherche
    loadMembers(document.getElementById('members-search-query').value);
});

// Afficher le modal d'ajout de membre
document.getElementById('members-add-btn').addEventListener('click', () => {
    document.getElementById('add-member-modal').classList.remove('hidden');
    document.getElementById('add-member-form').reset();
    document.getElementById('add-member-message').textContent = '';
});

// Annuler l'ajout de membre
document.getElementById('cancel-add-member').addEventListener('click', () => {
    document.getElementById('add-member-modal').classList.add('hidden');
});

// Soumettre le formulaire d'ajout de membre
document.getElementById('add-member-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.user_id = parseInt(data.user_id); // Convertir en entier
    const messageDiv = document.getElementById('add-member-message');
    messageDiv.textContent = '';

    try {
        await apiRequest('/members/', 'POST', data, true);
        messageDiv.textContent = 'Membre ajouté avec succès !';
        messageDiv.classList.remove('text-red-500');
        messageDiv.classList.add('text-green-500');
        form.reset();
        document.getElementById('add-member-modal').classList.add('hidden');
        loadMembers(); // Recharger la liste des membres
    } catch (error) {
        messageDiv.textContent = `Erreur lors de l'ajout: ${error.message}`;
        messageDiv.classList.remove('text-green-500');
        messageDiv.classList.add('text-red-500');
    }
});


// --- Gestion des Emprunts ---
let loansCurrentPage = 1;
const loansLimit = 10;

async function loadLoans(statusFilter = null, overdueOnly = false) {
    const container = document.getElementById('loans-list-container');
    container.innerHTML = '<p class="text-gray-600">Chargement des emprunts...</p>';
    const pageInfo = document.getElementById('loans-page-info');

    let url = `/loans?skip=${(loansCurrentPage - 1) * loansLimit}&limit=${loansLimit}`;
    if (statusFilter) {
        url += `&status_filter=${encodeURIComponent(statusFilter)}`;
    }
    if (overdueOnly) {
        url = `/loans/overdue?skip=${(loansCurrentPage - 1) * loansLimit}&limit=${loansLimit}`;
    }

    try {
        const loans = await apiRequest(url, 'GET', null, true);
        renderLoans(loans);
        pageInfo.textContent = `Page ${loansCurrentPage}`;
    } catch (error) {
        container.innerHTML = `<p class="text-red-500">Erreur lors du chargement des emprunts: ${error.message}</p>`;
    }
}

function renderLoans(loans) {
    const container = document.getElementById('loans-list-container');
    if (loans.length === 0) {
        container.innerHTML = '<p class="text-gray-600">Aucun emprunt trouvé.</p>';
        return;
    }

    const table = document.createElement('table');
    table.classList.add('w-full', 'table-auto', 'rounded-lg', 'overflow-hidden');
    table.innerHTML = `
        <thead>
            <tr class="bg-blue-100">
                <th class="px-4 py-2">ID Emprunt</th>
                <th class="px-4 py-2">Livre</th>
                <th class="px-4 py-2">Membre</th>
                <th class="px-4 py-2">Date Emprunt</th>
                <th class="px-4 py-2">Date Retour</th>
                <th class="px-4 py-2">Statut</th>
                <th class="px-4 py-2">Actions</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');

    loans.forEach(loan => {
        const row = tbody.insertRow();
        const returnButton = loan.status === 'En cours' ?
            `<button data-id="${loan.id}" class="px-4 py-2 rounded-md font-semibold transition duration-200 ease-in-out bg-blue-600 text-white hover:bg-blue-700 text-sm return-loan-btn">Retourner</button>` :
            '';
        row.innerHTML = `
            <td class="border px-4 py-2">${loan.id}</td>
            <td class="border px-4 py-2">${loan.book ? loan.book.title : 'N/A'} (ID: ${loan.book ? loan.book.id : 'N/A'})</td>
            <td class="border px-4 py-2">${loan.member ? loan.member.first_name + ' ' + loan.member.last_name : 'N/A'} (ID: ${loan.member ? loan.member.id : 'N/A'})</td>
            <td class="border px-4 py-2">${loan.loan_date}</td>
            <td class="border px-4 py-2">${loan.return_date || 'N/A'}</td>
            <td class="border px-4 py-2">${loan.status}</td>
            <td class="border px-4 py-2">
                ${returnButton}
            </td>
        `;
    });
    container.innerHTML = '';
    container.appendChild(table);

    // Ajouter les écouteurs d'événements pour les boutons de retour
    document.querySelectorAll('.return-loan-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            if (confirm(`Confirmer le retour de l'emprunt ID: ${e.target.dataset.id} ?`)) {
                try {
                    await apiRequest(`/loans/${e.target.dataset.id}`, 'PUT', null, true);
                    alert('Livre retourné avec succès !');
                    loadLoans(document.getElementById('loans-status-filter').value); // Recharger la liste
                } catch (error) {
                    alert(`Erreur lors du retour: ${error.message}`);
                }
            }
        });
    });
}

// Pagination des emprunts
document.getElementById('loans-prev-page').addEventListener('click', () => {
    if (loansCurrentPage > 1) {
        loansCurrentPage--;
        loadLoans(document.getElementById('loans-status-filter').value);
    }
});
document.getElementById('loans-next-page').addEventListener('click', () => {
    loansCurrentPage++;
    loadLoans(document.getElementById('loans-status-filter').value);
});

// Filtrage par statut des emprunts
document.getElementById('loans-status-filter').addEventListener('change', (e) => {
    loansCurrentPage = 1;
    loadLoans(e.target.value);
});

// Afficher les emprunts en retard
document.getElementById('loans-overdue-btn').addEventListener('click', () => {
    loansCurrentPage = 1;
    loadLoans(null, true); // Passer null pour le statut, et true pour les retards
});

// Afficher le modal d'ajout d'emprunt
document.getElementById('loans-add-btn').addEventListener('click', () => {
    document.getElementById('add-loan-modal').classList.remove('hidden');
    document.getElementById('add-loan-form').reset();
    document.getElementById('add-loan-message').textContent = '';
    // Pré-remplir la date d'emprunt avec la date du jour
    document.getElementById('add-loan-date').valueAsDate = new Date();
});

// Annuler l'ajout d'emprunt
document.getElementById('cancel-add-loan').addEventListener('click', () => {
    document.getElementById('add-loan-modal').classList.add('hidden');
});

// Soumettre le formulaire d'ajout d'emprunt
document.getElementById('add-loan-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.book_id = parseInt(data.book_id);
    data.member_id = parseInt(data.member_id);
    const messageDiv = document.getElementById('add-loan-message');
    messageDiv.textContent = '';

    try {
        await apiRequest('/loans/', 'POST', data, true);
        messageDiv.textContent = 'Emprunt enregistré avec succès !';
        messageDiv.classList.remove('text-red-500');
        messageDiv.classList.add('text-green-500');
        form.reset();
        document.getElementById('add-loan-modal').classList.add('hidden');
        loadLoans(); // Recharger la liste des emprunts
    } catch (error) {
        messageDiv.textContent = `Erreur lors de l'enregistrement de l'emprunt: ${error.message}`;
        messageDiv.classList.remove('text-green-500');
        messageDiv.classList.add('text-red-500');
    }
});


// --- Écouteurs d'événements de navigation ---
document.getElementById('nav-login').addEventListener('click', () => showSection('login-section'));
document.getElementById('nav-register').addEventListener('click', () => showSection('register-section'));
document.getElementById('nav-books').addEventListener('click', () => {
    showSection('books-section');
    loadBooks();
});
document.getElementById('nav-members').addEventListener('click', () => {
    showSection('members-section');
    loadMembers();
});
document.getElementById('nav-loans').addEventListener('click', () => {
    showSection('loans-section');
    loadLoans();
});


// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', checkLoginStatus);
