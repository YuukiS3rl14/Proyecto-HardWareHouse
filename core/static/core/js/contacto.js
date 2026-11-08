(function () {
    var formulario = document.getElementById('contactForm');
    if (!formulario) return;

    var nombre = document.getElementById('name');
    var telefono = document.getElementById('phone');
    var pais = document.getElementById('phone-country');
    var aviso = document.getElementById('contacto-error');
    var nombreOk = /^[^\W\d_]+(?:[ '\u2019-][^\W\d_]+)*$/u;
    var reglasNodo = document.getElementById('reglas-telefono');
    var reglas = reglasNodo ? JSON.parse(reglasNodo.textContent) : {};

    function placeholder() {
        if (!pais || !telefono) return;
        var regla = reglas[pais.value];
        telefono.placeholder = regla && regla.ejemplo ? regla.ejemplo : '';
    }

    function telefonoInvalido() {
        if (!telefono) return '';
        var texto = telefono.value.trim();
        if (!texto) return '';
        var regla = reglas[pais && pais.value] || reglas.CL;
        if (!regla) return 'Selecciona un país.';
        var crudo = texto.replace(/[\s().\-]/g, '');
        if (crudo.charAt(0) === '+') crudo = crudo.slice(1);
        if (crudo.indexOf('00') === 0) crudo = crudo.slice(2);
        if (!/^\d+$/.test(crudo)) return 'El teléfono solo puede incluir números y el prefijo del país.';
        if (crudo.indexOf(regla.prefijo) === 0) {
            var resto = crudo.slice(regla.prefijo.length);
            if (resto.length >= regla.min && resto.length <= regla.max) crudo = resto;
        }
        var largoOk = crudo.length >= regla.min && crudo.length <= regla.max;
        var inicioOk = !regla.inicio || crudo.indexOf(regla.inicio) === 0;
        if (!largoOk || !inicioOk) {
            if ((pais && pais.value) === 'CL') {
                return 'Ingresa un móvil chileno de 9 dígitos que empiece con 9, sin repetir el +56.';
            }
            return 'Revisa el teléfono de ' + regla.nombre + '. No repitas el prefijo +' + regla.prefijo + '.';
        }
        return '';
    }

    if (pais) pais.addEventListener('change', placeholder);
    placeholder();

    formulario.addEventListener('submit', function (event) {
        var mensaje = '';
        var textoNombre = (nombre && nombre.value || '').trim();
        if (/\d/.test(textoNombre) || !nombreOk.test(textoNombre)) {
            mensaje = 'El nombre solo puede incluir letras, espacios, guiones y apóstrofes.';
        } else {
            mensaje = telefonoInvalido();
        }
        if (!mensaje) {
            if (aviso) aviso.textContent = '';
            return;
        }
        event.preventDefault();
        if (aviso) aviso.textContent = mensaje;
    });
})();
