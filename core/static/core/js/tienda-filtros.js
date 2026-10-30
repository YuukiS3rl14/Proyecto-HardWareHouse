(function () {
    function conteo(select) {
        var destino = document.getElementById(select.getAttribute('data-count'));
        if (!destino) {
            return;
        }
        var elegidos = select.selectedOptions ? select.selectedOptions.length : 0;
        destino.textContent = String(elegidos);
    }

    document.querySelectorAll('.js-filtro-multiple').forEach(conteo);

    var formulario = document.getElementById('filtros-catalogo');
    var orden = document.getElementById('orden-catalogo');
    if (formulario) {
        formulario.addEventListener('submit', function () {
            var precio = document.getElementById('filtro-precio');
            if (precio && !precio.value) {
                precio.disabled = true;
            }
            if (orden && orden.value === 'relevancia') {
                orden.disabled = true;
            }
        });
    }
    if (orden && orden.form) {
        orden.addEventListener('change', function () {
            orden.form.submit();
        });
    }

    if (!window.jQuery || !jQuery.fn.select2) {
        return;
    }

    jQuery('.js-filtro-multiple').each(function () {
        var $select = jQuery(this);
        $select.select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: $select.data('placeholder') || 'Todas',
            closeOnSelect: true,
            allowClear: true,
            language: {
                noResults: function () { return 'Sin coincidencias'; },
                searching: function () { return 'Buscando…'; }
            }
        });
        $select.on('change', function () {
            conteo(this);
        });
    });
})();
