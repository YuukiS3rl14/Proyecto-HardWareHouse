document.addEventListener('DOMContentLoaded', function () {
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

        // Listeners para los botones de acción
        addToCartBtn.addEventListener('click', addAllToCart);
        downloadExcelBtn.addEventListener('click', downloadAsExcel);
    }

    function createComponentCardHTML(key, label, component) {
        const price = component ? `$${parseInt(component.precio).toLocaleString('es-CL')}` : '-';
        const name = component ? component.nombre : `No seleccionado`;
        const image = component && component.imagen ? component.imagen : urls.placeholderImg;

        let compatibilityStatus = '';
        let compatibilityIcon = '';
        if (component) {
            const { isCompatible, warning } = checkCompatibility(component, key);
            if (!isCompatible) {
                compatibilityStatus = 'text-danger';
                compatibilityIcon = `<i class="fas fa-exclamation-triangle mr-1" title="${warning}"></i>`;
            } else {
                compatibilityStatus = 'text-success';
                compatibilityIcon = `<i class="fas fa-check-circle mr-1" title="Compatible"></i>`;
            }
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

    function openComponentModal(e) {
        const type = e.target.dataset.type;
        const modalTitle = document.getElementById('componentModalLabel');
        const modalBody = document.getElementById('componentModalBody');

        const { label } = componentOrder.find(c => c.key === type);
        modalTitle.textContent = `Seleccionar ${label}`;

        const sortedComponents = [...allComponentsData[type]].sort((a, b) => parseFloat(a.precio) - parseFloat(b.precio));
        
        let listHTML = '<div class="list-group">';
        sortedComponents.forEach(component => {
            const { isCompatible, warning } = checkCompatibility(component, type);
            const price = parseInt(component.precio).toLocaleString('es-CL');
            const image = component.imagen ? component.imagen : urls.placeholderImg;
            listHTML += `
                <a href="#" class="list-group-item list-group-item-action" data-id="${component.id}" data-type="${type}">
                    <div class="d-flex w-100">
                        <img src="${image}" alt="${component.nombre}" style="width: 60px; height: 60px; object-fit: contain; margin-right: 15px;">
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between">
                                <h6 class="mb-1">${component.nombre}</h6>
                                <strong class="text-success">$${price}</strong>
                            </div>
                            <small class="text-muted">${getComponentSpecs(component, false)}</small>
                            ${warning ? `<p class="mb-0 mt-1 text-danger"><small>⚠️ ${warning}</small></p>` : ''}
                        </div>
                    </div>
                </a>
            `;
        });
        listHTML += '</div>';

        modalBody.innerHTML = listHTML;

        // Añadir listeners a los items de la lista
        modalBody.querySelectorAll('.list-group-item').forEach(item => {
            item.addEventListener('click', handleSelectionChange);
        });

        $('#componentModal').modal('show');
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
        // Refrigeración
        if (component.tipo) specs.push(`Tipo: ${component.tipo}`);
        if (component.tamanho_radiador_mm) specs.push(`Radiador: ${component.tamanho_radiador_mm}mm`);

        return isCard ? specs.map(s => `<li>${s}</li>`).join('') : specs.join(' | ');
    }

    function handleSelectionChange(e) {
        e.preventDefault();
        const target = e.currentTarget;
        const type = target.dataset.type;
        const selectedId = target.dataset.id;

        currentBuild[type] = allComponentsData[type].find(c => c.id == selectedId);

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

    function checkCompatibility(component, type) {
        const placaMadre = currentBuild.placa_madre;
        const procesador = currentBuild.procesador;
        const gabinete = currentBuild.gabinete;
        const ram = currentBuild.memoria_ram;

        // Lógica de compatibilidad
        switch (type) {
            case 'procesador':
                if (placaMadre && component.socket !== placaMadre.socket_cpu) {
                    return { isCompatible: false, warning: `Socket incompatible (requiere ${placaMadre.socket_cpu})` };
                }
                break;

            case 'placa_madre':
                if (procesador && component.socket_cpu !== procesador.socket) {
                    return { isCompatible: false, warning: `Socket incompatible (requiere ${procesador.socket})` };
                }
                if (gabinete && !isFormatoCompatible(component.formato, gabinete.formato_soporte)) {
                    return { isCompatible: false, warning: `Formato incompatible con gabinete` };
                }
                if (ram && component.tipo_ram_soportado !== ram.tipo_ddr) {
                    return { isCompatible: false, warning: `Tipo RAM incompatible (requiere ${ram.tipo_ddr})` };
                }
                break;

            case 'memoria_ram':
                if (placaMadre && component.tipo_ddr !== placaMadre.tipo_ram_soportado) {
                    return { isCompatible: false, warning: `Tipo de RAM incompatible (requiere ${placaMadre.tipo_ram_soportado})` };
                }
                break;

            case 'refrigeracion_cooler':
                const socketsCompatibles = component.socket_compatibles.split(',').map(s => s.trim());
                if (procesador && !socketsCompatibles.includes(procesador.socket)) {
                     return { isCompatible: false, warning: `Incompatible con socket de CPU (${procesador.socket})` };
                }
                if (placaMadre && !socketsCompatibles.includes(placaMadre.socket_cpu)) {
                    return { isCompatible: false, warning: `Incompatible con socket de Placa (${placaMadre.socket_cpu})` };
                }
                break;
            
            case 'gabinete':
                if (placaMadre && !isFormatoCompatible(placaMadre.formato, component.formato_soporte)) {
                    return { isCompatible: false, warning: `No soporta formato de Placa Madre (${placaMadre.formato})` };
                }
                break;
        }

        return { isCompatible: true, warning: null };
    }

    function isFormatoCompatible(formatoPlaca, formatoGabinete) {
        // Un gabinete más grande puede albergar una placa más pequeña.
        const formatos = ['Mini-ITX', 'Micro-ATX', 'ATX'];
        const indicePlaca = formatos.indexOf(formatoPlaca);
        const indiceGabinete = formatos.indexOf(formatoGabinete);
        return indiceGabinete >= indicePlaca;
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
                let compatibilityStatus = '';
                let compatibilityIcon = '';
                const { isCompatible, warning } = checkCompatibility(component, key);
                if (!isCompatible && warning) { // Solo mostrar advertencia si hay un warning específico
                    compatibilityStatus = 'text-danger';
                    compatibilityIcon = `<i class="fas fa-exclamation-triangle mr-1" title="${warning}"></i>`;
                } else if (isCompatible) { // Solo mostrar check si es compatible
                    compatibilityStatus = 'text-success';
                    compatibilityIcon = `<i class="fas fa-check-circle mr-1" title="Compatible"></i>`;
                }
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

        // Usamos un bucle for...of con await para procesar las peticiones en secuencia
        for (const [type, component] of items) {
            const formData = new FormData();
            const { modelName } = componentOrder.find(c => c.key === type);

            formData.append('product_id', component.id);
            formData.append('model_name', modelName);
            formData.append('quantity', 1);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            try {
                const response = await fetch(urls.addToCartUrl, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                });
                const data = await response.json();
                console.log(`Agregado: ${component.nombre}`, data);
            } catch (error) {
                // Si el error es un SyntaxError, probablemente la respuesta no fue JSON (ej. un 404 HTML)
                if (error instanceof SyntaxError) {
                    console.error(`Error de parseo JSON al agregar ${component.nombre}. Posiblemente un error del servidor o URL incorrecta.`, error);
                    alert(`Hubo un error de comunicación con el servidor al agregar ${component.nombre}. Por favor, inténtalo de nuevo.`);
                } else {
                    console.error(`Error agregando ${component.nombre}:`, error);
                    alert(`Hubo un error al agregar ${component.nombre} al carrito.`);
                }
                alert(`Hubo un error al agregar ${component.nombre} al carrito.`);
                return; // Detener si hay un error
            }
        }

        showToast('¡Componentes agregados! Redirigiendo al carrito...');
        // Esperamos un momento para que el usuario vea el toast antes de redirigir
        setTimeout(() => {
            window.location.href = '/carrito/';
        }, 1500);
    }

    function downloadAsExcel() {
        // 1. Determinar dinámicamente todas las columnas de atributos
        const baseHeaders = ['Componente', 'Producto', 'Cantidad', 'Precio Unitario'];
        const attributeHeaders = new Set();
        const componentsToExport = [];
        let isBuildCompatible = true;

        // Recopilar todos los componentes y sus atributos
        componentOrder.forEach(({ key, label }) => {
            const component = currentBuild[key];
            if (component) {
                componentsToExport.push({ label, component });
                // Comprobar compatibilidad general
                if (!checkCompatibility(component, key).isCompatible) {
                    isBuildCompatible = false;
                }
                // Recopilar cabeceras de atributos
                Object.keys(component).forEach(attr => {
                    if (!['id', 'nombre', 'precio', 'imagen', 'stock'].includes(attr)) {
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
        data.push(['', 'Compatibilidad del Armado:', isBuildCompatible ? 'Compatible' : 'Incompatible (Revisar Componentes)']);
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
    initializeBuilder();
});