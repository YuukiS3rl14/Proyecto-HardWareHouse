(function () {
    function pintar(raiz, valor) {
        var numero = valor === '' || valor === null ? NaN : parseFloat(valor);
        raiz.querySelectorAll('.hw-star').forEach(function (estrella) {
            var completa = parseFloat(estrella.getAttribute('data-full'));
            estrella.classList.remove('is-full', 'is-half', 'is-empty');
            if (Number.isNaN(numero)) estrella.classList.add('is-empty');
            else if (numero >= completa) estrella.classList.add('is-full');
            else if (numero + 0.001 >= completa - 0.5) estrella.classList.add('is-half');
            else estrella.classList.add('is-empty');
        });
        var texto = raiz.querySelector('.hw-rating-text');
        if (!texto) return;
        texto.textContent = Number.isNaN(numero)
            ? 'Selecciona una calificación'
            : String(valor).replace('.', ',') + ' de 5 estrellas';
    }

    function seleccionado(raiz) {
        var marcado = raiz.querySelector('input[type="radio"]:checked');
        return marcado ? marcado.value : '';
    }

    document.querySelectorAll('[data-estrellas]').forEach(function (raiz) {
        pintar(raiz, seleccionado(raiz));
        var fino = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
        raiz.querySelectorAll('.hw-star-hit').forEach(function (zona) {
            if (!fino) return;
            zona.addEventListener('mouseenter', function () {
                var input = document.getElementById(zona.getAttribute('for'));
                if (input) pintar(raiz, input.value);
            });
        });
        raiz.addEventListener('mouseleave', function () {
            if (fino) pintar(raiz, seleccionado(raiz));
        });
        raiz.querySelectorAll('input[type="radio"]').forEach(function (input) {
            input.addEventListener('change', function () {
                pintar(raiz, input.value);
            });
        });
    });

    document.querySelectorAll('[data-contador]').forEach(function (campo) {
        var aviso = document.getElementById(campo.getAttribute('data-contador'));
        if (!aviso) return;
        var maximo = parseInt(campo.getAttribute('maxlength'), 10);
        function actualizar() {
            var largo = campo.value.length;
            aviso.textContent = largo >= maximo
                ? 'Llegaste al máximo de ' + maximo + ' caracteres.'
                : largo + '/' + maximo;
        }
        campo.addEventListener('input', actualizar);
        actualizar();
    });
})();
