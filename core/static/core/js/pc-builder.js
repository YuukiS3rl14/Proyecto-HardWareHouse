function iniciarArmado() {
    // --- 1. OBTENER DATOS Y ELEMENTOS DEL DOM ---
    const allComponentsData = JSON.parse(document.getElementById('componentes-data').textContent);
    const urls = document.getElementById('builder-urls').dataset;
    const builderContainer = document.getElementById('pc-builder');
    const summaryList = document.getElementById('summary-list');
    const totalPriceEl = document.getElementById('total-price');
    const addToCartBtn = document.getElementById('add-to-cart-btn');
    const downloadExcelBtn = document.getElementById('download-excel-btn');

    // Estado actual de la construcción
    let currentBuild = {};

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
        if (component) {
            const visual = estadoVisual(checkCompatibility(component, key));
            compatibilityStatus = visual.status;
            compatibilityIcon = visual.icon;
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
        initializeBuilder(); // Redibuja toda la interfaz con la nueva selección
        updateSummaryAndTotal();
    }

    function handleRemoveComponent(e) {
        const type = e.target.dataset.type;
        delete currentBuild[type];
        initializeBuilder();
        updateSummaryAndTotal();
    }

    const SOCKETS_CONOCIDOS = ['AM4', 'AM5', 'LGA1200', 'LGA1700'];
    const TIPOS_DDR = ['DDR3', 'DDR4', 'DDR5'];
    const FORMATOS = ['MINI-ITX', 'MICRO-ATX', 'ATX'];

    function normalizarSpec(valor) {
        return String(valor ?? '').trim().toUpperCase().replace(/\s+/g, '');
    }

    function peorEstado(actual, candidato) {
        const orden = { compatible: 0, incompleto: 1, datos_insuficientes: 2, incompatible: 3 };
        return orden[candidato] > orden[actual] ? candidato : actual;
    }

    function resumir(hallazgos) {
        const vigentes = hallazgos.filter(Boolean);
        if (vigentes.length === 0) {
            return { estado: 'compatible', isCompatible: true, warning: null };
        }
        const estado = vigentes.reduce((peor, hallazgo) => peorEstado(peor, hallazgo.estado), 'compatible');
        const aviso = vigentes.find(hallazgo => hallazgo.estado === estado && hallazgo.warning);
        return { estado, isCompatible: false, warning: aviso ? aviso.warning : null };
    }

    function estadoVisual(resultado) {
        if (resultado.estado === 'incompatible' || resultado.estado === 'datos_insuficientes') {
            const titulo = (resultado.warning || '').replace(/"/g, '&quot;');
            return {
                status: 'text-danger',
                icon: `<i class="fas fa-exclamation-triangle mr-1" title="${titulo}"></i>`,
            };
        }
        if (resultado.estado === 'compatible') {
            return {
                status: 'text-success',
                icon: '<i class="fas fa-check-circle mr-1" title="Compatible"></i>',
            };
        }
        return { status: '', icon: '' };
    }

    function evaluarSocket(cpuPresente, socketCpu, placaPresente, socketPlaca, mensajeIncompatible) {
        if (!cpuPresente || !placaPresente) {
            return { estado: 'incompleto', warning: null };
        }
        const cpu = normalizarSpec(socketCpu);
        const placa = normalizarSpec(socketPlaca);
        if (!SOCKETS_CONOCIDOS.includes(cpu) || !SOCKETS_CONOCIDOS.includes(placa)) {
            return { estado: 'datos_insuficientes', warning: 'No se puede verificar el socket: un valor Otro o desconocido no es compatible.' };
        }
        if (cpu !== placa) {
            return { estado: 'incompatible', warning: mensajeIncompatible };
        }
        return null;
    }

    function evaluarRam(ramPresente, tipoRam, placaPresente, tipoPlaca, mensajeIncompatible) {
        if (!ramPresente || !placaPresente) {
            return { estado: 'incompleto', warning: null };
        }
        const ram = normalizarSpec(tipoRam);
        const placa = normalizarSpec(tipoPlaca);
        if (!TIPOS_DDR.includes(ram) || !TIPOS_DDR.includes(placa)) {
            return { estado: 'datos_insuficientes', warning: 'No se puede verificar la RAM porque el tipo DDR no es conocido.' };
        }
        if (ram !== placa) {
            return { estado: 'incompatible', warning: mensajeIncompatible };
        }
        return null;
    }

    function evaluarFormato(placaPresente, formatoPlaca, gabinetePresente, formatoGabinete, mensajeIncompatible) {
        if (!placaPresente || !gabinetePresente) {
            return { estado: 'incompleto', warning: null };
        }
        const indicePlaca = FORMATOS.indexOf(normalizarSpec(formatoPlaca));
        const indiceGabinete = FORMATOS.indexOf(normalizarSpec(formatoGabinete));
        if (indicePlaca === -1 || indiceGabinete === -1) {
            return { estado: 'datos_insuficientes', warning: 'No se puede verificar el formato porque no es un formato conocido.' };
        }
        if (indiceGabinete < indicePlaca) {
            return { estado: 'incompatible', warning: mensajeIncompatible };
        }
        return null;
    }

    function evaluarCoolerContra(socketsConocidos, socketObjetivo, mensajeIncompatible) {
        const objetivo = normalizarSpec(socketObjetivo);
        if (!SOCKETS_CONOCIDOS.includes(objetivo) || socketsConocidos.length === 0) {
            return { estado: 'datos_insuficientes', warning: 'No se puede verificar el cooler: faltan sockets conocidos.' };
        }
        if (!socketsConocidos.includes(objetivo)) {
            return { estado: 'incompatible', warning: mensajeIncompatible };
        }
        return null;
    }

    function checkCompatibility(component, type) {
        if (type === 'tarjeta_grafica' || type === 'almacenamiento' || type === 'fuente_de_poder') {
            return { estado: 'no_evaluada', isCompatible: false, warning: null };
        }

        const placaMadre = currentBuild.placa_madre;
        const procesador = currentBuild.procesador;
        const gabinete = currentBuild.gabinete;
        const ram = currentBuild.memoria_ram;
        const hallazgos = [];

        if (type === 'procesador') {
            hallazgos.push(evaluarSocket(
                true, component.socket, !!placaMadre, placaMadre && placaMadre.socket_cpu,
                `Socket incompatible (requiere ${placaMadre ? placaMadre.socket_cpu : ''})`
            ));
        } else if (type === 'placa_madre') {
            hallazgos.push(evaluarSocket(
                !!procesador, procesador && procesador.socket, true, component.socket_cpu,
                `Socket incompatible (requiere ${procesador ? procesador.socket : ''})`
            ));
            hallazgos.push(evaluarFormato(
                true, component.formato, !!gabinete, gabinete && gabinete.formato_soporte,
                'Formato incompatible con gabinete'
            ));
            hallazgos.push(evaluarRam(
                !!ram, ram && ram.tipo_ddr, true, component.tipo_ram_soportado,
                `Tipo RAM incompatible (requiere ${ram ? ram.tipo_ddr : ''})`
            ));
        } else if (type === 'memoria_ram') {
            hallazgos.push(evaluarRam(
                true, component.tipo_ddr, !!placaMadre, placaMadre && placaMadre.tipo_ram_soportado,
                `Tipo de RAM incompatible (requiere ${placaMadre ? placaMadre.tipo_ram_soportado : ''})`
            ));
        } else if (type === 'refrigeracion_cooler') {
            if (!procesador && !placaMadre) {
                hallazgos.push({ estado: 'incompleto', warning: null });
            } else {
                const sockets = String(component.socket_compatibles || '').split(',').map(normalizarSpec).filter(Boolean);
                const conocidos = sockets.filter(socket => SOCKETS_CONOCIDOS.includes(socket));
                if (procesador) {
                    hallazgos.push(evaluarCoolerContra(
                        conocidos, procesador.socket,
                        `Incompatible con socket de CPU (${procesador.socket})`
                    ));
                }
                if (placaMadre) {
                    hallazgos.push(evaluarCoolerContra(
                        conocidos, placaMadre.socket_cpu,
                        `Incompatible con socket de Placa (${placaMadre.socket_cpu})`
                    ));
                }
            }
        } else if (type === 'gabinete') {
            hallazgos.push(evaluarFormato(
                !!placaMadre, placaMadre && placaMadre.formato, true, component.formato_soporte,
                `No soporta formato de Placa Madre (${placaMadre ? placaMadre.formato : ''})`
            ));
        }

        return resumir(hallazgos);
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

                // Añadir al resumen
                const visual = estadoVisual(checkCompatibility(component, key));
                const compatibilityStatus = visual.status;
                const compatibilityIcon = visual.icon;
                const summaryItem = document.createElement('div');
                summaryItem.className = 'd-flex justify-content-between mb-2';
                summaryItem.innerHTML = `
                    <p class="mb-0 ${compatibilityStatus}">${compatibilityIcon}${label}</p>
                    <p class="mb-0">$${price.toLocaleString('es-CL')}</p>
                `;
                summaryList.appendChild(summaryItem);
            }
        });

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

    function downloadAsExcel() {
        // 1. Determinar dinámicamente todas las columnas de atributos
        const baseHeaders = ['Componente', 'Producto', 'Cantidad', 'Precio Unitario'];
        const attributeHeaders = new Set();
        const componentsToExport = [];
        let estadoReglas = null;
        let hayPiezaSinRegla = false;
        const etiquetasEstado = {
            compatible: 'Compatible',
            incompatible: 'Incompatible (Revisar Componentes)',
            datos_insuficientes: 'Datos insuficientes (no se declara compatible)',
            incompleto: 'Selección incompleta',
            no_evaluada: 'Compatibilidad no evaluada',
        };

        // Recopilar todos los componentes y sus atributos
        componentOrder.forEach(({ key, label }) => {
            const component = currentBuild[key];
            if (component) {
                componentsToExport.push({ label, component });
                const estadoPieza = checkCompatibility(component, key).estado;
                if (estadoPieza === 'no_evaluada') {
                    hayPiezaSinRegla = true;
                } else {
                    estadoReglas = estadoReglas ? peorEstado(estadoReglas, estadoPieza) : estadoPieza;
                }
                // Recopilar cabeceras de atributos
                Object.keys(component).forEach(attr => {
                    if (!['id', 'nombre', 'precio', 'imagen', 'stock', 'model_name'].includes(attr)) {
                        attributeHeaders.add(attr);
                    }
                });
            }
        });

        const finalHeaders = baseHeaders.concat(Array.from(attributeHeaders).sort());

        // 2. Construir las filas de datos
        const data = [finalHeaders];
        let totalBuildPrice = 0;

        componentsToExport.forEach(({ label, component }) => {
            const quantity = 1; // Cantidad es siempre 1 en el armador
            const price = parseInt(component.precio);
            totalBuildPrice += price * quantity;

            const row = [label, component.nombre, quantity, price];
            // Añadir valores de atributos en el orden correcto
            Array.from(attributeHeaders).sort().forEach(header => {
                row.push(component[header] || '-');
            });
            data.push(row);
        });

        // 3. Añadir filas de resumen al final
        data.push([]); // Fila vacía como separador
        let textoCompatibilidad = etiquetasEstado.no_evaluada;
        if (estadoReglas === 'compatible' && hayPiezaSinRegla) {
            textoCompatibilidad = 'Reglas comprobadas; hay piezas sin regla de compatibilidad';
        } else if (estadoReglas) {
            textoCompatibilidad = etiquetasEstado[estadoReglas] || estadoReglas;
        }
        data.push(['', 'Compatibilidad del Armado:', textoCompatibilidad]);
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