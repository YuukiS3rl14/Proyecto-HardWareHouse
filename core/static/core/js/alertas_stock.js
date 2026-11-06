(function () {
    const tabla = document.getElementById('stock-tabla');
    if (!tabla) {
        return;
    }
    const propio = document.currentScript;
    const token = document.querySelector('#umbral-csrf [name=csrfmiddlewaretoken]');
    const destino = propio ? propio.dataset.umbralUrl : '';

    function campo(celda, valor, etiqueta) {
        celda.innerHTML = '';
        const input = document.createElement('input');
        input.className = 'form-control form-control-sm';
        input.type = 'number';
        input.min = '0';
        input.step = '1';
        input.inputMode = 'numeric';
        input.value = valor;
        input.setAttribute('aria-label', etiqueta);
        celda.appendChild(input);
        return input;
    }

    function texto(celda, valor) {
        celda.textContent = valor;
    }

    function cerrar(fila) {
        texto(fila.querySelector('.js-minimo'), fila.dataset.minimo);
        texto(fila.querySelector('.js-advertencia'), fila.dataset.advertencia);
        fila.querySelector('.js-editar').classList.remove('d-none');
        fila.querySelector('.js-acciones-edicion').classList.add('d-none');
        fila.querySelector('.js-error').textContent = '';
        delete fila.dataset.guardando;
    }

    function etiqueta(estado, nombre) {
        const icono = {
            AGOTADO: 'fa-ban',
            CRITICO: 'fa-exclamation-circle',
            ADVERTENCIA: 'fa-exclamation-triangle',
            NORMAL: 'fa-check',
        }[estado] || 'fa-check';
        const clase = {
            AGOTADO: 'badge bg-danger',
            CRITICO: 'badge badge-danger',
            ADVERTENCIA: 'badge badge-warning',
            NORMAL: 'badge bg-success',
        }[estado] || 'badge bg-success';
        return '<span class="' + clase + '"><i class="fas ' + icono + ' mr-1" aria-hidden="true"></i> ' + nombre + '</span>';
    }

    tabla.addEventListener('click', function (evento) {
        const fila = evento.target.closest('tr');
        if (!fila) {
            return;
        }
        if (evento.target.closest('.js-editar')) {
            campo(fila.querySelector('.js-minimo'), fila.dataset.minimo, 'Stock mínimo');
            campo(fila.querySelector('.js-advertencia'), fila.dataset.advertencia, 'Umbral de advertencia');
            fila.querySelector('.js-editar').classList.add('d-none');
            fila.querySelector('.js-acciones-edicion').classList.remove('d-none');
            fila.querySelector('.js-error').textContent = '';
            return;
        }
        if (evento.target.closest('.js-cancelar')) {
            cerrar(fila);
            return;
        }
        const guardar = evento.target.closest('.js-guardar');
        if (!guardar || fila.dataset.guardando === '1') {
            return;
        }
        const minimo = fila.querySelector('.js-minimo input');
        const advertencia = fila.querySelector('.js-advertencia input');
        const error = fila.querySelector('.js-error');
        fila.dataset.guardando = '1';
        guardar.disabled = true;
        const cuerpo = new URLSearchParams({
            modelo: fila.dataset.modelo,
            pk: fila.dataset.pk,
            stock_minimo: minimo ? minimo.value : '',
            stock_advertencia: advertencia ? advertencia.value : '',
            estado: (document.getElementById('estado-stock') || {}).value || 'todos',
            categoria: (document.getElementById('categoria-stock') || {}).value || '',
            q: (document.getElementById('q-stock') || {}).value || '',
        });
        fetch(destino, {
            method: 'POST',
            headers: {
                'X-CSRFToken': token ? token.value : '',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: cuerpo,
        }).then(function (respuesta) {
            return respuesta.json().then(function (datos) {
                return { ok: respuesta.ok, datos: datos };
            });
        }).then(function (resultado) {
            guardar.disabled = false;
            if (!resultado.ok || !resultado.datos.ok) {
                delete fila.dataset.guardando;
                error.textContent = (resultado.datos && resultado.datos.error) || 'No se pudo guardar los umbrales.';
                return;
            }
            const datos = resultado.datos;
            fila.dataset.minimo = String(datos.stock_minimo);
            fila.dataset.advertencia = String(datos.stock_advertencia);
            texto(fila.querySelector('.js-stock'), datos.stock);
            texto(fila.querySelector('.js-unidades'), datos.unidades);
            fila.querySelector('.js-estado').innerHTML = etiqueta(datos.estado, datos.etiqueta);
            Object.keys(datos.resumen || {}).forEach(function (clave) {
                document.querySelectorAll('[data-stock-contador="' + clave + '"]').forEach(function (nodo) {
                    nodo.textContent = datos.resumen[clave];
                });
            });
            document.querySelectorAll('[data-stock-nav]').forEach(function (nodo) {
                nodo.textContent = datos.resumen.afectados;
                nodo.hidden = !datos.resumen.afectados;
            });
            cerrar(fila);
            if (!datos.visible) {
                fila.remove();
                if (!tabla.querySelector('tbody tr')) {
                    tabla.hidden = true;
                    const vacio = document.getElementById('stock-vacio');
                    vacio.hidden = false;
                    vacio.querySelector('[data-vacio="filtros"]').hidden = datos.resumen.afectados === 0;
                    vacio.querySelector('[data-vacio="ok"]').hidden = datos.resumen.afectados !== 0;
                }
            }
        }).catch(function () {
            guardar.disabled = false;
            delete fila.dataset.guardando;
            error.textContent = 'No se pudo guardar los umbrales.';
        });
    });
})();
