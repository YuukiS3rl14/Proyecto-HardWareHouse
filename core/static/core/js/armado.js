// Helpers
function formatCLP(value) {
    if (!value || isNaN(value)) return '—';
    return value.toLocaleString('es-CL', { style: 'currency', currency: 'CLP' });
}

function getSelectedInfo(selectEl) {
    var opt = selectEl.options[selectEl.selectedIndex];
    return {
        name: opt.value || null,
        price: parseInt(opt.dataset.price || 0, 10),
        img: opt.dataset.img || 'img/placeholder.png'
    };
}

// Elementos
const selects = {
    cpu: document.getElementById('select-cpu'),
    gpu: document.getElementById('select-gpu'),
    ram: document.getElementById('select-ram'),
    storage: document.getElementById('select-storage'),
    psu: document.getElementById('select-psu'),
    case: document.getElementById('select-case')
};

const pricesEls = {
    cpu: document.getElementById('price-cpu'),
    gpu: document.getElementById('price-gpu'),
    ram: document.getElementById('price-ram'),
    storage: document.getElementById('price-storage'),
    psu: document.getElementById('price-psu'),
    case: document.getElementById('price-case')
};

const imgs = {
    cpu: document.getElementById('img-cpu'),
    gpu: document.getElementById('img-gpu'),
    ram: document.getElementById('img-ram'),
    storage: document.getElementById('img-storage'),
    psu: document.getElementById('img-psu'),
    case: document.getElementById('img-case')
};

const thumbs = {
    cpu: { img: document.getElementById('thumb-cpu'), txt: document.getElementById('thumb-cpu-txt') },
    gpu: { img: document.getElementById('thumb-gpu'), txt: document.getElementById('thumb-gpu-txt') },
    ram: { img: document.getElementById('thumb-ram'), txt: document.getElementById('thumb-ram-txt') },
    storage: { img: document.getElementById('thumb-storage'), txt: document.getElementById('thumb-storage-txt') },
    psu: { img: document.getElementById('thumb-psu'), txt: document.getElementById('thumb-psu-txt') },
    case: { img: document.getElementById('thumb-case'), txt: document.getElementById('thumb-case-txt') }
};

const totalEl = document.getElementById('total-clp');
const btnGenerate = document.getElementById('btn-generate');
const btnReset = document.getElementById('btn-reset');
const resultContainer = document.getElementById('result-container');
const summaryBody = document.getElementById('summary-body');
const summaryTotal = document.getElementById('summary-total');
const btnCloseSummary = document.getElementById('btn-close-summary');
const btnDownload = document.getElementById('btn-download');

// Sumar precios y actualizar UI
function updateAll() {
    let total = 0;
    Object.keys(selects).forEach(key => {
        const info = getSelectedInfo(selects[key]);
        pricesEls[key].innerText = info.price ? formatCLP(info.price) : '—';
        imgs[key].src = info.img;
        // thumbs
        thumbs[key].img.src = info.img;
        thumbs[key].txt.innerText = info.name || '—';
        total += info.price;
    });
    totalEl.innerText = formatCLP(total);
    return total;
}

// Inicializa listeners
Object.keys(selects).forEach(key => {
    selects[key].addEventListener('change', updateAll);
});

// Reset
btnReset.addEventListener('click', function () {
    Object.keys(selects).forEach(k => { selects[k].selectedIndex = 0; });
    updateAll();
    resultContainer.style.display = 'none';
    summaryBody.innerHTML = '';
});

// Generar resumen (tabla)
btnGenerate.addEventListener('click', function () {
    const rows = [];
    let total = 0;
    Object.keys(selects).forEach(key => {
        const info = getSelectedInfo(selects[key]);
        if (info.name) {
            rows.push({ component: key.toUpperCase(), name: info.name, price: info.price });
            total += info.price;
        } else {
            rows.push({ component: key.toUpperCase(), name: 'Sin selección', price: 0 });
        }
    });

    // Rellenar tabla
    summaryBody.innerHTML = '';
    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + r.component + '</td><td>' + r.name + '</td><td>' + (r.price ? formatCLP(r.price) : '-') + '</td>';
        summaryBody.appendChild(tr);
    });

    summaryTotal.innerText = formatCLP(total);
    resultContainer.style.display = 'block';
    window.scrollTo({ top: resultContainer.offsetTop - 20, behavior: 'smooth' });
});

// Cerrar resumen
btnCloseSummary.addEventListener('click', function () { resultContainer.style.display = 'none'; });

// Descargar CSV
btnDownload.addEventListener('click', function () {
    const lines = [];
    lines.push(['Componente', 'Selección', 'Precio CLP']);
    Object.keys(selects).forEach(key => {
        const info = getSelectedInfo(selects[key]);
        lines.push([key.toUpperCase(), info.name || 'Sin selección', info.price ? info.price : 0]);
    });
    // total
    const total = Object.keys(selects).reduce((acc, k) => acc + getSelectedInfo(selects[k]).price, 0);
    lines.push([]); lines.push(['Total', '', total]);

    const csvContent = lines.map(l => l.map(cell => `"${(cell + '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resumen_armado_techparts.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Inicializar vista
updateAll();