import * as THREE from 'three';
import { GLTFLoader } from '../vendor/GLTFLoader.js';

const modelosGlb = new Map();
const geometrias = new Map();
let escala = 9.82;
const oyentes = new Set();
let cargas = 0;

const ARCHIVOS = {
    placa: 'motherboard/motherboard-light.glb',
    cpu: 'cpu/cpu.glb',
    ram: 'ram-stick/ram-stick.glb',
    gpu: 'graphics-card/graphics-card-light.glb',
    gpuCorta: 'graphics-card/gpu-dual-190.glb',
    gpuItx: 'graphics-card/gpu-mini-itx-170.glb',
    aire: 'cpu-cooler/cpu-cooler.glb',
    aireBajo: 'cpu-cooler/cooler-bajo-58.glb',
    fuente: 'power-supply-unit/power-supply-unit.glb',
    fuenteSfx: 'power-supply-unit/sfx-power-supply.glb',
    ssd: 'ssd/ssd.glb',
    hdd: 'hard-drive/hard-drive.glb',
};

const EJES = {
    placa: [new THREE.Vector3(0, -1, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1)],
    cpu: [new THREE.Vector3(0, 1, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, -1)],
    ram: [new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 1), new THREE.Vector3(1, 0, 0)],
    gpu: [new THREE.Vector3(0, 0, -1), new THREE.Vector3(0, 1, 0), new THREE.Vector3(1, 0, 0)],
    aire: [new THREE.Vector3(0, -1, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1)],
    aireBajo: [new THREE.Vector3(0, -1, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1)],
    m2: [new THREE.Vector3(0, 0, 1), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0)],
    fuente: [new THREE.Vector3(-1, 0, 0), new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, -1)],
};

const APOYO = {
    placa: 'bandeja',
    cpu: 'sobre',
    ram: 'sobre',
    aire: 'sobre',
    m2: 'sobre',
    gpu: 'ranura',
    gpu2: 'ranura',
    sata: 'suelo',
    hdd: 'suelo',
    fuente: 'sueloTrasero',
};

// Coordenadas en metros del archivo, no del gabinete.
// Placa: eje X del archivo hacia abajo de la placa, Y hacia los componentes, Z hacia el frente.
const REFERENCIA = {
    gabinete: {
        id: 'respaldo',
        archivo: 'gabinete/pc-case.glb',
        bandejaX: -0.96,
        techoY: 1.9,
        traseraZ: -2.28,
        sueloY: -2.27,
        fuente: { x: 0.05, z: -2.34 },
        hdd: { x: -0.2, z: 0.05, paso: 0.2 },
        sata: { x: 0.42, z: -0.35, paso: 0.12 },
    },
    placa: {
        alto: 0.305,
        zMin: -0.12474450469017029,
        zMax: 0.12200001627206802,
        relieveCpu: 0.0044,
        socket: { x: -0.067, y: 0.009, z: -0.0187 },
        dimm: [
            { x: -0.052, y: 0.006, z: 0.0715 },
            { x: -0.052, y: 0.006, z: 0.062 },
            { x: -0.052, y: 0.006, z: 0.051 },
            { x: -0.052, y: 0.006, z: 0.0415 },
        ],
        pcie: { x: 0.005, y: 0.009, z: -0.07 },
        m2: { x: 0.084, y: 0.002, z: 0.071, pasoX: 0, pasoZ: -0.028 },
    },
};

// Punto del modelo, en metros de su archivo, que debe coincidir con el ancla.
const PIVOTE = {
    aire: { x: 0, y: 0, z: -0.013 },
    aireBajo: { x: 0, y: 0, z: 0 },
    cpu: { x: -0.0249, y: 0, z: 0.0015 },
    ram: { x: 0, y: 0.0032, z: -0.0197 },
    gpu: { x: 0.1438, y: 0.0086, z: -0.0676 },
    gpu2: { x: 0.0025, y: 0.02, z: 0 },
    gpuCorta: { x: 0.001, y: 0.0008, z: -0.0014 },
    gpuItx: { x: 0.001, y: 0.0008, z: -0.0014 },
};

// Rotación propia (determinante 1). El signo negativo en X endereza la placa sin
// convertir una reflexión en cuaternión, que la dejaba acostada.
const EJES_ATX = [new THREE.Vector3(0, -1, 0), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1)];
const SIGNO_ATX = [-1, 1, 1];

const PLACAS = {
    ATX: {
        archivo: 'motherboard/atx-motherboard.glb',
        ejes: EJES_ATX,
        ejesM2: EJES_ATX,
        signo: SIGNO_ATX,
        signoM2: SIGNO_ATX,
        factor: 1,
        conservar: true,
        ocultar: ['Socket_protective_cap'],
        pivote: { x: 0.1525, y: 0, z: -0.122 },
        pivoteM2: { x: 0.046992, y: 0, z: 0.04969 },
        alto: 0.305,
        fondo: 0.244,
        referencia: {
            relieveCpu: 0.0044,
            socket: { x: 0.236, y: 0.0076, z: -0.15 },
            dimm: [
                { x: 0.2182, y: 0.004, z: -0.1015 },
                { x: 0.2182, y: 0.004, z: -0.093 },
                { x: 0.2182, y: 0.004, z: -0.0825 },
                { x: 0.2182, y: 0.004, z: -0.074 },
            ],
            pcie: { x: 0.1283, y: 0.0065, z: -0.23305 },
            // Cara superior del PCB de este archivo: 2,21 mm. El módulo apoya 0,15 mm más arriba.
            m2: [
                { x: 0.172, y: 0.00236, z: -0.1155 },
                { x: 0.097, y: 0.00236, z: -0.0205 },
                { x: 0.052, y: 0.00236, z: -0.0205 },
            ],
        },
    },
    'Micro-ATX': {
        archivo: 'motherboard/matx-motherboard.glb',
        ejes: EJES_ATX,
        ejesM2: EJES_ATX,
        signo: SIGNO_ATX,
        signoM2: SIGNO_ATX,
        factor: 1,
        conservar: true,
        ocultar: ['Socket_protective_cap'],
        pivote: { x: 0.183002, y: 0, z: -0.121999 },
        pivoteM2: { x: 0.046992, y: 0, z: 0.04969 },
        alto: 0.244005,
        fondo: 0.244006,
        retraso: 0,
        referencia: {
            relieveCpu: 0.0044,
            socket: { x: 0.236, y: 0.0076, z: -0.15 },
            dimm: [
                { x: 0.2182, y: 0.004, z: -0.1015 },
                { x: 0.2182, y: 0.004, z: -0.093 },
                { x: 0.2182, y: 0.004, z: -0.0825 },
                { x: 0.2182, y: 0.004, z: -0.074 },
            ],
            pcie: { x: 0.1283, y: 0.0065, z: -0.23305 },
            m2: [
                { x: 0.172, y: 0.00236, z: -0.1155 },
                { x: 0.097, y: 0.00236, z: -0.0205 },
            ],
        },
    },
    'Mini-ITX': {
        archivo: 'motherboard/mini-itx-motherboard.glb',
        ejes: EJES_ATX,
        ejesM2: EJES_ATX,
        signo: SIGNO_ATX,
        signoM2: SIGNO_ATX,
        factor: 1,
        conservar: true,
        pivote: { x: 0.085, y: 0, z: -0.085 },
        // Mismo recorte 22 × 80 mm que ATX/Micro-ATX (geometriaDe m2). El pivote por
        // ranura apunta al extremo del módulo 2280 que entra en el conector.
        pivoteM2: { x: 0.046992, y: 0, z: 0.04969 },
        alto: 0.170,
        fondo: 0.170,
        // En el mid-tower la placa baja 18,7 mm para la PCIe; el escudo de E/S se
        // compensa +18,7 mm en X del modelo para seguir en la abertura trasera.
        compensarES: 0.0187,
        referencia: {
            relieveCpu: 0.0044,
            socket: { x: 0.108, y: 0.0076, z: -0.100 },
            dimm: [
                { x: 0.085, y: 0.004, z: -0.048 },
                { x: 0.085, y: 0.004, z: -0.039 },
            ],
            // Extremo trasero de la ranura, a 10,9 mm del borde, igual que la PCIe superior ATX.
            pcie: { x: 0.012, y: 0.0065, z: -0.15905 },
            // Cara superior del PCB: 1,6 mm. Módulo M.2 2280 (no el SSD de 2,5").
            // Frontal: conector hacia −Z, cuerpo hacia el frente. Posterior: reverso.
            m2: [
                { x: 0.055, y: 0.00175, z: -0.153, pivote: { x: 0.046992, y: 0, z: -0.03 } },
                { x: 0.051, y: 0, z: -0.057, pivote: { x: 0.046992, y: 0, z: -0.03 }, reverso: true },
            ],
        },
    },
};

// Interior del mid-tower, en el espacio local del grupo del gabinete.
// La malla se encaja en la carcasa procedural; estas cifras se miden ahí.
const GABINETE_MID = {
    id: 'mid-tower',
    archivo: 'gabinete/mid-tower.glb',
    propios: true,
    bandejaX: -0.769,
    techoY: 2.166,
    traseraZ: -2.414,
    sueloY: -2.21,
    fuente: { x: 0.15, y: -2.2145, z: -2.42 },
    // HDD en la jaula, delante de la fuente. El SSD de 2,5" va sobre la cubierta.
    hdd: { x: 0.13, y: -2.177, z: -0.08, paso: 0, pasoY: 0.283 },
    sata: { x: -0.252, y: -1.360, z: 1.15, paso: 0, pasoX: 0.768 },
};

// Interior del Mini-ITX, en metros del archivo ya centrado (pies en Y = 0).
// No tiene bahías de 3,5" ni de 2,5". La fuente ocupa la abertura SFX trasera.
const GABINETE_ITX = {
    id: 'mini-itx',
    archivo: 'gabinete/mini-itx.glb',
    compacto: true,
    enMetros: true,
    bandejaX: -0.078,
    techoY: 0.2836,
    traseraZ: -0.1861977468729019,
    sueloY: 0.011,
    fuente: { x: 0.05675, y: 0.016, z: -0.18769774687290192 },
};

export function fichaGabinete(formato) {
    if (formato === 'Micro-ATX' || formato === 'ATX') {
        return GABINETE_MID;
    }
    if (formato === 'Mini-ITX') {
        return GABINETE_ITX;
    }
    return REFERENCIA.gabinete;
}

function urlModelo(ruta) {
    const url = new URL(`../modelos/${ruta}`, import.meta.url);
    url.searchParams.set('v', 'piezas38');
    return url;
}

function cargarModelo(url) {
    const clave = url.href;
    if (!modelosGlb.has(clave)) {
        const cargador = new GLTFLoader();
        const pendiente = cargador.loadAsync(clave).catch((error) => {
            modelosGlb.delete(clave);
            throw error;
        });
        modelosGlb.set(clave, pendiente);
    }
    return modelosGlb.get(clave);
}

function rastrear(promesa) {
    const aviso = document.getElementById('pc-visualizador-carga');
    cargas += 1;
    if (aviso) {
        aviso.textContent = 'Cargando modelo…';
        aviso.hidden = false;
    }
    return promesa.finally(() => {
        cargas -= 1;
        if (aviso && cargas <= 0) {
            aviso.hidden = true;
        }
    });
}

export function fijarEscala(valor) {
    if (!Number.isFinite(valor) || valor <= 0) {
        return;
    }
    escala = valor;
    oyentes.forEach((oyente) => oyente(valor));
}

export function metros() {
    return escala;
}

export function alEscalar(fn) {
    oyentes.add(fn);
}

function fichaPlaca(formato) {
    return PLACAS[formato] || PLACAS.ATX;
}

export function posePlaca(formato, formatoCaja) {
    const ficha = fichaPlaca(formato);
    const gabinete = fichaGabinete(formatoCaja || formato);
    const m = escala * ficha.factor;
    const bandeja = gabinete.enMetros ? gabinete.bandejaX * escala : gabinete.bandejaX;
    const techo = gabinete.enMetros ? gabinete.techoY * escala : gabinete.techoY;
    const trasera = gabinete.enMetros ? gabinete.traseraZ * escala : gabinete.traseraZ;
    const pose = ficha.pivote
        ? new THREE.Vector3(
            bandeja,
            techo - ficha.alto * m / 2,
            trasera + ficha.fondo * m / 2,
        )
        : new THREE.Vector3(
            bandeja,
            techo - ficha.referencia.alto * m / 2,
            trasera + (ficha.referencia.zMax - ficha.referencia.zMin) * m / 2,
        );
    if (ficha.retraso) {
        pose.z -= ficha.retraso;
    }
    // Con el borde superior alineado, esta PCIe queda 18,7 mm por encima de la
    // ranura superior ATX. En el mid-tower se baja la placa para que el bracket
    // entre en esa ranura; el escudo de E/S se reconpensa en crearPiezaGlb.
    // El gabinete compacto conserva su altura y el escudo sin desplazar.
    if (formato === 'Mini-ITX' && gabinete.propios) {
        pose.y -= (ficha.compensarES || 0.0187) * m;
    }
    return pose;
}

export function puntoM2(formato, indice) {
    const lista = fichaPlaca(formato).referencia.m2;
    if (!Array.isArray(lista) || !lista.length) {
        return null;
    }
    return lista[Math.min(indice || 0, lista.length - 1)];
}

function enPlaca(fx, fy, fz, formato, formatoCaja) {
    const ficha = fichaPlaca(formato);
    const m = escala * ficha.factor;
    const base = posePlaca(formato, formatoCaja);
    if (ficha.pivote) {
        const pivote = ficha.pivote;
        const signo = ficha.signo || [1, 1, 1];
        const local = new THREE.Vector3(
            (fx - pivote.x) * m * signo[0],
            (fy - pivote.y) * m * signo[1],
            (fz - pivote.z) * m * signo[2],
        );
        return base.clone().add(
            new THREE.Vector3()
                .addScaledVector(ficha.ejes[0], local.x)
                .addScaledVector(ficha.ejes[1], local.y)
                .addScaledVector(ficha.ejes[2], local.z),
        );
    }
    const placa = ficha.referencia;
    const zMedia = (placa.zMin + placa.zMax) / 2;
    return new THREE.Vector3(base.x + fy * m, base.y - fx * m, base.z + (fz - zMedia) * m);
}

export function anclaPlaca(clave, formato, indice, formatoCaja) {
    const caja = formatoCaja || formato;
    const placa = fichaPlaca(formato).referencia;
    if (clave === 'dimm') {
        const punto = placa.dimm[indice];
        return punto ? enPlaca(punto.x, punto.y, punto.z, formato, caja) : null;
    }
    if (clave === 'm2') {
        const lista = placa.m2;
        if (Array.isArray(lista)) {
            const punto = lista[Math.min(indice || 0, lista.length - 1)];
            return punto ? enPlaca(punto.x, punto.y, punto.z, formato, caja) : null;
        }
        const i = indice || 0;
        return enPlaca(lista.x + lista.pasoX * i, lista.y, lista.z + lista.pasoZ * i, formato, caja);
    }
    const punto = placa[clave];
    return enPlaca(punto.x, punto.y, punto.z, formato, caja);
}

export function asientoCooler(formato, formatoCaja) {
    const placa = fichaPlaca(formato).referencia;
    const socket = placa.socket;
    return enPlaca(socket.x, socket.y + placa.relieveCpu, socket.z, formato, formatoCaja || formato);
}

// Alto ATX de 86 mm, pasado a la escala del mid-tower.
// pc-case.glb mide 0,4804 m y el mid-tower 0,4916 m; la pieza conserva
// la escala del primero, así que esta razón evita que los 86 mm
// queden más altos que la bahía de 86,2 mm.
const ALTO_FUENTE_ATX = 0.086;
const RELACION_GABINETE = 0.4803999960422516 / 0.49160003662109375;

function altoFuenteEnEscena(escalaPieza) {
    return ALTO_FUENTE_ATX * escalaPieza * RELACION_GABINETE;
}

export function puesto(clave, indice, formato) {
    const gabinete = fichaGabinete(formato);
    const i = indice || 0;
    if (clave === 'fuente') {
        const y = Number.isFinite(gabinete.fuente.y) ? gabinete.fuente.y : gabinete.sueloY;
        const punto = new THREE.Vector3(gabinete.fuente.x, y, gabinete.fuente.z);
        return gabinete.enMetros ? punto.multiplyScalar(escala) : punto;
    }
    const bahia = gabinete[clave];
    const altura = Number.isFinite(bahia.y) ? bahia.y : gabinete.sueloY;
    return new THREE.Vector3(
        bahia.x + (bahia.pasoX || 0) * i,
        altura + (bahia.pasoY || 0) * i,
        bahia.z + (bahia.paso || 0) * i,
    );
}

function compactar(geometria, conservar) {
    const posicion = geometria.getAttribute('position');
    const indice = geometria.getIndex();
    const total = indice ? indice.count : posicion.count;
    const mapa = new Map();
    const orden = [];
    const indices = [];
    const identificar = (vertice) => {
        if (!mapa.has(vertice)) {
            mapa.set(vertice, orden.length);
            orden.push(vertice);
        }
        return mapa.get(vertice);
    };
    for (let i = 0; i < total; i += 3) {
        const a = indice ? indice.getX(i) : i;
        const b = indice ? indice.getX(i + 1) : i + 1;
        const c = indice ? indice.getX(i + 2) : i + 2;
        const promedio = (posicion.getX(a) + posicion.getX(b) + posicion.getX(c)) / 3;
        if (!conservar(promedio)) {
            continue;
        }
        indices.push(identificar(a), identificar(b), identificar(c));
    }
    const resultado = new THREE.BufferGeometry();
    Object.keys(geometria.attributes).forEach((nombre) => {
        const atributo = geometria.getAttribute(nombre);
        const datos = new atributo.array.constructor(orden.length * atributo.itemSize);
        orden.forEach((origen, destino) => {
            for (let componente = 0; componente < atributo.itemSize; componente += 1) {
                datos[destino * atributo.itemSize + componente] = atributo.getComponent(origen, componente);
            }
        });
        resultado.setAttribute(nombre, new THREE.BufferAttribute(datos, atributo.itemSize, atributo.normalized));
    });
    resultado.setIndex(indices);
    resultado.computeBoundingBox();
    resultado.userData.descartable = true;
    return resultado;
}

function geometriaDe(tipo, malla) {
    if (geometrias.has(tipo)) {
        return geometrias.get(tipo);
    }
    let geometria = malla.geometry;
    if (tipo === 'cpu') {
        geometria = compactar(malla.geometry, (x) => x < -0.001);
    } else if (tipo === 'm2') {
        geometria = compactar(malla.geometry, (x) => x > 0.015);
    } else if (tipo === 'sata') {
        geometria = compactar(malla.geometry, (x) => x < 0.008);
    }
    geometrias.set(tipo, geometria);
    return geometria;
}

function ejeFino(malla) {
    if (!malla.geometry.boundingBox) {
        malla.geometry.computeBoundingBox();
    }
    const tamano = malla.geometry.boundingBox.getSize(new THREE.Vector3());
    if (tamano.x <= tamano.y && tamano.x <= tamano.z) {
        return 'x';
    }
    if (tamano.y <= tamano.x && tamano.y <= tamano.z) {
        return 'y';
    }
    return 'z';
}

function materialOscuro(previo, color, metalness, roughness) {
    return new THREE.MeshStandardMaterial({
        color,
        map: previo && previo.map ? previo.map : null,
        normalMap: previo && previo.normalMap ? previo.normalMap : null,
        normalScale: previo && previo.normalScale ? previo.normalScale.clone() : new THREE.Vector2(1, 1),
        roughnessMap: previo && previo.roughnessMap ? previo.roughnessMap : null,
        metalnessMap: previo && previo.metalnessMap ? previo.metalnessMap : null,
        roughness: roughness == null ? (previo && previo.roughness != null ? previo.roughness : 0.55) : roughness,
        metalness: metalness == null ? (previo && previo.metalness != null ? previo.metalness : 0.35) : metalness,
        emissive: previo && previo.emissive ? previo.emissive.clone() : new THREE.Color(0x000000),
        emissiveMap: previo && previo.emissiveMap ? previo.emissiveMap : null,
        emissiveIntensity: previo && previo.emissiveMap ? 0.42 : (previo && previo.emissiveIntensity) || 0,
        envMapIntensity: 0,
        side: THREE.DoubleSide,
    });
}

function estilizar(gltf, tipo) {
    const clave = tipo === 'm2' || tipo === 'sata' ? 'ssd' : tipo;
    if (gltf.userData.estilizado === clave) {
        return;
    }
    const raiz = gltf.scene;
    const cuerpo = {
        placa: 0x3e4854,
        cpu: 0xd5d8dc,
        ram: 0x2c3138,
        gpu: 0x1a1c22,
        aire: 0x16181c,
        fuente: 0x3a4046,
        m2: 0x5a626a,
        sata: 0x8a9096,
        hdd: 0x4e565e,
    }[tipo] || 0x4a515a;
    raiz.traverse((nodo) => {
        if (!nodo.isMesh) {
            return;
        }
        const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
        nodo.material = lista.map((material) => {
            const nombre = ((material && material.name) || '').toLowerCase();
            if (nombre.includes('rgb') || nombre.includes('light')) {
                const copia = material.clone();
                let color = 0x5ee7ff;
                if (nombre.includes('pink') || nombre.includes('lila')) {
                    color = 0xb388ff;
                } else if (nombre.includes('blue')) {
                    color = 0x4d7dff;
                }
                copia.color = new THREE.Color(color);
                copia.emissive = new THREE.Color(color);
                copia.emissiveIntensity = 1.05;
                copia.roughness = 0.35;
                return copia;
            }
            if (nombre.includes('blade')) {
                return materialOscuro(material, 0x1a1e24, 0.2, 0.48);
            }
            if (nombre.includes('hub')) {
                const nucleo = materialOscuro(material, 0x1c2430, 0.35, 0.25);
                nucleo.emissive = new THREE.Color(0x8b6cff);
                nucleo.emissiveIntensity = 0.75;
                return nucleo;
            }
            if (tipo === 'ram') {
                return materialOscuro(material, 0x16181c, 0.4, 0.42);
            }
            if (tipo === 'aire' || tipo === 'aireBajo') {
                return materialOscuro(material, 0x8d98a4, 0.46, 0.62);
            }
            return materialOscuro(material, cuerpo, null, null);
        });
        if (nodo.material.length === 1) {
            nodo.material = nodo.material[0];
        }
        nodo.castShadow = true;
        nodo.receiveShadow = true;
        if ((nodo.name || '').includes('rotor')) {
            nodo.userData.ventilador = true;
            nodo.userData.eje = ejeFino(nodo);
        }
    });
    if (tipo === 'hdd') {
        const tapa = raiz.getObjectByName('hard-drive_cover');
        if (tapa && !tapa.userData.cerrada) {
            tapa.rotation.z -= 105 * Math.PI / 180;
            tapa.userData.cerrada = true;
        }
    }
    gltf.userData.estilizado = clave;
}

function distinguirM2(modelo) {
    const pcb = new THREE.Color(0x1f8f4a);
    const chip = new THREE.Color(0x14161a);
    const dedo = new THREE.Color(0xd7b15a);
    modelo.traverse((nodo) => {
        if (!nodo.isMesh || !nodo.geometry || nodo.userData.tornilloM2) {
            return;
        }
        const geometria = nodo.geometry.clone();
        const posiciones = geometria.getAttribute('position');
        const colores = new Float32Array(posiciones.count * 3);
        const tono = new THREE.Color();
        for (let i = 0; i < posiciones.count; i += 1) {
            if (posiciones.getY(i) > 0.001) {
                tono.copy(chip);
            } else if (posiciones.getZ(i) > 0.04) {
                tono.copy(dedo);
            } else {
                tono.copy(pcb);
            }
            colores[i * 3] = tono.r;
            colores[i * 3 + 1] = tono.g;
            colores[i * 3 + 2] = tono.b;
        }
        geometria.setAttribute('color', new THREE.BufferAttribute(colores, 3));
        nodo.geometry = geometria;
        nodo.material = new THREE.MeshStandardMaterial({
            vertexColors: true,
            roughness: 0.62,
            metalness: 0.08,
            envMapIntensity: 0,
            side: THREE.DoubleSide,
        });
    });
}

function pulirMicroAtx(modelo) {
    modelo.traverse((nodo) => {
        if (!nodo.isMesh || !nodo.material) {
            return;
        }
        const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
        const nuevas = lista.map((material) => {
            if (!material) {
                return material;
            }
            const nombre = (material.name || '').toLowerCase();
            const copia = material.clone();
            if (nombre.includes('pcb') || nombre.includes('solder') || nombre.includes('laminate')) {
                copia.roughness = 0.82;
                copia.metalness = 0.05;
                return copia;
            }
            if (nombre.includes('heatsink') || nombre.includes('aluminium') || nombre.includes('aluminum')) {
                copia.roughness = 0.4;
                copia.metalness = Math.max(copia.metalness || 0, 0.58);
                return copia;
            }
            if (nombre.includes('light')) {
                copia.emissiveIntensity = Math.max(copia.emissiveIntensity || 0, 0.7);
                return copia;
            }
            return material;
        });
        nodo.material = nuevas.length === 1 ? nuevas[0] : nuevas;
    });
}

// Sube el escudo y los puertos en el espacio del modelo para anular el descenso
// de la placa Mini-ITX en el mid-tower. No toca el PCB ni la ranura PCIe.
function compensarEscudoMiniItx(modelo, deltaX) {
    if (!(deltaX > 0)) {
        return;
    }
    modelo.traverse((nodo) => {
        if (!nodo.isMesh || !nodo.geometry) {
            return;
        }
        // GLTFLoader quita la barra de «E/S», así que el nodo llega como «ES».
        const nombre = (nodo.name || '').toLowerCase();
        if (nombre !== 'es' && nombre !== 'puertos') {
            return;
        }
        const geometria = nodo.geometry.clone();
        const posiciones = geometria.getAttribute('position');
        for (let i = 0; i < posiciones.count; i += 1) {
            posiciones.setX(i, posiciones.getX(i) + deltaX);
        }
        posiciones.needsUpdate = true;
        geometria.computeBoundingBox();
        geometria.computeBoundingSphere();
        nodo.geometry = geometria;
    });
}

function colocar(modelo, tipo, opciones) {
    const padre = modelo.parent;
    if (padre) {
        padre.remove(modelo);
    }
    modelo.position.set(0, 0, 0);
    modelo.rotation.set(0, 0, 0);
    modelo.scale.set(1, 1, 1);
    const ficha = tipo === 'placa' || tipo === 'm2' ? fichaPlaca((opciones || {}).formato) : null;
    const ejes = (ficha && (tipo === 'm2' ? ficha.ejesM2 : ficha.ejes)) || EJES[tipo];
    if (ejes) {
        modelo.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(ejes[0], ejes[1], ejes[2]));
    } else {
        modelo.quaternion.identity();
    }
    const uniforme = escala * (ficha && tipo === 'placa' ? ficha.factor : 1);
    let signo = (tipo === 'm2' && ficha && ficha.signoM2)
        || (tipo === 'placa' && ficha && ficha.signo)
        || null;
    if (Array.isArray(signo) && tipo === 'm2' && (opciones || {}).reverso) {
        signo = [signo[0], -signo[1], signo[2]];
    }
    if (signo) {
        modelo.scale.set(uniforme * signo[0], uniforme * signo[1], uniforme * signo[2]);
    } else {
        const alto = (tipo === 'gpu' || tipo === 'gpuItx') ? -uniforme : uniforme;
        modelo.scale.set(uniforme, alto, uniforme);
    }
    const formatoPieza = (opciones || {}).formato;
    if (tipo === 'fuente' && !(opciones || {}).sfx && (formatoPieza === 'Micro-ATX' || formatoPieza === 'ATX')) {
        modelo.updateMatrixWorld(true);
        const medida = new THREE.Box3().setFromObject(modelo);
        const altoMedido = medida.max.y - medida.min.y;
        const objetivo = altoFuenteEnEscena(uniforme);
        if (altoMedido > objetivo && objetivo > 0) {
            modelo.scale.y *= objetivo / altoMedido;
        }
    }
    const pivote = (tipo === 'm2' && (opciones || {}).pivote)
        || (tipo === 'm2' && ficha && ficha.pivoteM2)
        || (tipo === 'placa' && ficha && ficha.pivote)
        || PIVOTE[tipo];
    if (pivote) {
        modelo.updateMatrix();
        const punto = new THREE.Vector3(pivote.x, pivote.y, pivote.z).applyMatrix4(modelo.matrix);
        modelo.position.sub(punto);
    } else {
        modelo.updateMatrixWorld(true);
        const caja = new THREE.Box3().setFromObject(modelo);
        const centro = caja.getCenter(new THREE.Vector3());
        const modo = APOYO[tipo] || 'sobre';
        if (modo === 'sueloTrasero') {
            modelo.position.x -= centro.x;
            modelo.position.y -= caja.min.y;
            modelo.position.z -= caja.min.z;
        } else if (modo === 'suelo') {
            modelo.position.x -= centro.x;
            modelo.position.y -= caja.min.y;
            modelo.position.z -= centro.z;
        } else if (modo === 'ranura') {
            modelo.position.x -= caja.min.x;
            modelo.position.y -= centro.y;
            modelo.position.z -= caja.min.z;
        } else {
            modelo.position.x -= caja.min.x;
            modelo.position.y -= centro.y;
            modelo.position.z -= centro.z;
        }
    }
    if (padre) {
        padre.add(modelo);
    }
}

function aplicarGeometria(modelo, tipo) {
    if (tipo !== 'cpu' && tipo !== 'm2' && tipo !== 'sata') {
        return;
    }
    modelo.traverse((nodo) => {
        if (nodo.isMesh && nodo.geometry) {
            nodo.geometry = geometriaDe(tipo, nodo);
        }
    });
}

export function presentar(grupo, tipo, opciones) {
    const encajar = () => colocar(grupo, tipo, opciones || {});
    encajar();
    oyentes.add(encajar);
    grupo.userData.soltar = () => oyentes.delete(encajar);
    grupo.userData.origen = 'procedural';
    return grupo;
}

export function crearPiezaGlb(tipo, opciones, respaldo, alMontar) {
    const grupo = new THREE.Group();
    const procedural = respaldo();
    procedural.userData.respaldo = true;
    grupo.add(procedural);
    if (tipo === 'gpu' || tipo === 'gpuCorta' || tipo === 'gpuItx') {
        colocar(procedural, 'gpu2', opciones || {});
    }
    const ficha = tipo === 'placa' || tipo === 'm2' ? fichaPlaca((opciones || {}).formato) : null;
    const ruta = tipo === 'placa'
        ? ficha.archivo
        : (tipo === 'm2' || tipo === 'sata'
            ? ARCHIVOS.ssd
            : (tipo === 'fuente' && (opciones || {}).sfx
                ? ARCHIVOS.fuenteSfx
                : ARCHIVOS[tipo]));
    const promesa = rastrear(cargarModelo(urlModelo(ruta)).then((gltf) => {
        if (tipo !== 'gpuCorta' && tipo !== 'gpuItx' && !(tipo === 'placa' && ficha && ficha.conservar)) {
            estilizar(gltf, tipo);
        }
        const modelo = gltf.scene.clone(true);
        if (tipo === 'placa' && ficha && ficha.ocultar) {
            ficha.ocultar.forEach((nombre) => {
                const nodo = modelo.getObjectByName(nombre);
                if (nodo) {
                    nodo.removeFromParent();
                }
            });
        }
        if (tipo === 'placa' && ficha && (opciones || {}).formato === 'Micro-ATX') {
            pulirMicroAtx(modelo);
        }
        if (tipo === 'placa' && ficha && (opciones || {}).formato === 'Mini-ITX') {
            const caja = fichaGabinete((opciones || {}).formatoCaja || (opciones || {}).formato);
            if (caja && caja.propios) {
                compensarEscudoMiniItx(modelo, ficha.compensarES || 0.0187);
            }
        }
        if (tipo === 'gpuCorta' || tipo === 'gpuItx') {
            modelo.traverse((nodo) => {
                if (!nodo.isMesh) {
                    return;
                }
                nodo.castShadow = true;
                nodo.receiveShadow = true;
                if (tipo !== 'gpuItx') {
                    return;
                }
                const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
                lista.forEach((material) => {
                    if (material) {
                        material.side = THREE.DoubleSide;
                    }
                });
            });
        }
        if ((tipo === 'placa' || tipo === 'm2') && ficha && (ficha.signo || ficha.signoM2)) {
            modelo.traverse((nodo) => {
                if (!nodo.isMesh) {
                    return;
                }
                const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
                lista.forEach((material) => {
                    if (material) {
                        material.side = THREE.DoubleSide;
                    }
                });
            });
        }
        aplicarGeometria(modelo, tipo);
        procedural.traverse((nodo) => {
            if (nodo.userData && nodo.userData.ventilador && alMontar) {
                const indice = alMontar.indexOf ? alMontar.indexOf(nodo) : -1;
                if (indice >= 0) {
                    alMontar.splice(indice, 1);
                }
            }
        });
        modelo.traverse((nodo) => {
            if (nodo.userData && nodo.userData.ventilador && alMontar) {
                alMontar.push(nodo);
            }
        });
        const encajar = () => colocar(modelo, tipo, opciones || {});
        encajar();
        oyentes.add(encajar);
        grupo.userData.soltar = () => oyentes.delete(encajar);
        grupo.remove(procedural);
        const formatoM2 = (opciones || {}).formato;
        if (tipo === 'm2' && (formatoM2 === 'Micro-ATX' || formatoM2 === 'ATX' || formatoM2 === 'Mini-ITX')) {
            distinguirM2(modelo);
            if (formatoM2 === 'Micro-ATX' || formatoM2 === 'ATX') {
                const metalTornillo = new THREE.MeshStandardMaterial({
                    color: 0xf4f6f8, metalness: 0.12, roughness: 0.34, envMapIntensity: 0,
                });
                const ranura = new THREE.MeshStandardMaterial({
                    color: 0x23262b, metalness: 0.2, roughness: 0.55, envMapIntensity: 0,
                });
                const tornillo = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.00215, 0.00215, 0.0012, 14),
                    metalTornillo,
                );
                tornillo.position.set(0.046992, 0.00155, -0.0284);
                tornillo.userData.tornilloM2 = true;
                tornillo.castShadow = true;
                tornillo.receiveShadow = true;
                const corte = new THREE.Mesh(new THREE.BoxGeometry(0.0024, 0.00035, 0.00042), ranura);
                corte.position.set(0.046992, 0.0021, -0.0284);
                corte.userData.tornilloM2 = true;
                const corte2 = corte.clone();
                corte2.rotation.y = Math.PI / 2;
                modelo.add(tornillo, corte, corte2);
            }
        }
        grupo.add(modelo);
        grupo.userData.origen = 'glb';
        if (grupo.userData.marco) {
            grupo.remove(grupo.userData.marco);
            grupo.userData.marco = null;
        }
        if (typeof grupo.userData.remarcar === 'function') {
            grupo.userData.remarcar();
        }
    })).catch(() => {
        grupo.userData.origen = 'procedural';
    });
    grupo.userData.carga = promesa;
    return grupo;
}
