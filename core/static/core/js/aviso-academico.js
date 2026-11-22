(function () {
    'use strict';

    var CLAVE = 'hwh_aviso_academico';
    var nodo = document.getElementById('avisoAcademico');
    var boton = document.getElementById('avisoAcademicoAceptar');
    if (!nodo || !boton || typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        return;
    }

    function aceptado() {
        try {
            return localStorage.getItem(CLAVE) === '1';
        } catch (error) {
            return false;
        }
    }

    function marcar() {
        try {
            localStorage.setItem(CLAVE, '1');
        } catch (error) {}
    }

    function fondoInerte(activo) {
        Array.prototype.forEach.call(document.body.children, function (elemento) {
            if (elemento.id === 'avisoAcademico') {
                return;
            }
            if (activo) {
                elemento.setAttribute('inert', '');
            } else {
                elemento.removeAttribute('inert');
            }
        });
    }

    if (aceptado()) {
        document.documentElement.classList.remove('hw-aviso-pendiente');
        return;
    }

    var modal = new bootstrap.Modal(nodo, {
        backdrop: 'static',
        keyboard: false
    });

    nodo.addEventListener('hide.bs.modal', function (evento) {
        if (!aceptado()) {
            evento.preventDefault();
        }
    });

    boton.addEventListener('click', function () {
        marcar();
        document.documentElement.classList.remove('hw-aviso-pendiente');
        fondoInerte(false);
        modal.hide();
    });

    fondoInerte(true);
    modal.show();
    boton.focus();
})();
