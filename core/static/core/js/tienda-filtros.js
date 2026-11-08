(function () {
    function conteo(select) {
        var destino = document.getElementById(select.getAttribute('data-count'));
        if (!destino) {
            return;
        }
        var elegidos = 0;
        if (select.multiple) {
            elegidos = select.selectedOptions ? select.selectedOptions.length : 0;
        } else if (select.value) {
            elegidos = 1;
        }
        destino.textContent = String(elegidos);
    }

    function valor(id) {
        var campo = document.getElementById(id);
        return campo && campo.value ? campo.value : '';
    }

    function oculto(nombre) {
        if (!formulario) {
            return '';
        }
        var campo = formulario.querySelector('input[name="' + nombre + '"]');
        return campo && campo.value ? campo.value : '';
    }

    document.querySelectorAll('.js-filtro-catalogo').forEach(conteo);

    var formulario = document.getElementById('filtros-catalogo');
    var orden = document.getElementById('orden-catalogo');
    if (formulario) {
        formulario.addEventListener('submit', function (event) {
            event.preventDefault();
            var params = new URLSearchParams();
            var consulta = oculto('q');
            var categoria = valor('filtro-categoria');
            var proveedor = valor('filtro-marca');
            var precio = valor('filtro-precio');
            var ordenValor = orden && orden.value && orden.value !== 'relevancia' ? orden.value : '';
            var desdeHome = oculto('origen') === 'home';
            params.delete('q');
            params.delete('categoria');
            params.delete('proveedor');
            params.delete('precio');
            params.delete('orden');
            params.delete('origen');
            params.delete('page');
            if (desdeHome) {
                var cambioCategoria = categoria !== oculto('heredado_categoria');
                var cambioProveedor = proveedor !== oculto('heredado_proveedor');
                if (cambioCategoria || cambioProveedor) {
                    if (consulta === oculto('heredado_q')) {
                        consulta = '';
                    }
                    if (!cambioCategoria) {
                        categoria = '';
                    }
                    if (!cambioProveedor) {
                        proveedor = '';
                    }
                    desdeHome = false;
                }
            }
            if (consulta) {
                params.set('q', consulta);
            }
            if (categoria) {
                params.set('categoria', categoria);
            }
            if (proveedor) {
                params.set('proveedor', proveedor);
            }
            if (precio) {
                params.set('precio', precio);
            }
            if (ordenValor) {
                params.set('orden', ordenValor);
            }
            if (oculto('novedades') === '1') {
                params.set('novedades', '1');
            }
            if (desdeHome) {
                params.set('origen', 'home');
            } else {
                params.delete('origen');
            }
            var destino = formulario.getAttribute('action') || window.location.pathname;
            var consultaUrl = params.toString();
            window.location.assign(consultaUrl ? destino + '?' + consultaUrl : destino);
        });
    }

    var panel = document.getElementById('panel-filtros');
    var abrir = document.getElementById('abrir-filtros');
    var cerrarBtn = document.getElementById('cerrar-filtros');
    var overlay = document.getElementById('filtros-overlay');

    function esMovil() {
        return window.matchMedia('(max-width: 991.98px)').matches;
    }

    function panelAbierto() {
        return panel && panel.classList.contains('is-open');
    }

    function abrirPanel() {
        if (!panel || !esMovil()) return;
        panel.classList.add('is-open');
        if (overlay) overlay.hidden = false;
        if (abrir) abrir.setAttribute('aria-expanded', 'true');
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-modal', 'true');
        panel.setAttribute('aria-label', 'Filtros');
        if (cerrarBtn) cerrarBtn.focus();
    }

    function cerrarPanel(devolverFoco) {
        if (!panel) return;
        panel.classList.remove('is-open');
        if (overlay) overlay.hidden = true;
        if (abrir) abrir.setAttribute('aria-expanded', 'false');
        panel.removeAttribute('role');
        panel.removeAttribute('aria-modal');
        if (devolverFoco && abrir) abrir.focus();
    }

    if (abrir) abrir.addEventListener('click', abrirPanel);
    if (cerrarBtn) cerrarBtn.addEventListener('click', function () { cerrarPanel(true); });
    if (overlay) overlay.addEventListener('click', function () { cerrarPanel(true); });

    document.addEventListener('keydown', function (event) {
        if (!panelAbierto() || !esMovil()) return;
        if (event.key === 'Escape') {
            event.preventDefault();
            cerrarPanel(true);
            return;
        }
        if (event.key !== 'Tab' || !panel) return;
        var focos = panel.querySelectorAll('button, [href], select, input, textarea, [tabindex]:not([tabindex="-1"])');
        if (!focos.length) return;
        var primero = focos[0];
        var ultimo = focos[focos.length - 1];
        if (event.shiftKey && document.activeElement === primero) {
            event.preventDefault();
            ultimo.focus();
        } else if (!event.shiftKey && document.activeElement === ultimo) {
            event.preventDefault();
            primero.focus();
        }
    });

    window.addEventListener('resize', function () {
        if (!esMovil() && panelAbierto()) cerrarPanel(false);
    });

    if (!window.jQuery || !jQuery.fn.select2) {
        return;
    }

    jQuery('.js-filtro-catalogo').each(function () {
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
