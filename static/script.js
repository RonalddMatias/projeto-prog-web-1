const API_URL = '/users';

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    document.getElementById('userForm').addEventListener('submit', handleCreateUser);
});

async function loadUsers() {
    try {
        const response = await fetch(API_URL);
        const users = await response.json();
        renderUsers(users);
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function renderUsers(users) {
    const container = document.getElementById('userList');
    container.innerHTML = '';

    users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.innerHTML = `
            <h3>${user.username}</h3>
            <p><strong>ID:</strong> ${user.id}</p>
            <p><strong>Email:</strong> ${user.email}</p>
            <p><strong>Name:</strong> ${user.full_name || 'N/A'}</p>
            <button class="delete-btn" onclick="deleteUser(${user.id})">TERMINATE</button>
        `;
        container.appendChild(card);
    });
}

async function handleCreateUser(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const fullName = document.getElementById('fullName').value;

    const payload = {
        username,
        email,
        full_name: fullName || null
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        console.log(response);

        if (response.ok) {
            document.getElementById('userForm').reset();
            loadUsers();
        } else {
            const error = await response.json();
            alert('Error: ' + error.detail);
        }
    } catch (error) {
        console.error('Error creating user:', error);
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to terminate this operative?')) return;

    try {
        const response = await fetch(`${API_URL}/${userId}`, {
            method: 'DELETE'
        });

        console.log(response);

        if (response.ok) {
            loadUsers();
        } else {
            alert('Error deleting user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
    }
}
