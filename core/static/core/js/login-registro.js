const loginForm = document.getElementById('loginForm');
const popupBg = document.getElementById('popup-bg');
const popupMsg = document.getElementById('popup-msg');
const regForm = document.getElementById('registerForm');

loginForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const email = document.getElementById('email').value.trim();
    const user = email.split('@')[0];
    popupMsg.innerHTML = `Bienvenido, <strong>${user}</strong>. Inicio de sesión exitoso.`;
    popupBg.style.display = 'flex';
    loginForm.reset();
});

function closePopup() {
    popupBg.style.display = 'none';
}

regForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const name = document.getElementById('name').value.trim();
    const pass = document.getElementById('password').value;
    const conf = document.getElementById('confirm').value;

    if (pass !== conf) {
        alert("Las contraseñas no coinciden");
        return;
    }

    popupMsg.innerHTML = `Registro completado con éxito, <strong>${name}</strong>.`;
    popupBg.style.display = 'flex';
    regForm.reset();
});

function closePopup() {
    popupBg.style.display = 'none';
}