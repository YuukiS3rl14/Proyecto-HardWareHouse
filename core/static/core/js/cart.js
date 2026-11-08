document.addEventListener('DOMContentLoaded', function () {
    function stockDe(input) {
        var stock = parseInt(input.dataset.stock, 10);
        return Number.isFinite(stock) ? stock : null;
    }

    function mensajeCantidad(input) {
        var texto = (input.value || '').trim();
        if (texto === '') return 'Ingresa una cantidad.';
        if (!/^[0-9]+$/.test(texto)) return 'La cantidad debe ser un número entero positivo.';
        var cantidad = parseInt(texto, 10);
        if (cantidad < 1) return 'La cantidad mínima es 1.';
        var stock = stockDe(input);
        if (stock !== null && stock < 1) return 'Este producto no tiene stock disponible.';
        if (stock !== null && cantidad > stock) return 'Solo hay ' + stock + ' unidades disponibles.';
        return '';
    }

    function mostrarError(form, texto) {
        var aviso = form.querySelector('[data-cantidad-error]');
        if (aviso) aviso.textContent = texto || '';
        if (texto && window.HW) window.HW.showToast(texto, 'error');
    }

    document.querySelectorAll('form[id^="form-"]').forEach(function (form) {
        var input = form.querySelector('input[name="quantity"]');
        var menos = form.querySelector('.btn-minus');
        var mas = form.querySelector('.btn-plus');
        if (!input || !menos || !mas) return;

        function enviarSiValida(siguiente) {
            input.value = String(siguiente);
            var error = mensajeCantidad(input);
            if (error) {
                input.value = input.dataset.cantidad || '1';
                mostrarError(form, error);
                return;
            }
            mostrarError(form, '');
            menos.disabled = true;
            mas.disabled = true;
            form.submit();
        }

        menos.addEventListener('click', function () {
            var actual = parseInt(input.value, 10);
            if (!Number.isFinite(actual) || actual <= 1) {
                mostrarError(form, 'La cantidad mínima es 1.');
                input.value = input.dataset.cantidad || '1';
                return;
            }
            enviarSiValida(actual - 1);
        });

        mas.addEventListener('click', function () {
            var actual = parseInt(input.value, 10);
            if (!Number.isFinite(actual)) actual = 0;
            var stock = stockDe(input);
            if (stock !== null && actual + 1 > stock) {
                mostrarError(form, 'Solo hay ' + stock + ' unidades disponibles.');
                return;
            }
            enviarSiValida(actual + 1);
        });

        form.addEventListener('submit', function (event) {
            var error = mensajeCantidad(input);
            if (!error) return;
            event.preventDefault();
            input.value = input.dataset.cantidad || '1';
            mostrarError(form, error);
        });
    });
});
