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
    let evaluacionActual = null;
    let consultaSerial = 0;

    // Orden y etiquetas de los componentes
    const componentOrder = [
        { key: 'placa_madre', label: 'Placa Madre', modelName: 'placa_madre' },
        { key: 'procesador', label: 'Procesador (CPU)', modelName: 'procesador' },
        { key: 'memoria_ram', label: 'Memoria RAM', modelName: 'memoria_ram' },
        { key: 'refrigeracion_cooler', label: 'Refrigeración CPU', modelName: 'refrigeracion' },
        { key: 'tarjeta_grafica', label: 'Tarjeta Gráfica (GPU)', modelName: 'tarjeta_grafica' },
        { key: 'almacenamiento', label: 'Almacenamiento', modelName: 'almacenamiento_ssd' }, // O hdd, se maneja en el carrito
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

        updateSummaryAndTotal();
    }

    function createComponentCardHTML(key, label, component) {
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
        return Object.entries(currentBuild).map(([type, component]) => {
            const { modelName } = componentOrder.find(c => c.key === type);
            return {
                tipo: component.model_name || modelName,
                id: component.id,
            };
        });
    }

    async function openComponentModal(e) {
        const type = e.target.dataset.type;
        const modalTitle = document.getElementById('componentModalLabel');
        const modalBody = document.getElementById('componentModalBody');
        const { label } = componentOrder.find(c => c.key === type);
        categoriaModal = type;
        modalTitle.textContent = `Seleccionar ${label}`;
        modalBody.innerHTML = '<p class="text-muted mb-0">Revisando compatibilidad...</p>';
        $('#componentModal').modal('show');

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        try {
            const response = await fetch(urls.recomendarUrl, {
                method: 'POST',
                body: JSON.stringify({
                    categoria: type,
                    componentes: seleccionActual(),
                }),
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
            html += '<p class="text-muted mb-0">No hay piezas compatibles con la selección actual.</p>';
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
    }

    function detalleRecomendacion(candidato) {
        if (candidato.estado === 'compatible') {
            const pendientes = (candidato.pendientes || []).length
                ? `<p class="mb-0 text-muted"><small>Selección incompleta en reglas que aún no se pueden comprobar.</small></p>`
                : '';
            return `<p class="mb-0 mt-1 text-success"><small>${escaparHtml(candidato.etiqueta)}</small></p>${pendientes}`;
        }
        if (candidato.estado === 'incompatible' || candidato.estado === 'datos_insuficientes') {
            const motivos = (candidato.motivos || []).map(motivo => `<p class="mb-0 mt-1 text-danger"><small>${escaparHtml(motivo)}</small></p>`).join('');
            return `<p class="mb-0 mt-1 text-danger"><small>${escaparHtml(candidato.etiqueta)}</small></p>${motivos}`;
        }
        const clase = candidato.estado === 'no_evaluada' ? 'text-muted' : 'text-muted';
        return `<p class="mb-0 mt-1 ${clase}"><small>${escaparHtml(candidato.etiqueta)}</small></p>`;
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
        if (component.ranuras_ram) specs.push(`Slots RAM: ${component.ranuras_ram}`);
        // RAM
        if (component.tipo_ddr) specs.push(`Tipo: ${component.tipo_ddr}`);
        if (component.velocidad_mhz) specs.push(`Velocidad: ${component.velocidad_mhz}MHz`);
        // GPU
        if (component.vram_gb) specs.push(`VRAM: ${component.vram_gb}GB`);
        if (component.tipo_memoria) specs.push(`Memoria: ${component.tipo_memoria}`);
        if (component.interfaz) specs.push(`Interfaz: ${component.interfaz}`);
        // Almacenamiento y otros con capacidad
        if (component.capacidad_gb) specs.push(`Capacidad: ${component.capacidad_gb}GB`);
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

        currentBuild[type] = allComponentsData[type].find(c => (
            String(c.id) === String(selectedId) && (!modelName || c.model_name === modelName)
        ));

        $('#componentModal').modal('hide');
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

    async function evaluacionParaExportar(componentes) {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
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
        if (!response.ok || data.status !== 'success' || !data.piezas || !data.texto) {
            return null;
        }
        return data;
    }

    // --- 4. ACTUALIZAR RESUMEN Y TOTAL ---

    function updateSummaryAndTotal() {
        summaryList.innerHTML = '';
        let total = 0;
        let componentCount = 0;

        componentOrder.forEach(({ key, label }) => {
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
                nota.innerHTML = `<p class="mb-0"><small>${escaparHtml(evaluacionActual.texto)}</small></p>${motivos}`;
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
        const items = Object.entries(currentBuild);
        if (items.length === 0) return;

        const componentes = items.map(([type, component]) => {
            const { modelName } = componentOrder.find(c => c.key === type);
            return {
                tipo: component.model_name || modelName,
                id: component.id,
            };
        });

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

        let evaluacionExportada;
        try {
            evaluacionExportada = await evaluacionParaExportar(componentes);
        } catch (error) {
            console.error('Error al evaluar el armado para Excel:', error);
            evaluacionExportada = null;
        }
        if (!evaluacionExportada) {
            alert('No se pudo consultar la compatibilidad. El Excel no se generó para no mostrar un resultado anterior.');
            return;
        }

        const baseHeaders = ['Componente', 'Producto', 'Cantidad', 'Precio Unitario', 'Compatibilidad'];
        const attributeHeaders = new Set();
        const componentsToExport = [];

        componentOrder.forEach(({ key, label }) => {
            const component = currentBuild[key];
            if (component) {
                componentsToExport.push({ key, label, component });
                Object.keys(component).forEach(attr => {
                    if (!['id', 'nombre', 'precio', 'imagen', 'stock', 'model_name'].includes(attr)) {
                        attributeHeaders.add(attr);
                    }
                });
            }
        });

        const piezas = evaluacionExportada.piezas;
        const faltaAlguna = componentsToExport.some(({ key }) => !piezas[key]);
        if (faltaAlguna) {
            alert('No se pudo consultar la compatibilidad. El Excel no se generó para no mostrar un resultado anterior.');
            return;
        }

        const finalHeaders = baseHeaders.concat(Array.from(attributeHeaders).sort());
        const data = [finalHeaders];
        let totalBuildPrice = 0;

        componentsToExport.forEach(({ key, label, component }) => {
            const quantity = 1;
            const price = parseInt(component.precio);
            totalBuildPrice += price * quantity;
            const pieza = piezas[key];
            const textos = [pieza.etiqueta]
                .concat(pieza.motivos || [])
                .concat(pieza.pendientes || [])
                .filter(Boolean);
            const row = [label, component.nombre, quantity, price, textos.join(' | ')];
            Array.from(attributeHeaders).sort().forEach(header => {
                row.push(component[header] || '-');
            });
            data.push(row);
        });

        data.push([]);
        data.push(['', 'Compatibilidad del Armado:', evaluacionExportada.texto]);
        (evaluacionExportada.motivos || []).forEach(motivo => {
            data.push(['', motivo]);
        });
        data.push(['', 'Precio Total del Armado:', totalBuildPrice]);

        // 4. Crear y descargar el archivo Excel
        const worksheet = XLSX.utils.aoa_to_sheet(data);
        worksheet['!cols'] = [{wch: 20}, {wch: 50}, {wch: 10}, {wch: 15}]; // Ancho para las primeras columnas
        worksheet['D1'].z = '$#,##0'; // Formato moneda para cabecera de Precio Unitario
        worksheet['C' + (data.length)].z = '$#,##0'; // Formato moneda para el Precio Total
        
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Mi Armado de PC');

        XLSX.writeFile(workbook, 'Mi_Armado_PC.xlsx');
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