// AUTO-LOGIN ]
if (window.location.pathname === '/auth/login') {
    const token = localStorage.getItem('token');

    if (token) {
        fetch('/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(res => {
            if (res.ok) {
                window.location.href = '/scan';
            } else {
                localStorage.removeItem('token');
            }
        })
        .catch(() => {
            localStorage.removeItem('token');
        });
    }
}


// LOGIN
const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        const formData = new URLSearchParams();
        formData.append('username', email);  // OAuth2 uses 'username'
        formData.append('password', password);

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                if (!errorDiv) {
                    alert(data.detail || 'Eroare la autentificare');
                } else {
                    errorDiv.textContent = data.detail || 'Eroare la autentificare';
                    errorDiv.style.display = 'block';
                }
                return;
            }

            localStorage.setItem('token', data.access_token);
            window.location.href = '/scan';

        } catch (error) {
            alert('Parola este gresita!');
        }
    });
}

// REGISTER
const registerForm = document.getElementById('registerForm');

if (registerForm) {
    registerForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const nume = document.getElementById('nume').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

       // if(password <= 8){
       //     alert("Parola trebuie sa aiba minim 8 caracterere!");
       //     return;
       // }

        if (password !== confirmPassword) {
            alert('Parolele nu coincid!');
            return;
        }

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    nume,
                    email,
                    password,
                    confirm_password: confirmPassword
                })
            });

            const data = await response.json();

            if (!response.ok) {
                alert(data.detail || 'Eroare la înregistrare');
                return;
            }

            alert('Cont creat cu succes!');
            window.location.href = '/auth/login';

        } catch (error) {
            alert('Eroare de conexiune');
        }
    });
}