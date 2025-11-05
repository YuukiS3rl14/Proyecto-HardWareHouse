document.addEventListener('DOMContentLoaded', function () {
    // --- 1. OBTENER DATOS Y ELEMENTOS DEL DOM ---
    const allComponentsData = JSON.parse(document.getElementById('componentes-data').textContent);
    const builderContainer = document.getElementById('pc-builder');
    const summaryList = document.getElementById('summary-list');
    const totalPriceEl = document.getElementById('total-price');

    // Estado actual de la construcción
    let currentBuild = {};

    // Orden y etiquetas de los componentes
    const componentOrder = [
        { key: 'placa_madre', label: 'Placa Madre' },
        { key: 'procesador', label: 'Procesador (CPU)' },
        { key: 'memoria_ram', label: 'Memoria RAM' },
        { key: 'refrigeracion_cooler', label: 'Refrigeración CPU' },
        { key: 'tarjeta_grafica', label: 'Tarjeta Gráfica (GPU)' },
        { key: 'almacenamiento', label: 'Almacenamiento' },
        { key: 'gabinete', label: 'Gabinete' },
        { key: 'fuente_de_poder', label: 'Fuente de Poder' },
    ];

    // --- 2. INICIALIZAR LA INTERFAZ ---
    function initializeBuilder() {
        componentOrder.forEach(({ key, label }) => {
            // Crear la fila para cada componente
            const row = document.createElement('div');
            row.className = 'component-row';
            row.innerHTML = `
                <div class="component-label">${label}</div>
                <div class="component-select">
                    <select class="form-control component-selector" data-type="${key}" id="select-${key}"></select>
                </div>
                <div class="component-price" id="price-${key}">$0</div>
            `;
            builderContainer.appendChild(row);

            // Inicializar Select2 en el nuevo select
            const selector = $(`#select-${key}`);
            selector.select2({
                theme: 'bootstrap-5',
                placeholder: `Selecciona un(a) ${label}`,
                allowClear: true
            });

            // Cargar las opciones iniciales
            updateOptions(key);

            // Añadir listener para cuando se selecciona un componente
            selector.on('change', handleSelectionChange);
        });
        updateSummaryAndTotal();
    }

    // --- 3. MANEJO DE EVENTOS Y LÓGICA DE COMPATIBILIDAD ---

    function handleSelectionChange(e) {
        const selectedId = e.target.value;
        const type = e.target.dataset.type;

        if (selectedId) {
            currentBuild[type] = allComponentsData[type].find(c => c.id == selectedId);
        } else {
            delete currentBuild[type];
        }

        // Re-evaluar la compatibilidad de todos los componentes
        componentOrder.forEach(({ key }) => {
            updateOptions(key);
        });

        updateSummaryAndTotal();
    }

    function updateOptions(type) {
        const selector = $(`#select-${type}`);
        const currentSelectionId = selector.val(); // Guardar la selección actual
        selector.empty(); // Limpiar opciones

        // Añadir opción por defecto
        selector.append(new Option('', '', true, true));

        allComponentsData[type].forEach(component => {
            let isCompatible = true; // Asumir compatible por defecto para depuración
            let warning = null;      // Asumir sin advertencia por defecto para depuración

            // Solo aplicar la lógica de compatibilidad si no estamos depurando o si es otro tipo de componente
            if (type !== 'placas_madre') { // O si quieres depurar solo placas madre, puedes cambiar esto
                const compatibilityResult = checkCompatibility(component, type);
                isCompatible = compatibilityResult.isCompatible;
                warning = compatibilityResult.warning;
            }
            
            let optionText = `${component.nombre} - $${parseInt(component.precio).toLocaleString('es-CL')}`;
            if (warning) {
                optionText += ` (⚠️ ${warning})`;
            }

            console.log(`DEBUG JS: Añadiendo opción para ${type}: ${optionText}, ID: ${component.id}, Compatible: ${isCompatible}`);
            const option = new Option(optionText, component.id, false, false);
            option.disabled = !isCompatible;

            selector.append(option);
        });

        // Restaurar la selección si todavía es válida
        if (currentSelectionId) {
            selector.val(currentSelectionId).trigger('change.select2');
        } else {
            selector.trigger('change.select2');
        }
    }

    function checkCompatibility(component, type) {
        const placaMadre = currentBuild.placas_madre;
        const procesador = currentBuild.procesadores;
        const gabinete = currentBuild.gabinetes;

        // Lógica de compatibilidad
        switch (type) {
            case 'procesadores':
                if (placaMadre && component.socket !== placaMadre.socket_cpu) {
                    return { isCompatible: false, warning: `Socket incompatible (requiere ${placaMadre.socket_cpu})` };
                }
                break;

            case 'placas_madre':
                if (procesador && component.socket_cpu !== procesador.socket) {
                    return { isCompatible: false, warning: `Socket incompatible (requiere ${procesador.socket})` };
                }
                if (gabinete && component.formato !== gabinete.formato_soporte) {
                    return { isCompatible: false, warning: `Formato incompatible con gabinete (requiere ${gabinete.formato_soporte})` };
                }
                break;

            case 'memorias_ram':
                if (placaMadre && component.tipo_ddr !== placaMadre.tipo_ram_soportado) {
                    return { isCompatible: false, warning: `Tipo de RAM incompatible (requiere ${placaMadre.tipo_ram_soportado})` };
                }
                break;

            case 'refrigeracion_cooler':
                if (procesador && !component.socket_compatibles.includes(procesador.socket)) {
                     return { isCompatible: false, warning: `Socket incompatible con CPU` };
                }
                if (placaMadre && !component.socket_compatibles.includes(placaMadre.socket_cpu)) {
                    return { isCompatible: false, warning: `Socket incompatible con Placa Madre` };
                }
                break;
            
            case 'gabinetes':
                if (placaMadre && component.formato_soporte !== placaMadre.formato) {
                    return { isCompatible: false, warning: `Formato incompatible con Placa Madre (requiere ${placaMadre.formato})` };
                }
                break;
        }

        // Si no hay advertencias, es compatible
        return { isCompatible: true, warning: null };
    }

    // --- 4. ACTUALIZAR RESUMEN Y TOTAL ---

    function updateSummaryAndTotal() {
        summaryList.innerHTML = '';
        let total = 0;

        componentOrder.forEach(({ key, label }) => {
            const component = currentBuild[key];
            const priceEl = document.getElementById(`price-${key}`);

            if (component) {
                const price = parseFloat(component.precio);
                total += price;

                // Actualizar precio en la fila del selector
                priceEl.textContent = `$${price.toLocaleString('es-CL')}`;

                // Añadir al resumen
                const summaryItem = document.createElement('div');
                summaryItem.className = 'd-flex justify-content-between';
                summaryItem.innerHTML = `
                    <p>${label}</p>
                    <p>$${price.toLocaleString('es-CL')}</p>
                `;
                summaryList.appendChild(summaryItem);

            } else {
                priceEl.textContent = '$0';
            }
        });

        totalPriceEl.textContent = `$${total.toLocaleString('es-CL')}`;
    }

    // --- 5. INICIAR TODO ---
    initializeBuilder();
});