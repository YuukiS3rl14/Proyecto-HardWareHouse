function iniciarArmado() {
    // --- 1. OBTENER DATOS Y ELEMENTOS DEL DOM ---
    const allComponentsData = JSON.parse(document.getElementById('componentes-data').textContent);
    const imagenesCategoria = JSON.parse(document.getElementById('imagenes-categoria').textContent);
    const urls = document.getElementById('builder-urls').dataset;

    function imagenComponente(component, clave) {
        if (component && component.imagen) {
            return component.imagen;
        }
        return imagenesCategoria[clave] || '';
    }
    const builderContainer = document.getElementById('pc-builder');
    const summaryList = document.getElementById('summary-list');
    const totalPriceEl = document.getElementById('total-price');
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    const downloadExcelBtn = document.getElementById('download-excel-btn');

    // Estado actual de la construcción y de la última consulta vigente.
    let currentBuild = {};
    let discos = [];
    let memorias = [];
    let evaluacionActual = null;
    let modoModal = '';
    let reemplazaId = null;
    let consultaSerial = 0;

    // Orden y etiquetas de los componentes
    const componentOrder = [
        { key: 'placa_madre', label: 'Placa Madre', modelName: 'placa_madre' },
        { key: 'procesador', label: 'Procesador (CPU)', modelName: 'procesador' },
        { key: 'memoria_ram', label: 'Memoria RAM', modelName: 'memoria_ram' },
        { key: 'refrigeracion_cooler', label: 'Refrigeración CPU', modelName: 'refrigeracion' },
        { key: 'tarjeta_grafica', label: 'Tarjeta Gráfica (GPU)', modelName: 'tarjeta_grafica' },
        { key: 'almacenamiento', label: 'Almacenamiento', modelName: 'almacenamiento_ssd' },
        { key: 'gabinete', label: 'Gabinete', modelName: 'gabinete' },
        { key: 'fuente_de_poder', label: 'Fuente de Poder', modelName: 'fuente_de_poder' },
    ];

    // --- 2. INICIALIZAR LA INTERFAZ ---
    function initializeBuilder() {
        desecharPopovers(builderContainer);
        builderContainer.innerHTML = '<div class="row"></div>'; // Crear una fila para la rejilla
        const gridRow = builderContainer.querySelector('.row');

        componentOrder.forEach(({ key, label }) => {
            const component = currentBuild[key];
            const cardHTML = createComponentCardHTML(key, label, component);
            gridRow.insertAdjacentHTML('beforeend', cardHTML);
        });

        // Añadir listeners a los nuevos botones
        document.querySelectorAll('.select-component-btn').forEach(btn => {
            btn.addEventListener('click', openComponentModal);
        });
        document.querySelectorAll('.remove-component-btn').forEach(btn => {
            btn.addEventListener('click', handleRemoveComponent);
        });
        document.querySelectorAll('.quitar-disco-btn').forEach(btn => {
            btn.addEventListener('click', quitarDisco);
        });
        document.querySelectorAll('.cantidad-disco').forEach(input => {
            input.addEventListener('change', cambiarCantidadDisco);
        });
        document.querySelectorAll('.quitar-ram-btn').forEach(btn => {
            btn.addEventListener('click', quitarRam);
        });
        document.querySelectorAll('.cantidad-ram').forEach(input => {
            input.addEventListener('change', cambiarCantidadRam);
        });

        montarPopovers(builderContainer);
        updateSummaryAndTotal();
    }

    function htmlAlmacenamiento(label) {
        const hay = discos.length > 0;
        const detalle = hay ? htmlEstadoTarjeta('almacenamiento', label) : '';
        const totalDiscos = discos.reduce((suma, disco) => suma + parseFloat(disco.precio) * disco.cantidad, 0);
        const precio = hay ? `$${totalDiscos.toLocaleString('es-CL')}` : '-';
        const lineas = hay ? discos.map(disco => {
            const subtotal = parseFloat(disco.precio) * disco.cantidad;
            return `
                <div class="border-top pt-2 mt-2">
                    <p class="mb-1 small">${escaparHtml(disco.nombre)}</p>
                    <ul class="list-unstyled spec-list mb-1">${getComponentSpecs(disco, true)}</ul>
                    <div class="d-flex align-items-center justify-content-between">
                        <label class="small mb-0">Cantidad
                            <input type="number" min="1" max="${disco.stock}" step="1" class="form-control form-control-sm cantidad-disco d-inline-block ml-1" style="width: 4.5rem;" data-model-name="${escaparHtml(disco.model_name)}" data-id="${disco.id}" value="${disco.cantidad}">
                        </label>
                        <strong class="small">$${subtotal.toLocaleString('es-CL')}</strong>
                        <button type="button" class="btn btn-sm btn-outline-danger quitar-disco-btn" data-model-name="${escaparHtml(disco.model_name)}" data-id="${disco.id}">Quitar</button>
                    </div>
                </div>`;
        }).join('') : '<p class="mb-1 small">No seleccionado</p><ul class="list-unstyled spec-list mb-0"><li>Puedes combinar SSD y HDD</li></ul>';
        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="component-card-wrapper">
                    <div class="component-card">
                        <div class="info">
                            <h5 class="font-weight-bold">${label}</h5>
                            <img src="${hay ? (discos[0].imagen || imagenesCategoria.almacenamiento) : imagenesCategoria.almacenamiento}" alt="Almacenamiento">
                            ${lineas}
                            ${detalle}
                        </div>
                        <div class="actions">
                            <h5 class="font-weight-bold mb-3">${precio}</h5>
                            <div class="d-grid gap-2">
                                <button class="btn btn-sm btn-outline-success select-component-btn" data-type="almacenamiento">Agregar</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function htmlMemorias(label) {
        const hay = memorias.length > 0;
        const detalle = hay ? htmlEstadoTarjeta('memoria_ram', label) : '';
        const totalRam = memorias.reduce((suma, ram) => suma + parseFloat(ram.precio) * ram.cantidad, 0);
        const precio = hay ? `$${totalRam.toLocaleString('es-CL')}` : '-';
        const lineas = hay ? memorias.map(ram => {
            const subtotal = parseFloat(ram.precio) * ram.cantidad;
            return `
                <div class="border-top pt-2 mt-2">
                    <p class="mb-1 small">${escaparHtml(ram.nombre)}</p>
                    <ul class="list-unstyled spec-list mb-1">${getComponentSpecs(ram, true)}</ul>
                    <div class="d-flex align-items-center justify-content-between">
                        <label class="small mb-0">Cantidad
                            <input type="number" min="1" max="${ram.stock}" step="1" class="form-control form-control-sm cantidad-ram d-inline-block ml-1" style="width: 4.5rem;" data-id="${ram.id}" value="${ram.cantidad}">
                        </label>
                        <strong class="small">$${subtotal.toLocaleString('es-CL')}</strong>
                        <button type="button" class="btn btn-sm btn-outline-secondary select-component-btn" data-type="memoria_ram" data-modo="reemplazar" data-reemplaza-id="${ram.id}">Editar</button>
                        <button type="button" class="btn btn-sm btn-outline-danger quitar-ram-btn" data-id="${ram.id}">Quitar</button>
                    </div>
                </div>`;
        }).join('') : '<p class="mb-1 small">No seleccionado</p><ul class="list-unstyled spec-list mb-0"><li>Puedes combinar módulos y kits</li></ul>';
        const conteo = hay ? `<p class="mb-0 text-muted"><small>${escaparHtml(textoConteoRam())}</small></p>` : '';
        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="component-card-wrapper">
                    <div class="component-card">
                        <div class="info">
                            <h5 class="font-weight-bold">${label}</h5>
                            <img src="${hay ? (memorias[0].imagen || imagenesCategoria.memoria_ram) : imagenesCategoria.memoria_ram}" alt="Memoria RAM">
                            ${lineas}
                            ${conteo}
                            ${detalle}
                        </div>
                        <div class="actions">
                            <h5 class="font-weight-bold mb-3">${precio}</h5>
                            <div class="d-grid gap-2">
                                <button class="btn btn-sm btn-outline-success select-component-btn" data-type="memoria_ram" data-modo="agregar">Agregar</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    function textoConteoRam() {
        let modulos = 0;
        let capacidad = 0;
        let faltaModulos = false;
        let faltaCapacidad = false;
        memorias.forEach(ram => {
            const cantidad = Number(ram.cantidad);
            if (ram.modulos_por_producto) {
                modulos += Number(ram.modulos_por_producto) * cantidad;
            } else {
                faltaModulos = true;
            }
            if (ram.capacidad_gb) {
                capacidad += Number(ram.capacidad_gb) * cantidad;
            } else {
                faltaCapacidad = true;
            }
        });
        const textoModulos = faltaModulos ? 'módulos sin dato' : `${modulos} módulos`;
        const textoCapacidad = faltaCapacidad ? 'capacidad sin dato' : `${capacidad} GB`;
        return `${textoModulos} · ${textoCapacidad} en total`;
    }

    function createComponentCardHTML(key, label, component) {
        if (key === 'memoria_ram') {
            return htmlMemorias(label);
        }
        if (key === 'almacenamiento') {
            return htmlAlmacenamiento(label);
        }
        const price = component ? `$${parseInt(component.precio).toLocaleString('es-CL')}` : '-';
        const name = component ? component.nombre : `No seleccionado`;
        const image = imagenComponente(component, key);

        const compatibilityDetail = component ? htmlEstadoTarjeta(key, label) : '';

        // Generar lista de especificaciones clave
        const specs = component ? getComponentSpecs(component, true) : '<li>Selecciona un producto</li>';

        return `
            <div class="col-sm-6 col-xl-4 mb-4">
                <div class="component-card-wrapper">
                    <div class="component-card">
                        <div class="info">
                            <h5 class="font-weight-bold">${label}</h5>
                            <img src="${image}" alt="${name}">
                            <p class="mb-1 small text-truncate">${name}</p>
                            <ul class="list-unstyled spec-list mb-0">${specs}</ul>
                            ${compatibilityDetail}
                        </div>
                        <div class="actions">
                            <h5 class="font-weight-bold mb-3">${price}</h5>
                            <div class="d-grid gap-2">
                                <button class="btn btn-sm btn-outline-success select-component-btn" data-type="${key}">
                                    ${component ? 'Cambiar' : 'Seleccionar'}
                                </button>
                                ${component ? `<button class="btn btn-sm btn-outline-danger remove-component-btn" data-type="${key}">Quitar</button>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // --- 3. MANEJO DE EVENTOS Y LÓGICA DE COMPATIBILIDAD ---

    let soloCompatibles = false;
    let filtrosActivos = {};
    let recomendacionesActuales = [];
    let categoriaModal = null;
    const MENSAJE_FALTAN = 'Faltan componentes por seleccionar';
    const MENSAJE_SIN_FILTROS = 'No se encontraron productos con estos filtros';

    function escaparHtml(texto) {
        return String(texto ?? '').replace(/[&<>"']/g, caracter => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        }[caracter]));
    }

    function seleccionActual() {
        const piezas = Object.entries(currentBuild).map(([type, component]) => {
            const { modelName } = componentOrder.find(c => c.key === type);
            return {
                tipo: component.model_name || modelName,
                id: component.id,
            };
        });
        discos.forEach(disco => {
            piezas.push({
                tipo: disco.model_name,
                id: disco.id,
                cantidad: disco.cantidad,
            });
        });
        memorias.forEach(ram => {
            piezas.push({
                tipo: 'memoria_ram',
                id: ram.id,
                cantidad: ram.cantidad,
            });
        });
        return piezas;
    }

    function modalComponente() {
        return bootstrap.Modal.getOrCreateInstance(document.getElementById('componentModal'));
    }

    async function openComponentModal(e) {
        const type = e.target.dataset.type;
        const modalTitle = document.getElementById('componentModalLabel');
        const modalBody = document.getElementById('componentModalBody');
        const { label } = componentOrder.find(c => c.key === type);
        categoriaModal = type;
        filtrosActivos = {};
        modoModal = e.target.dataset.modo || '';
        reemplazaId = e.target.dataset.reemplazaId || null;
        modalTitle.textContent = modoModal === 'reemplazar' ? `Reemplazar ${label}` : `Seleccionar ${label}`;
        modalBody.innerHTML = '<p class="text-muted mb-0">Revisando compatibilidad...</p>';
        modalComponente().show();

        const cuerpo = {
            categoria: type,
            componentes: seleccionActual(),
        };
        if (type === 'memoria_ram') {
            cuerpo.modo = modoModal || 'agregar';
            if (cuerpo.modo === 'reemplazar') {
                cuerpo.reemplaza_id = Number(reemplazaId);
            }
        }
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        try {
            const response = await fetch(urls.recomendarUrl, {
                method: 'POST',
                body: JSON.stringify(cuerpo),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfInput ? csrfInput.value : '',
                },
            });
            const data = await response.json();
            if (!response.ok || data.status !== 'success') {
                modalBody.innerHTML = `<p class="text-danger mb-0">${escaparHtml(data.message || 'No se pudo recomendar.')}</p>`;
                return;
            }
            recomendacionesActuales = data.candidatos;
            renderRecomendaciones();
        } catch (error) {
            console.error('Error al recomendar:', error);
            modalBody.innerHTML = '<p class="text-danger mb-0">No se pudo consultar la compatibilidad.</p>';
        }
    }

    const FILTROS_MODAL = {
        procesador: [
            { id: 'marca', label: 'Marca', leer: producto => producto.marca },
            { id: 'socket', label: 'Socket', leer: producto => producto.socket },
            { id: 'nucleos', label: 'Núcleos', leer: producto => producto.nucleos, orden: 'numero' },
            { id: 'frecuencia', label: 'Frecuencia', leer: producto => producto.frecuencia_base, etiqueta: valor => `${textoNumero(valor)} GHz`, orden: 'numero' },
        ],
        placa_madre: [
            { id: 'socket', label: 'Socket', leer: producto => producto.socket_cpu },
            { id: 'chipset', label: 'Chipset', leer: producto => producto.chipset },
            { id: 'ddr', label: 'DDR', leer: producto => producto.tipo_ram_soportado },
            { id: 'formato', label: 'Formato', leer: producto => producto.formato },
        ],
        memoria_ram: [
            { id: 'ddr', label: 'DDR', leer: producto => producto.tipo_ddr },
            { id: 'capacidad', label: 'Capacidad', leer: producto => producto.capacidad_gb, etiqueta: valor => `${textoNumero(valor)} GB`, orden: 'numero' },
            { id: 'frecuencia', label: 'Frecuencia', leer: producto => producto.velocidad_mhz, etiqueta: valor => `${textoNumero(valor)} MHz`, orden: 'numero' },
            { id: 'formato', label: 'Formato', leer: producto => producto.formato_ram },
        ],
        tarjeta_grafica: [
            { id: 'marca', label: 'Marca', leer: producto => producto.marca },
            { id: 'vram', label: 'VRAM', leer: producto => producto.vram_gb, etiqueta: valor => `${textoNumero(valor)} GB`, orden: 'numero' },
            { id: 'consumo', label: 'Consumo', leer: producto => producto.consumo_referencia_watts, etiqueta: valor => `${textoNumero(valor)} W`, orden: 'numero' },
            { id: 'longitud', label: 'Longitud', leer: producto => producto.largo_mm, etiqueta: valor => `${textoNumero(valor)} mm`, orden: 'numero' },
        ],
        fuente_de_poder: [
            { id: 'potencia', label: 'Potencia', leer: producto => producto.potencia_watts, etiqueta: valor => `${textoNumero(valor)} W`, orden: 'numero' },
            { id: 'certificacion', label: 'Certificación', leer: producto => producto.certificacion },
            { id: 'modularidad', label: 'Modularidad', leer: producto => textoModular(producto.modular) },
        ],
        gabinete: [
            { id: 'formato', label: 'Formato', leer: producto => producto.formato_soporte },
            { id: 'largo_gpu', label: 'Longitud máxima de GPU', leer: producto => producto.largo_max_gpu_mm, etiqueta: valor => `${textoNumero(valor)} mm`, orden: 'numero' },
        ],
        refrigeracion_cooler: [
            { id: 'socket', label: 'Socket compatible', tokens: producto => tokensSocket(producto.socket_compatibles) },
            { id: 'tipo', label: 'Tipo', leer: producto => producto.tipo },
        ],
        almacenamiento: [
            { id: 'tipo', label: 'Tipo', leer: producto => textoTipoDisco(producto.model_name) },
            { id: 'capacidad', label: 'Capacidad', leer: producto => producto.capacidad_gb, etiqueta: valor => `${textoNumero(valor)} GB`, orden: 'numero' },
            { id: 'interfaz', label: 'Interfaz', leer: producto => producto.interfaz },
        ],
    };

    function textoNumero(valor) {
        const numero = Number(valor);
        return Number.isFinite(numero) ? String(numero) : String(valor);
    }

    function textoModular(valor) {
        if (valor === true || valor === 'true') {
            return 'Modular';
        }
        if (valor === false || valor === 'false') {
            return 'No modular';
        }
        return null;
    }

    function textoTipoDisco(modelName) {
        if (modelName === 'almacenamiento_ssd') {
            return 'SSD';
        }
        if (modelName === 'almacenamiento_hdd') {
            return 'HDD';
        }
        return null;
    }

    function tokensSocket(valor) {
        return String(valor || '').split(',').map(token => token.trim()).filter(Boolean);
    }

    function claveFiltro(filtro, valor) {
        if (valor === null || valor === undefined || valor === '') {
            return null;
        }
        if (filtro.orden === 'numero') {
            const numero = Number(valor);
            return Number.isFinite(numero) ? String(numero) : null;
        }
        return String(valor);
    }

    function productoDeCandidato(candidato) {
        const local = (allComponentsData[categoriaModal] || []).find(componente => (
            String(componente.id) === String(candidato.id) && componente.model_name === candidato.model_name
        ));
        return local || candidato;
    }

    function opcionesFiltro(filtro, productos) {
        const vistos = new Map();
        productos.forEach(producto => {
            const valores = filtro.tokens ? filtro.tokens(producto) : [filtro.leer(producto)];
            valores.forEach(valor => {
                const clave = claveFiltro(filtro, valor);
                if (clave === null || vistos.has(clave)) {
                    return;
                }
                vistos.set(clave, filtro.etiqueta ? filtro.etiqueta(valor) : String(valor));
            });
        });
        return [...vistos.entries()].sort((a, b) => {
            if (filtro.orden === 'numero') {
                return Number(a[0]) - Number(b[0]);
            }
            return a[1].localeCompare(b[1], 'es');
        });
    }

    function productoPasaFiltros(producto) {
        const definiciones = FILTROS_MODAL[categoriaModal] || [];
        return definiciones.every(filtro => {
            const elegido = filtrosActivos[filtro.id];
            if (!elegido) {
                return true;
            }
            if (filtro.tokens) {
                return filtro.tokens(producto).some(token => claveFiltro(filtro, token) === elegido);
            }
            return claveFiltro(filtro, filtro.leer(producto)) === elegido;
        });
    }

    function htmlFiltros(productos) {
        const definiciones = (FILTROS_MODAL[categoriaModal] || [])
            .map(filtro => ({ filtro, opciones: opcionesFiltro(filtro, productos) }))
            .filter(item => item.opciones.length > 0);
        if (definiciones.length === 0) {
            return '';
        }
        const selects = definiciones.map(({ filtro, opciones }) => {
            const actual = filtrosActivos[filtro.id] || '';
            const choices = opciones.map(([clave, etiqueta]) => (
                `<option value="${escaparHtml(clave)}"${clave === actual ? ' selected' : ''}>${escaparHtml(etiqueta)}</option>`
            )).join('');
            return `
                <div class="col-6 col-md-4 col-xl-3">
                    <label class="form-label" for="filtro-armado-${filtro.id}">${escaparHtml(filtro.label)}</label>
                    <select class="form-select form-select-sm" id="filtro-armado-${filtro.id}" data-filtro="${filtro.id}">
                        <option value="">Todos</option>
                        ${choices}
                    </select>
                </div>
            `;
        }).join('');
        return `
            <div class="armado-filtros border-bottom pb-3 mb-3">
                <div class="row g-2 align-items-end">
                    ${selects}
                    <div class="col-12 col-md-auto">
                        <button type="button" class="btn btn-outline-secondary btn-sm w-100" id="limpiar-filtros-armado">Limpiar filtros</button>
                    </div>
                </div>
            </div>
        `;
    }

    function hayFiltrosActivos() {
        return soloCompatibles || Object.values(filtrosActivos).some(Boolean);
    }

    function renderRecomendaciones() {
        const modalBody = document.getElementById('componentModalBody');
        const productos = recomendacionesActuales.map(productoDeCandidato);
        const visibles = recomendacionesActuales.filter((candidato, indice) => {
            if (soloCompatibles && candidato.estado !== 'compatible') {
                return false;
            }
            return productoPasaFiltros(productos[indice]);
        });

        let html = `
            <div class="armado-modal-controles">
                ${htmlFiltros(productos)}
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" id="solo-compatibles" ${soloCompatibles ? 'checked' : ''}>
                    <label class="form-check-label" for="solo-compatibles">Solo compatibles</label>
                </div>
            </div>
            <div class="armado-lista-resultados">
        `;

        if (visibles.length === 0) {
            html += htmlListaVacia();
        } else {
            html += '<div class="list-group">';
            visibles.forEach(candidato => {
                const local = productoDeCandidato(candidato);
                const price = parseInt(local.precio).toLocaleString('es-CL');
                const image = local.imagen || imagenesCategoria[categoriaModal] || '';
                const detalle = detalleRecomendacion(candidato, local);
                const etiquetaStock = candidato.seleccionable ? '' : '<span class="badge badge-secondary ml-2">Sin stock</span>';
                const clase = candidato.seleccionable ? 'list-group-item list-group-item-action' : 'list-group-item disabled';
                const accion = candidato.seleccionable ? ' role="button" tabindex="0"' : '';
                html += `
                    <div class="${clase} armado-opcion" data-id="${candidato.id}" data-type="${categoriaModal}" data-model-name="${escaparHtml(candidato.model_name)}" data-seleccionable="${candidato.seleccionable ? '1' : '0'}"${accion}>
                        <div class="d-flex w-100">
                            <img src="${escaparHtml(image)}" alt="${escaparHtml(local.nombre)}" style="width: 60px; height: 60px; object-fit: contain; margin-right: 15px;">
                            <div class="flex-grow-1 min-w-0">
                                <div class="d-flex justify-content-between gap-2">
                                    <h6 class="mb-1 armado-opcion-nombre">${escaparHtml(local.nombre)}${etiquetaStock}</h6>
                                    <strong class="armado-opcion-precio flex-shrink-0">$${price}</strong>
                                </div>
                                ${detalle}
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        html += '</div>';
        modalBody.innerHTML = html;
        const filtro = document.getElementById('solo-compatibles');
        if (filtro) {
            filtro.addEventListener('change', () => {
                soloCompatibles = filtro.checked;
                renderRecomendaciones();
            });
        }
        modalBody.querySelectorAll('[data-seleccionable="1"]').forEach(item => {
            item.addEventListener('click', activarSeleccion);
            item.addEventListener('keydown', activarSeleccion);
        });
        modalBody.querySelectorAll('[data-filtro]').forEach(select => {
            select.addEventListener('change', () => {
                filtrosActivos[select.dataset.filtro] = select.value;
                renderRecomendaciones();
            });
        });
        const limpiar = document.getElementById('limpiar-filtros-armado');
        if (limpiar) {
            limpiar.addEventListener('click', () => {
                filtrosActivos = {};
                soloCompatibles = false;
                renderRecomendaciones();
            });
        }
    }

    function htmlListaVacia() {
        if (recomendacionesActuales.length === 0) {
            return '<p class="text-muted mb-0">No hay piezas en esta categoría.</p>';
        }
        if (hayFiltrosActivos()) {
            return `<p class="text-muted mb-0">${MENSAJE_SIN_FILTROS}</p>`;
        }
        return '<p class="text-muted mb-0">No hay piezas en esta categoría.</p>';
    }

    function activarSeleccion(evento) {
        if (evento.type === 'keydown' && evento.key !== 'Enter' && evento.key !== ' ') {
            return;
        }
        if (evento.target.closest('.armado-detalles')) {
            return;
        }
        handleSelectionChange(evento);
    }

    function tokenSpec(texto) {
        return String(texto || '')
            .toLowerCase()
            .replace(/\s+/g, '')
            .replace(/(gb|mhz|ghz|mm|w)$/, '');
    }

    function specYaVisible(linea, principales) {
        const valor = linea.includes(':') ? linea.split(':').slice(1).join(':').trim() : linea;
        const token = tokenSpec(valor);
        if (!token) {
            return true;
        }
        return principales.some(parte => tokenSpec(parte) === token);
    }

    function caracteristicasPrincipales(producto) {
        const partes = [];
        const agregar = (valor, formatear) => {
            if (valor === null || valor === undefined || valor === '') {
                return;
            }
            partes.push(formatear ? formatear(valor) : String(valor));
        };
        if (categoriaModal === 'memoria_ram') {
            agregar(producto.tipo_ddr);
            agregar(producto.capacidad_gb, valor => `${textoNumero(valor)} GB`);
            agregar(producto.velocidad_mhz, valor => `${textoNumero(valor)} MHz`);
            agregar(producto.formato_ram);
        } else if (categoriaModal === 'procesador') {
            agregar(producto.socket);
            agregar(producto.nucleos, valor => `${textoNumero(valor)} núcleos`);
            agregar(producto.frecuencia_base, valor => `${textoNumero(valor)} GHz`);
        } else if (categoriaModal === 'placa_madre') {
            agregar(producto.socket_cpu);
            agregar(producto.chipset);
            agregar(producto.tipo_ram_soportado);
            agregar(producto.formato);
        } else if (categoriaModal === 'tarjeta_grafica') {
            agregar(producto.vram_gb, valor => `${textoNumero(valor)} GB`);
            agregar(producto.largo_mm, valor => `${textoNumero(valor)} mm`);
            agregar(producto.consumo_referencia_watts, valor => `${textoNumero(valor)} W`);
        } else if (categoriaModal === 'fuente_de_poder') {
            agregar(producto.potencia_watts, valor => `${textoNumero(valor)} W`);
            agregar(producto.certificacion);
            agregar(textoModular(producto.modular));
        } else if (categoriaModal === 'gabinete') {
            agregar(producto.formato_soporte);
            agregar(producto.largo_max_gpu_mm, valor => `GPU máx. ${textoNumero(valor)} mm`);
        } else if (categoriaModal === 'refrigeracion_cooler') {
            agregar(producto.tipo);
            agregar(producto.socket_compatibles);
        } else if (categoriaModal === 'almacenamiento') {
            agregar(textoTipoDisco(producto.model_name));
            agregar(producto.capacidad_gb, valor => `${textoNumero(valor)} GB`);
            agregar(producto.interfaz);
            agregar(producto.formato);
        }
        return partes;
    }

    function specsSecundarias(producto, principales) {
        return lineasEspecificacion(producto).filter(linea => !specYaVisible(linea, principales));
    }

    function textosServidor(candidato) {
        const textos = [];
        const agregar = (valor) => {
            const limpio = String(valor || '').trim();
            if (limpio && !textos.includes(limpio)) {
                textos.push(limpio);
            }
        };
        const coincidencias = candidato.coincidencias || [];
        const resumen = coincidencias.length ? `Coincide: ${coincidencias.join(', ')}` : '';
        if (candidato.etiqueta && candidato.etiqueta !== resumen) {
            agregar(candidato.etiqueta);
        }
        coincidencias.forEach(agregar);
        (candidato.motivos || []).forEach(agregar);
        (candidato.pendientes || []).forEach(agregar);
        (candidato.advertencias || []).forEach(agregar);
        if ((candidato.pendientes || []).length) {
            agregar(MENSAJE_FALTAN);
        }
        return textos;
    }

    function estadoVisual(candidato) {
        if (candidato.estado === 'compatible') {
            return { texto: 'Compatible', clase: 'armado-estado-ok', motivo: false };
        }
        if (candidato.estado === 'incompatible') {
            return { texto: 'Incompatible', clase: 'armado-estado-no', motivo: true };
        }
        if (candidato.estado === 'datos_insuficientes') {
            return { texto: 'No verificada', clase: 'armado-estado-revisar', motivo: true };
        }
        if (candidato.estado === 'incompleto') {
            return { texto: 'Disponible', clase: 'armado-estado-disponible', motivo: false };
        }
        if (candidato.estado === 'no_evaluada' && categoriaModal === 'almacenamiento' && !currentBuild.placa_madre) {
            return { texto: 'Disponible', clase: 'armado-estado-disponible', motivo: false };
        }
        return { texto: 'No verificada', clase: 'armado-estado-revisar', motivo: true };
    }

    function detalleRecomendacion(candidato, producto) {
        const visual = estadoVisual(candidato);
        const estado = `<p class="armado-estado-badge ${visual.clase} mb-0">${escaparHtml(visual.texto)}</p>`;
        const principales = producto ? caracteristicasPrincipales(producto) : [];
        const secundarias = producto ? specsSecundarias(producto, principales) : [];
        const textos = textosServidor(candidato);
        const specs = principales.length
            ? `<p class="armado-specs mb-0">${escaparHtml(principales.join(' · '))}</p>`
            : '';
        if (secundarias.length === 0 && textos.length === 0) {
            return `${specs}${estado}`;
        }
        const titulo = visual.motivo ? 'Ver motivo' : 'Ver detalles';
        const listaSpecs = secundarias.map(linea => `<li>${escaparHtml(linea)}</li>`).join('');
        const listaTextos = textos.map(texto => `<p class="armado-detalle-texto">${escaparHtml(texto)}</p>`).join('');
        return `
            ${specs}
            ${estado}
            <details class="armado-detalles">
                <summary>${titulo}</summary>
                ${listaSpecs ? `<ul class="armado-detalle-specs">${listaSpecs}</ul>` : ''}
                ${listaTextos}
            </details>
        `;
    }

    function getComponentSpecs(component, isCard) {
        const specs = lineasEspecificacion(component);
        return isCard ? specs.map(s => `<li>${s}</li>`).join('') : specs.join(' | ');
    }

    function lineasEspecificacion(component) {
        let specs = [];
        // Procesador
        if (component.socket) specs.push(`Socket: ${component.socket}`);
        if (component.nucleos) specs.push(`Núcleos: ${component.nucleos}`);
        if (component.frecuencia_base) specs.push(`Frecuencia: ${component.frecuencia_base}GHz`);
        // Placa Madre
        if (component.socket_cpu) specs.push(`Socket: ${component.socket_cpu}`);
        if (component.chipset) specs.push(`Chipset: ${component.chipset}`);
        if (component.formato) specs.push(`Formato: ${component.formato}`);
        if (component.tipo_ram_soportado) specs.push(`RAM: ${component.tipo_ram_soportado}`);
        if (component.formato_ram_soportado) specs.push(`Formato RAM: ${component.formato_ram_soportado}`);
        if (component.ranuras_ram) specs.push(`Slots RAM: ${component.ranuras_ram}`);
        if (component.capacidad_maxima_ram_gb) specs.push(`RAM máx.: ${component.capacidad_maxima_ram_gb}GB`);
        if (component.ranuras_m2_solo_nvme != null) specs.push(`M.2 solo NVMe: ${component.ranuras_m2_solo_nvme}`);
        if (component.ranuras_m2_solo_sata != null) specs.push(`M.2 solo SATA: ${component.ranuras_m2_solo_sata}`);
        if (component.ranuras_m2_nvme_o_sata != null) specs.push(`M.2 NVMe o SATA: ${component.ranuras_m2_nvme_o_sata}`);
        if (component.puertos_sata != null) specs.push(`Puertos SATA: ${component.puertos_sata}`);
        // RAM
        if (component.tipo_ddr) specs.push(`Tipo: ${component.tipo_ddr}`);
        if (component.formato_ram) specs.push(`Formato: ${component.formato_ram}`);
        if (component.modulos_por_producto) specs.push(`Módulos: ${component.modulos_por_producto}`);
        if (component.capacidad_modulo_gb) specs.push(`Por módulo: ${component.capacidad_modulo_gb}GB`);
        if (component.velocidad_mhz) specs.push(`Velocidad indicada: ${component.velocidad_mhz}MHz`);
        // GPU
        if (component.vram_gb) specs.push(`VRAM: ${component.vram_gb}GB`);
        if (component.tipo_memoria) specs.push(`Memoria: ${component.tipo_memoria}`);
        if (component.interfaz) specs.push(`Interfaz: ${component.interfaz}`);
        // Almacenamiento y otros con capacidad
        if (component.capacidad_gb && !component.tipo_ddr) specs.push(`Capacidad: ${component.capacidad_gb}GB`);
        if (component.capacidad_gb && component.tipo_ddr) specs.push(`Capacidad del producto: ${component.capacidad_gb}GB`);
        // Fuente de Poder
        if (component.potencia_watts) specs.push(`Potencia: ${component.potencia_watts}W`);
        if (component.potencia_referencia_watts) specs.push(`Referencia: ${component.potencia_referencia_watts}W`);
        if (component.consumo_referencia_watts) specs.push(`Consumo ref.: ${component.consumo_referencia_watts}W`);
        if (component.potencia_minima_fuente_watts) specs.push(`Fuente mín. recomendada: ${component.potencia_minima_fuente_watts}W`);
        if (component.largo_mm) specs.push(`Largo: ${component.largo_mm}mm`);
        if (component.largo_max_gpu_mm) specs.push(`GPU máx.: ${component.largo_max_gpu_mm}mm`);
        // Refrigeración
        if (component.tipo) specs.push(`Tipo: ${component.tipo}`);
        if (component.tamanho_radiador_mm) specs.push(`Radiador: ${component.tamanho_radiador_mm}mm`);

        return specs;
    }

    function handleSelectionChange(e) {
        e.preventDefault();
        const target = e.currentTarget;
        if (target.dataset.seleccionable === '0') {
            return;
        }
        const type = target.dataset.type;
        const selectedId = target.dataset.id;
        const modelName = target.dataset.modelName;
        const producto = (allComponentsData[type] || []).find(c => (
            String(c.id) === String(selectedId) && (!modelName || c.model_name === modelName)
        ));
        if (!producto) {
            return;
        }

        if (type === 'memoria_ram') {
            if (modoModal === 'reemplazar') {
                const indice = memorias.findIndex(ram => String(ram.id) === String(reemplazaId));
                const cantidad = indice >= 0 ? memorias[indice].cantidad : 1;
                const sinLinea = memorias.filter(ram => String(ram.id) !== String(reemplazaId));
                const existente = sinLinea.find(ram => String(ram.id) === String(producto.id));
                if (existente && existente.cantidad + cantidad > Number(existente.stock)) {
                    showToast('No hay más unidades en stock.', 'error');
                    return;
                }
                if (!existente && cantidad > Number(producto.stock)) {
                    showToast('No hay más unidades en stock.', 'error');
                    return;
                }
                memorias = sinLinea;
                if (existente) {
                    existente.cantidad += cantidad;
                } else {
                    memorias.push(Object.assign({}, producto, { cantidad }));
                }
            } else {
                const existente = memorias.find(ram => String(ram.id) === String(producto.id));
                if (existente) {
                    if (existente.cantidad >= Number(existente.stock)) {
                        showToast('No hay más unidades en stock.', 'error');
                        return;
                    }
                    existente.cantidad += 1;
                } else {
                    memorias.push(Object.assign({}, producto, { cantidad: 1 }));
                }
            }
        } else if (type === 'almacenamiento') {
            const existente = discos.find(disco => (
                disco.model_name === producto.model_name && String(disco.id) === String(producto.id)
            ));
            if (existente) {
                if (existente.cantidad >= Number(existente.stock)) {
                    showToast('No hay más unidades en stock.', 'error');
                    return;
                }
                existente.cantidad += 1;
            } else {
                discos.push(Object.assign({}, producto, { cantidad: 1 }));
            }
        } else {
            currentBuild[type] = producto;
        }

        modalComponente().hide();
        consultarEvaluacion();
    }

    function quitarDisco(e) {
        const modelName = e.currentTarget.dataset.modelName;
        const id = e.currentTarget.dataset.id;
        discos = discos.filter(disco => !(disco.model_name === modelName && String(disco.id) === String(id)));
        consultarEvaluacion();
    }

    function cambiarCantidadDisco(e) {
        const modelName = e.target.dataset.modelName;
        const id = e.target.dataset.id;
        const disco = discos.find(item => item.model_name === modelName && String(item.id) === String(id));
        const numero = Number(e.target.value);
        if (!disco || !Number.isInteger(numero) || numero < 1 || numero > Number(disco.stock)) {
            showToast('La cantidad debe ser un entero positivo dentro del stock.', 'error');
            consultarEvaluacion();
            return;
        }
        disco.cantidad = numero;
        consultarEvaluacion();
    }

    function quitarRam(e) {
        const id = e.currentTarget.dataset.id;
        memorias = memorias.filter(ram => String(ram.id) !== String(id));
        consultarEvaluacion();
    }

    function cambiarCantidadRam(e) {
        const id = e.target.dataset.id;
        const ram = memorias.find(item => String(item.id) === String(id));
        const numero = Number(e.target.value);
        if (!ram || !Number.isInteger(numero) || numero < 1 || numero > Number(ram.stock)) {
            showToast('La cantidad debe ser un entero positivo dentro del stock.', 'error');
            consultarEvaluacion();
            return;
        }
        ram.cantidad = numero;
        consultarEvaluacion();
    }

    function handleRemoveComponent(e) {
        const type = e.target.dataset.type;
        delete currentBuild[type];
        consultarEvaluacion();
    }

    function piezaEvaluada(key) {
        if (!evaluacionActual || evaluacionActual.pendiente || evaluacionActual.fallo) {
            return null;
        }
        return (evaluacionActual.piezas || {})[key] || null;
    }

    function clasificarPieza(pieza) {
        if (!pieza) {
            return null;
        }
        const pendientes = pieza.pendientes || [];
        const avisos = pieza.advertencias || [];
        if (pieza.estado === 'incompatible') {
            return { texto: 'Incompatible', clase: 'text-danger', icono: 'fa-times-circle' };
        }
        if (pieza.estado === 'datos_insuficientes' || avisos.length) {
            return { texto: 'Revisar compatibilidad', clase: 'text-warning', icono: 'fa-exclamation-triangle' };
        }
        if (pieza.estado === 'no_evaluada') {
            return { texto: 'Compatibilidad no verificada', clase: 'text-info', icono: 'fa-info-circle' };
        }
        if (pieza.estado === 'incompleto' || pendientes.length) {
            return { texto: 'Faltan componentes', clase: 'text-info', icono: 'fa-info-circle' };
        }
        if (pieza.estado === 'compatible') {
            return { texto: 'Compatible', clase: 'text-success', icono: 'fa-check-circle' };
        }
        return { texto: 'Compatibilidad no verificada', clase: 'text-info', icono: 'fa-info-circle' };
    }

    function textosDetalle(pieza) {
        const textos = [];
        const agregar = (valor) => {
            const limpio = String(valor || '').trim();
            if (limpio && !textos.includes(limpio)) {
                textos.push(limpio);
            }
        };
        if (!pieza) {
            return textos;
        }
        agregar(pieza.etiqueta);
        (pieza.coincidencias || []).forEach(agregar);
        (pieza.motivos || []).forEach(agregar);
        (pieza.pendientes || []).forEach(agregar);
        (pieza.advertencias || []).forEach(agregar);
        return textos;
    }

    function esAvisoCritico(texto) {
        return /potencia insuficiente|no se puede estimar la potencia|para estimar la potencia de la fuente/i.test(texto);
    }

    function contenidoEstado(pieza, label) {
        const clase = clasificarPieza(pieza);
        if (!evaluacionActual || evaluacionActual.pendiente) {
            return { clase: 'text-muted', html: '<span>Consultando compatibilidad...</span>' };
        }
        if (evaluacionActual.fallo || !clase) {
            return { clase: 'text-danger', html: '<span>No se pudo consultar la compatibilidad.</span>' };
        }
        const detalle = textosDetalle(pieza);
        const info = detalle.length
            ? `<button type="button" class="btn btn-link btn-sm armado-resumen-info ${clase.clase}" data-detalle="${escaparHtml(detalle.join('\n\n'))}" aria-label="Ver detalle de compatibilidad de ${escaparHtml(label)}"><i class="fas fa-info-circle" aria-hidden="true"></i></button>`
            : '';
        return {
            clase: clase.clase,
            html: `<span><i class="fas ${clase.icono}" aria-hidden="true"></i> ${escaparHtml(clase.texto)}</span>${info}`,
        };
    }

    function htmlEstadoTarjeta(key, label) {
        const estado = contenidoEstado(piezaEvaluada(key), label);
        return `<div class="armado-estado-compacto ${estado.clase}">${estado.html}</div>`;
    }

    function desecharPopovers(raiz) {
        if (!raiz) {
            return;
        }
        raiz.querySelectorAll('[data-detalle]').forEach(boton => {
            const instancia = bootstrap.Popover.getInstance(boton);
            if (instancia) {
                instancia.dispose();
            }
        });
    }

    function cerrarPopovers(excepto) {
        document.querySelectorAll('[data-detalle]').forEach(boton => {
            if (boton === excepto) {
                return;
            }
            const instancia = bootstrap.Popover.getInstance(boton);
            if (instancia) {
                instancia.hide();
            }
        });
    }

    function montarPopovers(raiz) {
        if (!raiz) {
            return;
        }
        raiz.querySelectorAll('[data-detalle]').forEach(boton => {
            const popover = new bootstrap.Popover(boton, {
                container: 'body',
                trigger: 'click',
                placement: 'auto',
                html: false,
                customClass: 'armado-popover',
                title: 'Detalle de compatibilidad',
                content: boton.getAttribute('data-detalle') || '',
            });
            boton.addEventListener('click', (evento) => {
                evento.stopPropagation();
                cerrarPopovers(boton);
            });
            boton.addEventListener('keydown', (evento) => {
                if (evento.key === 'Escape') {
                    evento.stopPropagation();
                    popover.hide();
                }
            });
        });
    }

    document.addEventListener('click', (evento) => {
        if (evento.target.closest('[data-detalle]') || evento.target.closest('.popover')) {
            return;
        }
        cerrarPopovers(null);
    });
    document.addEventListener('keydown', (evento) => {
        if (evento.key === 'Escape') {
            cerrarPopovers(null);
        }
    });

    async function consultarEvaluacion() {
        const serial = ++consultaSerial;
        const componentes = seleccionActual();
        if (componentes.length === 0) {
            evaluacionActual = {
                piezas: {},
                estado: 'compatible',
                texto: '',
                motivos: [],
                fallo: false,
                pendiente: false,
            };
            initializeBuilder();
            document.dispatchEvent(
                new CustomEvent('hw-builder-state', { detail: { componentes: [] } })
            );
            return;
        }

        evaluacionActual = { pendiente: true, fallo: false, piezas: {} };
        initializeBuilder();
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        try {
            const response = await fetch(urls.evaluarUrl, {
                method: 'POST',
                body: JSON.stringify({ componentes }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfInput ? csrfInput.value : '',
                },
            });
            const data = await response.json().catch(() => ({}));
            if (serial !== consultaSerial) {
                return;
            }
            if (!response.ok || data.status !== 'success' || !data.piezas) {
                evaluacionActual = { fallo: true, pendiente: false, piezas: {} };
            } else {
                evaluacionActual = Object.assign({}, data, { fallo: false, pendiente: false });
            }
            document.dispatchEvent(
                new CustomEvent('hw-builder-state', { detail: { componentes: seleccionActual() } })
            );
        } catch (error) {
            console.error('Error al evaluar el armado:', error);
            if (serial !== consultaSerial) {
                return;
            }
            evaluacionActual = { fallo: true, pendiente: false, piezas: {} };
        }
        initializeBuilder();
    }

    // --- 4. ACTUALIZAR RESUMEN Y TOTAL ---

    function updateSummaryAndTotal() {
        desecharPopovers(summaryList);
        summaryList.innerHTML = '';
        let total = 0;
        let componentCount = 0;
        const criticosVisibles = new Set();

        const agregarLinea = (key, label, subtotal, nombres) => {
            total += subtotal;
            componentCount += 1;
            const pieza = piezaEvaluada(key);
            const estado = contenidoEstado(pieza, label);
            const clase = estado;
            const criticos = (pieza && evaluacionActual && !evaluacionActual.pendiente && !evaluacionActual.fallo)
                ? [...(pieza.motivos || []), ...(pieza.advertencias || [])].filter(esAvisoCritico)
                : [];
            const avisosCriticos = criticos.filter(texto => {
                if (criticosVisibles.has(texto)) {
                    return false;
                }
                criticosVisibles.add(texto);
                return true;
            }).map(texto => `<p class="armado-resumen-critico text-warning mb-0">${escaparHtml(texto)}</p>`).join('');
            const summaryItem = document.createElement('div');
            summaryItem.className = 'armado-resumen-item';
            summaryItem.innerHTML = `
                <div class="d-flex justify-content-between gap-2">
                    <span class="fw-bold">${escaparHtml(label)}</span>
                    <span class="text-nowrap">$${subtotal.toLocaleString('es-CL')}</span>
                </div>
                ${nombres}
                <div class="armado-resumen-estado ${clase.clase}">${clase.html}</div>
                ${avisosCriticos}
            `;
            summaryList.appendChild(summaryItem);
        };

        componentOrder.forEach(({ key, label }) => {
            if (key === 'memoria_ram') {
                if (memorias.length === 0) {
                    return;
                }
                const subtotal = memorias.reduce((suma, ram) => suma + parseFloat(ram.precio) * ram.cantidad, 0);
                const lineas = memorias.map(ram => (
                    `<p class="mb-0 small text-muted">${escaparHtml(ram.nombre)} × ${ram.cantidad}</p>`
                )).join('') + `<p class="mb-0 small text-muted">${escaparHtml(textoConteoRam())}</p>`;
                agregarLinea(key, label, subtotal, lineas);
                return;
            }
            if (key === 'almacenamiento') {
                if (discos.length === 0) {
                    return;
                }
                const subtotal = discos.reduce((suma, disco) => suma + parseFloat(disco.precio) * disco.cantidad, 0);
                const lineas = discos.map(disco => (
                    `<p class="mb-0 small text-muted">${escaparHtml(disco.nombre)} × ${disco.cantidad}</p>`
                )).join('');
                agregarLinea(key, label, subtotal, lineas);
                return;
            }
            const component = currentBuild[key];
            if (component) {
                agregarLinea(
                    key,
                    label,
                    parseFloat(component.precio),
                    `<p class="mb-0 small text-muted">${escaparHtml(component.nombre)}</p>`,
                );
            }
        });

        if (componentCount > 0 && evaluacionActual && !evaluacionActual.pendiente && !evaluacionActual.fallo) {
            (evaluacionActual.advertencias || []).filter(esAvisoCritico).forEach(texto => {
                if (criticosVisibles.has(texto)) {
                    return;
                }
                criticosVisibles.add(texto);
                const nota = document.createElement('p');
                nota.className = 'armado-resumen-critico text-warning mb-0';
                nota.textContent = texto;
                summaryList.appendChild(nota);
            });
        }

        montarPopovers(summaryList);

        totalPriceEl.textContent = `$${total.toLocaleString('es-CL')}`;

        addToCartBtn.disabled = componentCount === 0;
        downloadExcelBtn.disabled = componentCount === 0;
    }

    // --- 5. ACCIONES FINALES ---

    // Función para mostrar un mensaje flotante (toast)
    function showToast(message, type = 'success') {
        const toastContainer = document.body;
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '1050';
        toast.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        toast.textContent = message;

        toastContainer.appendChild(toast);

        // El mensaje desaparece después de 3 segundos
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    async function addAllToCart() {
        const componentes = seleccionActual();
        if (componentes.length === 0) return;

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');

        try {
            const response = await fetch(urls.addArmadoUrl, {
                method: 'POST',
                body: JSON.stringify({ componentes }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfInput ? csrfInput.value : '',
                },
            });
            const data = await response.json();
            if (!response.ok || data.status !== 'success') {
                const motivos = (data.motivos || []).filter(Boolean);
                alert(motivos.length ? motivos.join('\n') : (data.message || 'No se agregó el armado al carrito.'));
                return;
            }
        } catch (error) {
            console.error('Error al agregar el armado:', error);
            alert('Hubo un error de comunicación con el servidor al agregar el armado.');
            return;
        }

        showToast('¡Componentes agregados! Redirigiendo al carrito...');
        setTimeout(() => {
            window.location.href = '/carrito/';
        }, 1500);
    }

    async function downloadAsExcel() {
        const componentes = seleccionActual();
        if (componentes.length === 0) {
            return;
        }

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        let response;
        try {
            response = await fetch(urls.exportarUrl, {
                method: 'POST',
                body: JSON.stringify({ componentes }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfInput ? csrfInput.value : '',
                },
            });
        } catch (error) {
            console.error('Error al exportar el armado:', error);
            alert('No se pudo consultar la compatibilidad. El Excel no se generó para no mostrar un resultado anterior.');
            return;
        }

        const tipo = response.headers.get('Content-Type') || '';
        if (!response.ok || !tipo.includes('spreadsheetml')) {
            alert('No se pudo consultar la compatibilidad. El Excel no se generó para no mostrar un resultado anterior.');
            return;
        }

        const blob = await response.blob();
        const enlace = document.createElement('a');
        const url = URL.createObjectURL(blob);
        enlace.href = url;
        enlace.download = 'Presupuesto_armado_PC.xlsx';
        document.body.appendChild(enlace);
        enlace.click();
        enlace.remove();
        URL.revokeObjectURL(url);
    }

    function revalidarUrl() {
        const root = document.getElementById('hw-chat-root');
        return root ? root.getAttribute('data-revalidar-url') : '';
    }

    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : '';
    }

    async function revalidarPropuesta(propuesta) {
        const url = revalidarUrl();
        if (!url || !propuesta) {
            return null;
        }
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                credentials: 'same-origin',
                body: JSON.stringify({ proposal: propuesta }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.status !== 'success') {
                return null;
            }
            return data;
        } catch (e) {
            return null;
        }
    }

    function buscarProductoEnCatalogo(tipo, id) {
        if (tipo === 'memoria_ram') {
            return (allComponentsData.memoria_ram || []).find(c => String(c.id) === String(id));
        }
        if (tipo === 'almacenamiento_ssd' || tipo === 'almacenamiento_hdd') {
            return (allComponentsData.almacenamiento || []).find(c => (
                String(c.id) === String(id) && c.model_name === tipo
            ));
        }
        const uiKey = tipo === 'refrigeracion' ? 'refrigeracion_cooler' : tipo;
        const lista = allComponentsData[uiKey] || [];
        return lista.find(c => String(c.id) === String(id));
    }

    function aplicarSeleccionDesdeApi(componentes) {
        if (!Array.isArray(componentes) || componentes.length === 0) {
            return false;
        }
        currentBuild = {};
        discos = [];
        memorias = [];
        let aplicados = 0;
        componentes.forEach(item => {
            const tipo = item.tipo;
            const cantidad = item.cantidad ? Number(item.cantidad) : 1;
            const producto = buscarProductoEnCatalogo(tipo, item.id);
            if (!producto) {
                return;
            }
            aplicados += 1;
            if (tipo === 'memoria_ram') {
                memorias.push(Object.assign({}, producto, { cantidad }));
            } else if (tipo === 'almacenamiento_ssd' || tipo === 'almacenamiento_hdd') {
                discos.push(Object.assign({}, producto, { cantidad }));
            } else {
                const uiKey = tipo === 'refrigeracion' ? 'refrigeracion_cooler' : tipo;
                currentBuild[uiKey] = producto;
            }
        });
        if (aplicados === 0) {
            return false;
        }
        consultarEvaluacion();
        return true;
    }

    function builderTienePiezas() {
        return seleccionActual().length > 0;
    }

    function limpiarPropuestaAplicada() {
        if (window.HWChatSession) {
            window.HWChatSession.setProposalPending(null, rootUserKey());
        }
        if (window.history && window.history.replaceState) {
            const url = new URL(window.location.href);
            url.searchParams.delete('aplicar');
            window.history.replaceState({}, '', url.pathname + url.search);
        }
    }

    function mostrarBannerPropuestaPendiente(propuesta, opciones) {
        opciones = opciones || {};
        if (!propuesta || !Array.isArray(propuesta.componentes)) {
            return;
        }
        const contenedor = document.getElementById('armado-pending-banner');
        if (!contenedor) {
            return;
        }
        contenedor.innerHTML = `
            <div class="alert alert-info d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
                <span>${opciones.reemplazar ? 'Ya tienes piezas en el armador. ¿Reemplazo el armado con la propuesta del chat?' : 'Tienes una propuesta de armado desde el asistente. ¿Quieres cargarla aquí?'}</span>
                <div>
                    <button type="button" class="btn btn-sm btn-primary" id="armado-apply-pending-btn">${opciones.reemplazar ? 'Reemplazar armado' : 'Cargar propuesta'}</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" id="armado-dismiss-pending-btn">Descartar</button>
                </div>
            </div>`;
        contenedor.querySelector('#armado-apply-pending-btn').addEventListener('click', async function () {
            const validada = await revalidarPropuesta(propuesta);
            if (!validada || !validada.componentes) {
                showToast('La propuesta expiró o ya no tiene stock y compatibilidad válidos.', 'error');
                return;
            }
            if (aplicarSeleccionDesdeApi(validada.componentes)) {
                limpiarPropuestaAplicada();
                contenedor.innerHTML = '';
                showToast('Propuesta cargada en el armador.');
            } else {
                showToast('No se pudieron mapear las piezas al catálogo actual.', 'error');
            }
        });
        contenedor.querySelector('#armado-dismiss-pending-btn').addEventListener('click', function () {
            if (window.HWChatSession) {
                window.HWChatSession.setProposalPending(null, rootUserKey());
            }
            contenedor.innerHTML = '';
        });
    }

    function rootUserKey() {
        const root = document.getElementById('hw-chat-root');
        return root ? root.getAttribute('data-user-key') || 'anon' : 'anon';
    }

    function leerPropuestaPendienteLocal() {
        if (window.HWChatSession) {
            return window.HWChatSession.getProposalPending(rootUserKey());
        }
        return null;
    }

    window.HW_BUILDER_SYNC = {
        getComponentes: seleccionActual,
        applyComponentes: aplicarSeleccionDesdeApi,
        refresh: consultarEvaluacion,
    };

    document.addEventListener('hw-armado-apply', function (event) {
        const detalle = event.detail || {};
        if (detalle.componentes && aplicarSeleccionDesdeApi(detalle.componentes)) {
            showToast('Armado actualizado desde el chat.');
        }
    });

    document.addEventListener('hw-armado-pending', function (event) {
        const propuesta = event.detail;
        if (propuesta) {
            if (window.HWChatSession) {
                window.HWChatSession.setProposalPending(propuesta, rootUserKey());
            }
            mostrarBannerPropuestaPendiente(propuesta);
        }
    });

    function iniciarRecomendador() {
        const abrir = document.getElementById('recomendar-pc-btn');
        const modalEl = document.getElementById('recomendarPcModal');
        const detalleEl = document.getElementById('recomendarPcDetalleModal');
        const formulario = document.getElementById('recomendar-pc-form');
        const salida = document.getElementById('recomendar-pc-resultado');
        const detalleCuerpo = document.getElementById('recomendar-pc-detalle');
        const detalleTitulo = document.getElementById('recomendarPcDetalleLabel');
        if (!abrir || !modalEl || !detalleEl || !formulario || !salida || !detalleCuerpo || !urls.recomendarPcUrl) {
            return;
        }
        const modal = new bootstrap.Modal(modalEl);
        const modalDetalle = new bootstrap.Modal(detalleEl);
        let propuestas = [];
        let buscando = false;
        let indiceDetalle = null;
        let volverAlCerrarDetalle = false;
        let trasCerrarPrincipal = null;
        let trasCerrarDetalle = null;
        let cambiandoModal = false;
        abrir.addEventListener('click', () => modal.show());

        function cuandoEsteQuieto(elemento, instancia, callback) {
            if (!instancia._isTransitioning) {
                callback();
                return;
            }
            const continuar = () => {
                elemento.removeEventListener('shown.bs.modal', continuar);
                elemento.removeEventListener('hidden.bs.modal', continuar);
                callback();
            };
            elemento.addEventListener('shown.bs.modal', continuar);
            elemento.addEventListener('hidden.bs.modal', continuar);
        }

        modalEl.addEventListener('hidden.bs.modal', () => {
            const accion = trasCerrarPrincipal;
            trasCerrarPrincipal = null;
            if (accion) {
                accion();
            }
        });
        detalleEl.addEventListener('hide.bs.modal', () => {
            if (volverAlCerrarDetalle) {
                trasCerrarDetalle = () => modal.show();
            }
        });
        detalleEl.addEventListener('hidden.bs.modal', () => {
            const accion = trasCerrarDetalle;
            trasCerrarDetalle = null;
            volverAlCerrarDetalle = false;
            if (accion) {
                accion();
            }
        });

        formulario.addEventListener('submit', async (evento) => {
            evento.preventDefault();
            if (buscando) {
                return;
            }
            const boton = document.getElementById('recomendador-generar');
            const modo = formulario.querySelector('input[name="modo"]:checked');
            const cuerpo = {
                presupuesto: document.getElementById('recomendador-presupuesto').value,
                uso: document.getElementById('recomendador-uso').value,
                resolucion: document.getElementById('recomendador-resolucion').value,
                modo: modo ? modo.value : '',
            };
            if (cuerpo.modo === 'completar') {
                cuerpo.componentes = seleccionActual();
            }
            buscando = true;
            boton.disabled = true;
            boton.setAttribute('aria-busy', 'true');
            salida.innerHTML = `
                <div class="d-flex align-items-center gap-2 text-muted" role="status">
                    <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                    <span>Buscando configuraciones en el inventario...</span>
                </div>`;
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            try {
                const response = await fetch(urls.recomendarPcUrl, {
                    method: 'POST',
                    body: JSON.stringify(cuerpo),
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfInput ? csrfInput.value : '',
                    },
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    propuestas = [];
                    salida.innerHTML = `<p class="text-danger mb-0">${escaparHtml(data.message || 'No se pudo generar la recomendación.')}</p>`;
                    return;
                }
                propuestas = data.recomendaciones || [];
                salida.innerHTML = htmlRecomendaciones(data);
            } catch (error) {
                console.error('Error al recomendar el armado:', error);
                propuestas = [];
                salida.innerHTML = '<p class="text-danger mb-0">No se pudo consultar el recomendador.</p>';
            } finally {
                buscando = false;
                boton.disabled = false;
                boton.removeAttribute('aria-busy');
            }
        });

        function cerrarModalActivo() {
            volverAlCerrarDetalle = false;
            trasCerrarDetalle = null;
            const cerrarDetalle = () => {
                if (!modalDetalle._isShown && !detalleEl.classList.contains('show')) {
                    return;
                }
                cuandoEsteQuieto(detalleEl, modalDetalle, () => modalDetalle.hide());
            };
            const cerrarPrincipal = () => {
                if (!modal._isShown && !modalEl.classList.contains('show')) {
                    return;
                }
                cuandoEsteQuieto(modalEl, modal, () => modal.hide());
            };
            if (modalDetalle._isShown || detalleEl.classList.contains('show') || modalDetalle._isTransitioning) {
                cerrarDetalle();
                return;
            }
            cerrarPrincipal();
        }

        function aplicarPropuesta(indice) {
            const propuesta = propuestas[Number(indice)];
            if (!propuesta || !aplicarSeleccionDesdeApi(propuesta.componentes)) {
                showToast('No se pudieron cargar las piezas en el armador.', 'error');
                return;
            }
            trasCerrarPrincipal = null;
            cambiandoModal = false;
            cerrarModalActivo();
            showToast('Recomendación cargada en el armador.');
        }

        function abrirDetalle(indice) {
            const propuesta = propuestas[Number(indice)];
            if (!propuesta || cambiandoModal || (!modalEl.classList.contains('show') && !modal._isShown)) {
                return;
            }
            cambiandoModal = true;
            indiceDetalle = Number(indice);
            if (detalleTitulo) {
                detalleTitulo.textContent = propuesta.titulo || 'Detalle de la recomendación';
            }
            detalleCuerpo.innerHTML = htmlDetalleRecomendacion(propuesta);
            volverAlCerrarDetalle = true;
            cuandoEsteQuieto(modalEl, modal, () => {
                if (modal._isShown || modalEl.classList.contains('show')) {
                    trasCerrarPrincipal = () => modalDetalle.show();
                    modal.hide();
                    return;
                }
                modalDetalle.show();
            });
            detalleEl.addEventListener('shown.bs.modal', function liberar() {
                detalleEl.removeEventListener('shown.bs.modal', liberar);
                cambiandoModal = false;
            });
        }

        salida.addEventListener('click', (evento) => {
            const ver = evento.target.closest('[data-ver-detalle]');
            if (ver) {
                abrirDetalle(ver.dataset.verDetalle);
                return;
            }
            const boton = evento.target.closest('[data-aplicar-recomendacion]');
            if (!boton) {
                return;
            }
            aplicarPropuesta(boton.dataset.aplicarRecomendacion);
        });

        document.getElementById('recomendador-volver').addEventListener('click', () => {
            volverAlCerrarDetalle = true;
            cuandoEsteQuieto(detalleEl, modalDetalle, () => {
                if (detalleEl.classList.contains('show') || modalDetalle._isShown) {
                    modalDetalle.hide();
                }
            });
        });
        document.getElementById('recomendador-aplicar-detalle').addEventListener('click', () => {
            if (indiceDetalle === null) {
                return;
            }
            aplicarPropuesta(indiceDetalle);
        });
    }

    function pesosClp(valor) {
        return `$${Number(valor).toLocaleString('es-CL')}`;
    }

    function esDisco(tipo) {
        return tipo === 'almacenamiento_ssd' || tipo === 'almacenamiento_hdd';
    }

    function esAvisoNoVerificado(texto) {
        return /no se comprueban puertos SATA|Compatibilidad no evaluada/i.test(texto || '');
    }

    function esAvisoVisible(texto) {
        return /potencia insuficiente|no coincide con|incompatible/i.test(texto || '');
    }

    function textosUnicos(lista) {
        const unicos = [];
        (lista || []).forEach(texto => {
            const limpio = String(texto || '').trim();
            if (limpio && !unicos.includes(limpio)) {
                unicos.push(limpio);
            }
        });
        return unicos;
    }

    function avisosDe(propuesta) {
        const repetidos = [];
        const vistos = {};
        (propuesta.componentes || []).forEach(pieza => {
            String(pieza.motivo || '').split(/(?<=\.)\s+/).forEach(fragmento => {
                const limpio = fragmento.trim();
                if (limpio.length < 40) {
                    return;
                }
                vistos[limpio] = (vistos[limpio] || 0) + 1;
            });
        });
        Object.keys(vistos).forEach(texto => {
            if (vistos[texto] > 1) {
                repetidos.push(texto);
            }
        });
        return textosUnicos([...(propuesta.limitaciones || []), ...(propuesta.advertencias || []), ...repetidos]);
    }

    function motivoSinAvisos(motivo, avisos) {
        let texto = String(motivo || '').trim();
        avisos.forEach(aviso => {
            if (aviso && texto.includes(aviso)) {
                texto = texto.replace(aviso, ' ');
            }
        });
        return texto.replace(/\s+/g, ' ').trim();
    }

    function estadoRecomendacion(propuesta) {
        if (propuesta.estado_reglas === 'incompatible') {
            return {
                clase: 'text-danger',
                icono: 'fa-times-circle',
                texto: propuesta.compatibilidad || 'Incompatible',
            };
        }
        if (propuesta.estado_reglas === 'no_evaluada') {
            return {
                clase: 'text-info',
                icono: 'fa-info-circle',
                texto: propuesta.compatibilidad || 'Compatibilidad no verificada',
            };
        }
        if (propuesta.completamente_compatible) {
            return { clase: 'text-success', icono: 'fa-check-circle', texto: propuesta.compatibilidad || 'Compatible' };
        }
        return {
            clase: 'text-warning',
            icono: 'fa-exclamation-circle',
            texto: propuesta.compatibilidad || 'Reglas comprobadas, con limitaciones',
        };
    }

    function resumenDe(componentes, tipos) {
        const piezas = (componentes || []).filter(pieza => tipos.includes(pieza.tipo));
        if (!piezas.length) {
            return 'No incluida';
        }
        return piezas.map(pieza => {
            const cantidad = Number(pieza.cantidad) > 1 ? ` × ${pieza.cantidad}` : '';
            return `${pieza.nombre}${cantidad}`;
        }).join(' + ');
    }

    function htmlRecomendaciones(data) {
        if (!data.recomendaciones || data.recomendaciones.length === 0) {
            const detalle = textosUnicos(data.detalle).map(texto => `<li>${escaparHtml(texto)}</li>`).join('');
            return `
                <div class="alert alert-warning mb-0" role="status">
                    <p class="mb-2">${escaparHtml(data.mensaje || 'No hay una configuración disponible con estos criterios.')}</p>
                    ${detalle ? `<ul class="mb-0">${detalle}</ul>` : ''}
                </div>`;
        }
        const totales = data.recomendaciones.map(propuesta => Number(propuesta.total));
        const minimo = Math.min(...totales);
        const hayMasCaro = totales.some(total => total > minimo);
        const tarjetas = data.recomendaciones.map((propuesta, indice) => {
            const componentes = propuesta.componentes || [];
            const avisos = avisosDe(propuesta);
            const estado = estadoRecomendacion(propuesta);
            const discoSinVerificar = avisos.some(esAvisoNoVerificado) || componentes.some(pieza => (
                esDisco(pieza.tipo) && esAvisoNoVerificado(pieza.motivo)
            ));
            const criticos = avisos.filter(esAvisoVisible);
            const presupuesto = Number(propuesta.presupuesto);
            const total = Number(propuesta.total);
            let diferencia = '';
            if (Number.isFinite(presupuesto) && Number.isFinite(total)) {
                const resta = presupuesto - total;
                if (resta > 0) {
                    diferencia = `Quedan ${pesosClp(resta)} dentro del presupuesto`;
                } else if (resta < 0) {
                    diferencia = `Supera el presupuesto en ${pesosClp(Math.abs(resta))}`;
                }
            }
            const menorPrecio = hayMasCaro && total === minimo
                ? '<span class="badge bg-success">Menor precio</span>'
                : '';
            const visibleCritico = criticos.map(texto => `<p class="small text-danger mb-1">${escaparHtml(texto)}</p>`).join('');
            const almacenamiento = discoSinVerificar
                ? '<p class="small text-info mb-1"><i class="fas fa-info-circle" aria-hidden="true"></i> Almacenamiento: compatibilidad no verificada</p>'
                : '';
            return `
                <div class="col">
                    <article class="card h-100 recomendacion-tarjeta">
                        <div class="card-body d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start gap-2 mb-2">
                                <h6 class="mb-0">${escaparHtml(propuesta.titulo || `Opción ${indice + 1}`)}</h6>
                                ${menorPrecio}
                            </div>
                            <p class="recomendacion-precio fw-bold text-success mb-1">${pesosClp(total)}</p>
                            ${diferencia ? `<p class="small text-muted mb-2">${diferencia}</p>` : ''}
                            <dl class="recomendacion-resumen small mb-2">
                                <div class="d-flex gap-2"><dt class="mb-0">CPU</dt><dd class="mb-0 text-break">${escaparHtml(resumenDe(componentes, ['procesador']))}</dd></div>
                                <div class="d-flex gap-2"><dt class="mb-0">GPU</dt><dd class="mb-0 text-break">${escaparHtml(resumenDe(componentes, ['tarjeta_grafica']))}</dd></div>
                                <div class="d-flex gap-2"><dt class="mb-0">RAM</dt><dd class="mb-0 text-break">${escaparHtml(resumenDe(componentes, ['memoria_ram']))}</dd></div>
                                <div class="d-flex gap-2"><dt class="mb-0">Disco</dt><dd class="mb-0 text-break">${escaparHtml(resumenDe(componentes, ['almacenamiento_ssd', 'almacenamiento_hdd']))}</dd></div>
                            </dl>
                            <p class="recomendacion-estado ${estado.clase} mb-1"><i class="fas ${estado.icono}" aria-hidden="true"></i> ${escaparHtml(estado.texto)}</p>
                            ${almacenamiento}
                            ${visibleCritico}
                            <p class="small text-muted mb-3">${componentes.length} ${componentes.length === 1 ? 'componente' : 'componentes'}</p>
                            <div class="d-grid gap-2 mt-auto">
                                <button type="button" class="btn btn-sm btn-outline-success" data-ver-detalle="${indice}">Ver detalles</button>
                                <button type="button" class="btn btn-sm btn-success" data-aplicar-recomendacion="${indice}">Aplicar recomendación</button>
                            </div>
                        </div>
                    </article>
                </div>`;
        }).join('');
        return `<div class="row row-cols-1 row-cols-md-2 g-3">${tarjetas}</div>`;
    }

    function htmlDetalleRecomendacion(propuesta) {
        const componentes = propuesta.componentes || [];
        const avisos = avisosDe(propuesta);
        const discoSinVerificar = avisos.some(esAvisoNoVerificado) || componentes.some(pieza => (
            esDisco(pieza.tipo) && esAvisoNoVerificado(pieza.motivo)
        ));
        const filas = componentes.map(pieza => {
            const motivo = motivoSinAvisos(pieza.motivo, avisos);
            const unidades = Number(pieza.cantidad) === 1 ? '1 unidad' : `${pieza.cantidad} unidades`;
            const noVerificado = esDisco(pieza.tipo) && (discoSinVerificar || esAvisoNoVerificado(pieza.motivo))
                ? '<div class="small text-info">Compatibilidad no verificada</div>'
                : '';
            return `
                <li>
                    <div class="d-flex justify-content-between gap-2">
                        <span class="fw-bold text-break">${escaparHtml(pieza.nombre)}</span>
                        <span class="text-nowrap">${pesosClp(pieza.subtotal)}</span>
                    </div>
                    <div class="small text-muted">${escaparHtml(pieza.categoria || '')} · ${unidades} · ${pesosClp(pieza.precio)} c/u</div>
                    ${noVerificado}
                    ${motivo ? `<p class="small mb-0 mt-1">${escaparHtml(motivo)}</p>` : ''}
                </li>`;
        }).join('');
        const listaAvisos = avisos.map(texto => {
            let clase = 'text-warning';
            if (esAvisoNoVerificado(texto)) {
                clase = 'text-info';
            } else if (esAvisoVisible(texto)) {
                clase = 'text-danger';
            }
            return `<li class="${clase}">${escaparHtml(texto)}</li>`;
        }).join('');
        const criterios = (propuesta.criterios || []).map(texto => `<li>${escaparHtml(texto)}</li>`).join('');
        const estado = estadoRecomendacion(propuesta);
        return `
            <p class="recomendacion-precio fw-bold text-success mb-1">${pesosClp(propuesta.total)}</p>
            <p class="recomendacion-estado ${estado.clase} mb-2"><i class="fas ${estado.icono}" aria-hidden="true"></i> ${escaparHtml(estado.texto)}</p>
            <p class="small mb-2">${escaparHtml(propuesta.explicacion || '')}</p>
            <p class="small text-muted mb-3">Puntaje interno del algoritmo: ${escaparHtml(propuesta.puntaje)}. No es un benchmark de rendimiento.</p>
            <ul class="list-unstyled recomendacion-detalle-lista mb-3">${filas}</ul>
            ${listaAvisos ? `<h6 class="small fw-bold">Comprobaciones y advertencias</h6><ul class="small mb-3">${listaAvisos}</ul>` : ''}
            ${criterios ? `<h6 class="small fw-bold">Criterios del puntaje</h6><ul class="small text-muted mb-0">${criterios}</ul>` : ''}`;
    }

    // --- 6. INICIAR TODO ---
    iniciarRecomendador();
    addToCartBtn.addEventListener('click', addAllToCart);
    downloadExcelBtn.addEventListener('click', downloadAsExcel);
    initializeBuilder();
    const pendiente = leerPropuestaPendienteLocal();
    const aplicarAlEntrar = new URLSearchParams(window.location.search).get('aplicar') === '1';
    if (pendiente) {
        revalidarPropuesta(pendiente).then(function (validada) {
            if (!validada || !validada.componentes) {
                showToast('La propuesta expiró o ya no es válida con el catálogo actual.', 'error');
                if (window.HWChatSession) {
                    window.HWChatSession.setProposalPending(null, rootUserKey());
                }
                return;
            }
            const propuesta = validada.proposal_pending || { componentes: validada.componentes };
            if (aplicarAlEntrar && !builderTienePiezas()) {
                if (aplicarSeleccionDesdeApi(validada.componentes)) {
                    limpiarPropuestaAplicada();
                    showToast('Armado aplicado. Puedes agregarlo al carrito o exportar el Excel.');
                }
                return;
            }
            mostrarBannerPropuestaPendiente(propuesta, {
                reemplazar: aplicarAlEntrar && builderTienePiezas(),
            });
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarArmado);
} else {
    iniciarArmado();
}