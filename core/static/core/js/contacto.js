(function () {
    var formulario = document.getElementById('contactForm');
    if (!formulario) return;

    var nombre = document.getElementById('name');
    var telefono = document.getElementById('phone');
    var aviso = document.getElementById('contacto-error');
    var nombreOk = /^[^\W\d_]+(?:[ '\u2019-][^\W\d_]+)*$/u;
    var telefonoOk = /^[0-9+\-().\s]{0,20}$/;

    formulario.addEventListener('submit', function (event) {
        var mensaje = '';
        var textoNombre = (nombre && nombre.value || '').trim();
        if (/\d/.test(textoNombre) || !nombreOk.test(textoNombre)) {
            mensaje = 'El nombre solo puede incluir letras, espacios, guiones y apóstrofes.';
        } else if (telefono && telefono.value.trim() && !telefonoOk.test(telefono.value.trim())) {
            mensaje = 'El teléfono admite hasta 20 caracteres: números, espacios, +, -, paréntesis y puntos.';
        }
        if (!mensaje) {
            if (aviso) aviso.textContent = '';
            return;
        }
        event.preventDefault();
        if (aviso) aviso.textContent = mensaje;
    });
})();
