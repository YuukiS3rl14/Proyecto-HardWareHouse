function iniciarArmado() {
    // --- 1. OBTENER DATOS Y ELEMENTOS DEL DOM ---
    const allComponentsData = JSON.parse(document.getElementById('componentes-data').textContent);
    const urls = document.getElementById('builder-urls').dataset;
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

        updateSummaryAndTotal();
    }

    function htmlAlmacenamiento(label) {
        const hay = discos.length > 0;
        const visual = hay ? estadoVisual(piezaEvaluada('almacenamiento')) : { status: '', icon: '' };
        const detalle = hay ? htmlDetallePieza('almacenamiento') : '';
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
                            <h5 class="font-weight-bold ${visual.status}">${visual.icon}${label}</h5>
                            <img src="${urls.placeholderImg}" alt="Almacenamiento">
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
        const visual = hay ? estadoVisual(piezaEvaluada('memoria_ram')) : { status: '', icon: '' };
        const detalle = hay ? htmlDetallePieza('memoria_ram') : '';
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
                            <h5 class="font-weight-bold ${visual.status}">${visual.icon}${label}</h5>
                            <img src="${urls.placeholderImg}" alt="Memoria RAM">
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
        const image = component && component.imagen ? component.imagen : urls.placeholderImg;

        let compatibilityStatus = '';
        let compatibilityIcon = '';
        let compatibilityDetail = '';
        if (component) {
            const visual = estadoVisual(piezaEvaluada(key));
            compatibilityStatus = visual.status;
            compatibilityIcon = visual.icon;
            compatibilityDetail = htmlDetallePieza(key);
        }

        // Generar lista de especificaciones clave
        const specs = component ? getComponentSpecs(component, true) : '<li>Selecciona un producto</li>';

        return `
            <div class="col-lg-6 col-xl-4 mb-4">
                <div class="component-card-wrapper">
                    <div class="component-card">
                        <div class="info">
                            <h5 class="font-weight-bold ${compatibilityStatus}">${compatibilityIcon}${label}</h5>
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
    let recomendacionesActuales = [];
    let categoriaModal = null;

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

    async function openComponentModal(e) {
        const type = e.target.dataset.type;
        const modalTitle = document.getElementById('componentModalLabel');
        const modalBody = document.getElementById('componentModalBody');
        const { label } = componentOrder.find(c => c.key === type);
        categoriaModal = type;
        modoModal = e.target.dataset.modo || '';
        reemplazaId = e.target.dataset.reemplazaId || null;
        modalTitle.textContent = modoModal === 'reemplazar' ? `Reemplazar ${label}` : `Seleccionar ${label}`;
        modalBody.innerHTML = '<p class="text-muted mb-0">Revisando compatibilidad...</p>';
        $('#componentModal').modal('show');

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

    function renderRecomendaciones() {
        const modalBody = document.getElementById('componentModalBody');
        const visibles = soloCompatibles
            ? recomendacionesActuales.filter(candidato => candidato.estado === 'compatible')
            : recomendacionesActuales;

        let html = `
            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="solo-compatibles" ${soloCompatibles ? 'checked' : ''}>
                <label class="form-check-label" for="solo-compatibles">Solo compatibles</label>
            </div>
        `;

        if (visibles.length === 0) {
            html += htmlListaVacia();
        } else {
            html += '<div class="list-group">';
            visibles.forEach(candidato => {
                const local = (allComponentsData[categoriaModal] || []).find(componente => (
                    String(componente.id) === String(candidato.id) && componente.model_name === candidato.model_name
                )) || candidato;
                const price = parseInt(local.precio).toLocaleString('es-CL');
                const image = local.imagen ? local.imagen : urls.placeholderImg;
                const detalle = detalleRecomendacion(candidato);
                const etiquetaStock = candidato.seleccionable ? '' : '<span class="badge badge-secondary ml-2">Sin stock</span>';
                const clase = candidato.seleccionable ? 'list-group-item list-group-item-action' : 'list-group-item disabled';
                const tag = candidato.seleccionable ? 'a' : 'div';
                const href = candidato.seleccionable ? ' href="#"' : '';
                html += `
                    <${tag}${href} class="${clase}" data-id="${candidato.id}" data-type="${categoriaModal}" data-model-name="${escaparHtml(candidato.model_name)}" data-seleccionable="${candidato.seleccionable ? '1' : '0'}">
                        <div class="d-flex w-100">
                            <img src="${escaparHtml(image)}" alt="${escaparHtml(local.nombre)}" style="width: 60px; height: 60px; object-fit: contain; margin-right: 15px;">
                            <div class="flex-grow-1">
                                <div class="d-flex justify-content-between">
                                    <h6 class="mb-1">${escaparHtml(local.nombre)}${etiquetaStock}</h6>
                                    <strong class="text-success">$${price}</strong>
                                </div>
                                <small class="text-muted">${getComponentSpecs(local, false)}</small>
                                ${detalle}
                            </div>
                        </div>
                    </${tag}>
                `;
            });
            html += '</div>';
        }

        modalBody.innerHTML = html;
        const filtro = document.getElementById('solo-compatibles');
        if (filtro) {
            filtro.addEventListener('change', () => {
                soloCompatibles = filtro.checked;
                renderRecomendaciones();
            });
        }
        modalBody.querySelectorAll('[data-seleccionable="1"]').forEach(item => {
            item.addEventListener('click', handleSelectionChange);
        });
        const quitarFiltro = document.getElementById('quitar-filtro-compatibles');
        if (quitarFiltro) {
            quitarFiltro.addEventListener('click', () => {
                soloCompatibles = false;
                renderRecomendaciones();
            });
        }
    }

    function htmlListaVacia() {
        if (recomendacionesActuales.length === 0 || !soloCompatibles) {
            return '<p class="text-muted mb-0">No hay piezas en esta categoría.</p>';
        }
        const estados = new Set(recomendacionesActuales.map(candidato => candidato.estado));
        const boton = '<button type="button" class="btn btn-link btn-sm p-0 align-baseline" id="quitar-filtro-compatibles">Mostrar todas</button>';
        const soloSinComprobar = [...estados].every(estado => estado === 'incompleto' || estado === 'no_evaluada');
        if (soloSinComprobar) {
            let causa = 'Faltan piezas o no hay reglas evaluables. Eso no significa que todas sean incompatibles.';
            if (estados.size === 1 && estados.has('no_evaluada')) {
                causa = 'Esta categoría no tiene reglas que el filtro pueda exigir. No se comprueban puertos SATA, ranuras M.2 ni bahías. Eso no significa que todas sean incompatibles.';
            } else if (categoriaModal === 'tarjeta_grafica') {
                causa = 'Selecciona un gabinete para comprobar el largo. Mientras falte, el filtro no puede mostrar estas GPU como compatibles. Eso no significa que todas sean incompatibles.';
            }
            return `<p class="text-muted mb-0">${causa} ${boton}</p>`;
        }
        const haySinComprobar = estados.has('incompleto') || estados.has('no_evaluada');
        const hayConflicto = estados.has('incompatible') || estados.has('datos_insuficientes');
        if (hayConflicto && haySinComprobar) {
            return `<p class="text-muted mb-0">Ninguna pieza cumple las reglas que ya se pueden comprobar. Otras siguen sin evaluarse; eso no las hace incompatibles. ${boton}</p>`;
        }
        return '<p class="text-muted mb-0">No hay piezas compatibles con la selección actual.</p>';
    }

    function detalleRecomendacion(candidato) {
        const avisos = (candidato.advertencias || []).map(texto => (
            `<p class="mb-0 text-warning"><small>${escaparHtml(texto)}</small></p>`
        )).join('');
        if (candidato.estado === 'compatible') {
            const pendientes = (candidato.pendientes || []).length
                ? `<p class="mb-0 text-muted"><small>Selección incompleta en reglas que aún no se pueden comprobar.</small></p>`
                : '';
            return `<p class="mb-0 mt-1 text-success"><small>${escaparHtml(candidato.etiqueta)}</small></p>${avisos}${pendientes}`;
        }
        if (candidato.estado === 'incompleto') {
            const pendientes = (candidato.pendientes || []).map(texto => `<p class="mb-0 text-muted"><small>${escaparHtml(texto)}</small></p>`).join('');
            return `<p class="mb-0 mt-1 text-muted"><small>${escaparHtml(candidato.etiqueta)}</small></p>${avisos}${pendientes}`;
        }
        if (candidato.estado === 'incompatible' || candidato.estado === 'datos_insuficientes') {
            const motivos = (candidato.motivos || []).map(motivo => `<p class="mb-0 mt-1 text-danger"><small>${escaparHtml(motivo)}</small></p>`).join('');
            const pendientes = (candidato.pendientes || []).map(texto => `<p class="mb-0 text-muted"><small>${escaparHtml(texto)}</small></p>`).join('');
            return `<p class="mb-0 mt-1 text-danger"><small>${escaparHtml(candidato.etiqueta)}</small></p>${motivos}${avisos}${pendientes}`;
        }
        return `<p class="mb-0 mt-1 text-muted"><small>${escaparHtml(candidato.etiqueta)}</small></p>${avisos}`;
    }

    function getComponentSpecs(component, isCard) {
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

        return isCard ? specs.map(s => `<li>${s}</li>`).join('') : specs.join(' | ');
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

        $('#componentModal').modal('hide');
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

    function htmlDetallePieza(key) {
        if (!evaluacionActual || evaluacionActual.pendiente) {
            return '<p class="mb-0 text-muted"><small>Consultando compatibilidad...</small></p>';
        }
        if (evaluacionActual.fallo) {
            return '<p class="mb-0 text-danger"><small>No se pudo consultar la compatibilidad.</small></p>';
        }
        const pieza = (evaluacionActual.piezas || {})[key];
        if (!pieza) {
            return '<p class="mb-0 text-danger"><small>No se pudo consultar la compatibilidad.</small></p>';
        }
        return detalleRecomendacion(pieza);
    }

    function estadoVisual(pieza) {
        if (!pieza) {
            return { status: '', icon: '' };
        }
        if (pieza.estado === 'incompatible' || pieza.estado === 'datos_insuficientes') {
            const titulo = escaparHtml((pieza.motivos || []).join(' ') || pieza.etiqueta);
            return {
                status: 'text-danger',
                icon: `<i class="fas fa-exclamation-triangle mr-1" title="${titulo}"></i>`,
            };
        }
        if (pieza.estado === 'compatible') {
            const titulo = escaparHtml(pieza.etiqueta);
            return {
                status: 'text-success',
                icon: `<i class="fas fa-check-circle mr-1" title="${titulo}"></i>`,
            };
        }
        return { status: 'text-muted', icon: '' };
    }

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
        summaryList.innerHTML = '';
        let total = 0;
        let componentCount = 0;

        componentOrder.forEach(({ key, label }) => {
            if (key === 'memoria_ram') {
                if (memorias.length === 0) {
                    return;
                }
                const subtotal = memorias.reduce((suma, ram) => suma + parseFloat(ram.precio) * ram.cantidad, 0);
                total += subtotal;
                componentCount += 1;
                const visual = estadoVisual(piezaEvaluada(key));
                const lineas = memorias.map(ram => (
                    `<p class="mb-0 small">${escaparHtml(ram.nombre)} × ${ram.cantidad}</p>`
                )).join('');
                const summaryItem = document.createElement('div');
                summaryItem.className = 'd-flex justify-content-between mb-2';
                summaryItem.innerHTML = `
                    <div class="pr-2">
                        <p class="mb-0 ${visual.status}">${visual.icon}${label}</p>
                        ${lineas}
                        <p class="mb-0 text-muted"><small>${escaparHtml(textoConteoRam())}</small></p>
                        ${htmlDetallePieza(key)}
                    </div>
                    <p class="mb-0">$${subtotal.toLocaleString('es-CL')}</p>
                `;
                summaryList.appendChild(summaryItem);
                return;
            }
            if (key === 'almacenamiento') {
                if (discos.length === 0) {
                    return;
                }
                const subtotal = discos.reduce((suma, disco) => suma + parseFloat(disco.precio) * disco.cantidad, 0);
                total += subtotal;
                componentCount += 1;
                const visual = estadoVisual(piezaEvaluada(key));
                const lineas = discos.map(disco => (
                    `<p class="mb-0 small">${escaparHtml(disco.nombre)} × ${disco.cantidad}</p>`
                )).join('');
                const summaryItem = document.createElement('div');
                summaryItem.className = 'd-flex justify-content-between mb-2';
                summaryItem.innerHTML = `
                    <div class="pr-2">
                        <p class="mb-0 ${visual.status}">${visual.icon}${label}</p>
                        ${lineas}
                        ${htmlDetallePieza(key)}
                    </div>
                    <p class="mb-0">$${subtotal.toLocaleString('es-CL')}</p>
                `;
                summaryList.appendChild(summaryItem);
                return;
            }
            const component = currentBuild[key];

            if (component) {
                const price = parseFloat(component.precio);
                total += price;
                componentCount++;

                const visual = estadoVisual(piezaEvaluada(key));
                const summaryItem = document.createElement('div');
                summaryItem.className = 'd-flex justify-content-between mb-2';
                summaryItem.innerHTML = `
                    <div class="pr-2">
                        <p class="mb-0 ${visual.status}">${visual.icon}${label}</p>
                        ${htmlDetallePieza(key)}
                    </div>
                    <p class="mb-0">$${price.toLocaleString('es-CL')}</p>
                `;
                summaryList.appendChild(summaryItem);
            }
        });

        if (componentCount > 0) {
            const nota = document.createElement('div');
            nota.className = 'mt-2';
            if (!evaluacionActual || evaluacionActual.pendiente) {
                nota.innerHTML = '<p class="mb-0 text-muted"><small>Consultando compatibilidad...</small></p>';
            } else if (evaluacionActual.fallo) {
                nota.innerHTML = '<p class="mb-0 text-danger"><small>No se pudo consultar la compatibilidad.</small></p>';
            } else {
                const motivos = (evaluacionActual.motivos || [])
                    .map(motivo => `<p class="mb-0 text-danger"><small>${escaparHtml(motivo)}</small></p>`)
                    .join('');
                const avisos = (evaluacionActual.advertencias || [])
                    .map(aviso => `<p class="mb-0 text-warning"><small>${escaparHtml(aviso)}</small></p>`)
                    .join('');
                nota.innerHTML = `<p class="mb-0"><small>${escaparHtml(evaluacionActual.texto)}</small></p>${motivos}${avisos}`;
            }
            summaryList.appendChild(nota);
        }

        totalPriceEl.textContent = `$${total.toLocaleString('es-CL')}`;

        // Habilitar/deshabilitar botones
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

    // --- 6. INICIAR TODO ---
    addToCartBtn.addEventListener('click', addAllToCart);
    downloadExcelBtn.addEventListener('click', downloadAsExcel);
    initializeBuilder();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarArmado);
} else {
    iniciarArmado();
}