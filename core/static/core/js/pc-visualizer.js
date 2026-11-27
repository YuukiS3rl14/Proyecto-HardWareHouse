import * as THREE from 'three';
import { OrbitControls } from '../vendor/OrbitControls.js';
import { GLTFLoader } from '../vendor/GLTFLoader.js';
import {
    alEscalar, anclaPlaca, asientoCooler, crearPiezaGlb, fichaGabinete, fijarEscala, metros, posePlaca, presentar, puntoM2, puesto,
} from './pc-modelos.js?v=piezas38';

const modelosGlb = new Map();

const CAJA = new THREE.BoxGeometry(1, 1, 1);
const CILINDRO = new THREE.CylinderGeometry(1, 1, 1, 18);
const TORO = new THREE.TorusGeometry(1, 0.11, 8, 28);
const ASPA = new THREE.BoxGeometry(1, 0.12, 0.28);
const dummy = new THREE.Object3D();

function materialesBase() {
    const metal = (color, rough, metalness) => new THREE.MeshStandardMaterial({
        color, roughness: rough, metalness, envMapIntensity: 0,
    });
    return {
        acero: metal(0x1a1a1a, 0.62, 0.22),
        aceroClaro: metal(0x8f8f8f, 0.42, 0.4),
        aluminio: metal(0xc2c2c2, 0.36, 0.48),
        cobre: metal(0xb87333, 0.28, 0.85),
        oro: metal(0xc6a15b, 0.35, 0.7),
        plastico: new THREE.MeshStandardMaterial({ color: 0x121212, roughness: 0.82, metalness: 0.02 }),
        plasticoClaro: new THREE.MeshStandardMaterial({ color: 0x3a3a3a, roughness: 0.7, metalness: 0.04 }),
        gpuCuerpo: new THREE.MeshStandardMaterial({ color: 0x23232b, roughness: 0.48, metalness: 0.22 }),
        gpuTapa: new THREE.MeshStandardMaterial({ color: 0x2e2e38, roughness: 0.42, metalness: 0.34 }),
        gpuBorde: new THREE.MeshStandardMaterial({ color: 0xc5ccd4, roughness: 0.58, metalness: 0.28 }),
        pcb: new THREE.MeshStandardMaterial({ color: 0x243038, roughness: 0.62, metalness: 0.08 }),
        pcbOscuro: new THREE.MeshStandardMaterial({ color: 0x1b2428, roughness: 0.6, metalness: 0.1 }),
        vidrio: vidrioNeutro(),
        led: new THREE.MeshStandardMaterial({
            color: 0xd7e8ff, emissive: 0x67e8ff, emissiveIntensity: 0.7, roughness: 0.4, metalness: 0.04,
        }),
        rgb: new THREE.MeshStandardMaterial({
            color: 0x241838, emissive: 0x8b6cff, emissiveIntensity: 0.9, roughness: 0.32, metalness: 0.12,
        }),
        seleccion: new THREE.MeshBasicMaterial({
            color: 0xd0d5dc, side: THREE.BackSide, depthTest: true,
        }),
    };
}

function caja(sx, sy, sz, material) {
    const malla = new THREE.Mesh(CAJA, material);
    malla.scale.set(sx, sy, sz);
    malla.castShadow = true;
    malla.receiveShadow = true;
    return malla;
}

function cilindro(radio, alto, material) {
    const malla = new THREE.Mesh(CILINDRO, material);
    malla.scale.set(radio, alto, radio);
    malla.castShadow = true;
    malla.receiveShadow = true;
    return malla;
}

function ventilador(radio, mat) {
    const grupo = new THREE.Group();
    grupo.userData.ventilador = true;
    const marco = new THREE.Mesh(TORO, mat.rgb);
    marco.scale.set(radio, radio, radio * 0.62);
    const aro = new THREE.Mesh(TORO, mat.acero);
    aro.scale.set(radio * 0.78, radio * 0.78, radio * 0.28);
    const cubo = cilindro(radio * 0.16, radio * 0.14, mat.gpuBorde);
    cubo.rotation.x = Math.PI / 2;
    const nucleo = cilindro(radio * 0.07, radio * 0.16, mat.rgb);
    nucleo.rotation.x = Math.PI / 2;
    const aspas = new THREE.InstancedMesh(ASPA, mat.plasticoClaro, 9);
    aspas.castShadow = true;
    for (let i = 0; i < 9; i += 1) {
        const angulo = (i / 9) * Math.PI * 2;
        dummy.position.set(Math.cos(angulo) * radio * 0.46, Math.sin(angulo) * radio * 0.46, 0);
        dummy.rotation.set(0.22, 0, angulo);
        dummy.scale.set(radio * 0.76, radio * 0.14, radio * 0.2);
        dummy.updateMatrix();
        aspas.setMatrixAt(i, dummy.matrix);
    }
    grupo.add(marco, aro, cubo, nucleo, aspas);
    return grupo;
}

function laminas(cantidad, ancho, alto, material) {
    const grupo = new THREE.Group();
    const malla = new THREE.InstancedMesh(CAJA, material, cantidad);
    malla.castShadow = true;
    for (let i = 0; i < cantidad; i += 1) {
        dummy.position.set(0, 0, (i - (cantidad - 1) / 2) * (ancho / cantidad));
        dummy.rotation.set(0, 0, 0);
        dummy.scale.set(0.012, alto, ancho * 0.92);
        dummy.updateMatrix();
        malla.setMatrixAt(i, dummy.matrix);
    }
    grupo.add(malla);
    return grupo;
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

function cajaLocal(raiz, incluir) {
    const inversa = new THREE.Matrix4().copy(raiz.matrixWorld).invert();
    const limites = new THREE.Box3();
    raiz.updateWorldMatrix(true, true);
    raiz.traverse((nodo) => {
        if (!nodo.isMesh || !nodo.geometry || (incluir && !incluir(nodo))) {
            return;
        }
        if (!nodo.geometry.boundingBox) {
            nodo.geometry.computeBoundingBox();
        }
        const cajaNodo = nodo.geometry.boundingBox.clone();
        cajaNodo.applyMatrix4(nodo.matrixWorld).applyMatrix4(inversa);
        limites.union(cajaNodo);
    });
    return limites;
}

function materialCuerpo(previo) {
    return new THREE.MeshStandardMaterial({
        color: 0x141414,
        roughness: 0.86,
        metalness: 0.04,
        normalMap: previo && previo.normalMap ? previo.normalMap : null,
        normalScale: previo && previo.normalScale ? previo.normalScale.clone() : new THREE.Vector2(1, 1),
        roughnessMap: previo && previo.roughnessMap ? previo.roughnessMap : null,
        metalnessMap: previo && previo.metalnessMap ? previo.metalnessMap : null,
        envMapIntensity: 0,
        side: THREE.DoubleSide,
    });
}

function colorAnillo(nombre) {
    const texto = (nombre || '').toLowerCase().replace(/_/g, ' ');
    if (texto.includes('fan 2')) {
        return 0x4d7dff;
    }
    if (texto.includes('fan 3') || texto.includes('power')) {
        return 0x5ee7ff;
    }
    return 0xb388ff;
}

function materialRgb(color, intensidad) {
    return new THREE.MeshStandardMaterial({
        color: 0x101014,
        emissive: color,
        emissiveIntensity: intensidad,
        roughness: 0.72,
        metalness: 0,
        envMapIntensity: 0,
        toneMapped: false,
    });
}

function vidrioNeutro() {
    return new THREE.MeshPhysicalMaterial({
        color: 0xb5b5b5,
        roughness: 0.07,
        metalness: 0,
        specularIntensity: 0.7,
        specularColor: new THREE.Color(0xffffff),
        clearcoat: 0.35,
        clearcoatRoughness: 0.2,
        transparent: true,
        opacity: 0.12,
        side: THREE.DoubleSide,
        depthWrite: false,
        envMapIntensity: 0,
    });
}

function prepararGabinete(raiz, mat, conservar) {
    const vidrios = [];
    raiz.traverse((nodo) => {
        if (!nodo.isMesh) {
            return;
        }
        const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
        const nombre = ((lista[0] && lista[0].name) || '').toLowerCase();
        const pieza = (nodo.name || '').toLowerCase();
        nodo.castShadow = true;
        nodo.receiveShadow = true;
        if (pieza.includes('rgb') || pieza.includes('light ring')) {
            nodo.material = materialRgb(colorAnillo(pieza), conservar ? 1.05 : 0.95);
            return;
        }
        if (conservar && pieza.includes('hub')) {
            nodo.material = materialRgb(colorAnillo(pieza), 0.62);
            nodo.material.color.setHex(0x12141a);
            nodo.material.roughness = 0.62;
            return;
        }
        if (pieza.includes('panel-vista')) {
            nodo.userData.esVidrio = true;
            nodo.userData.panel = 'vidrio';
            nodo.raycast = () => {};
            vidrios.push(nodo);
            return;
        }
        if (nodo.userData.esVidrio || nombre.includes('glass') || pieza.includes('side_panel_glass') || pieza.includes('tempered_glass')) {
            nodo.material = vidrioNeutro();
            nodo.castShadow = false;
            nodo.raycast = () => {};
            nodo.userData.esVidrio = true;
            vidrios.push(nodo);
            return;
        }
        if (nombre.includes('screw')) {
            nodo.material = new THREE.MeshStandardMaterial({
                color: 0xb7bcc4, roughness: 0.32, metalness: 0.72, envMapIntensity: 0,
            });
            return;
        }
        if (nombre.includes('border')) {
            nodo.material = new THREE.MeshStandardMaterial({
                color: 0x141414, roughness: 0.46, metalness: 0.3, envMapIntensity: 0, side: THREE.DoubleSide,
            });
            return;
        }
        if (conservar && lista[0] && lista[0].map) {
            const copia = lista[0].clone();
            copia.color = new THREE.Color(0xffffff);
            copia.emissive = new THREE.Color(0x000000);
            copia.emissiveIntensity = 0;
            copia.roughness = Math.max(copia.roughness == null ? 0.82 : copia.roughness, 0.8);
            copia.metalness = Math.min(copia.metalness == null ? 0.06 : copia.metalness, 0.1);
            copia.envMapIntensity = 0;
            copia.opacity = 1;
            copia.transparent = false;
            copia.side = THREE.DoubleSide;
            nodo.material = copia;
            nodo.userData.panel = (pieza.includes('psu shroud') || pieza.includes('psu_shroud')) ? 'cubierta' : 'cuerpo';
            return;
        }
        nodo.material = materialCuerpo(lista[0]);
        nodo.userData.panel = (pieza.includes('psu shroud') || pieza.includes('psu_shroud')) ? 'cubierta' : 'cuerpo';
    });
    return vidrios;
}

function iluminarMid(gabinete, envoltura) {
    const grupo = new THREE.Group();
    grupo.name = 'luces-mid';
    grupo.userData.adorno = true;
    envoltura.updateWorldMatrix(true, true);
    const inversa = new THREE.Matrix4().copy(gabinete.matrixWorld).invert();
    const volumen = new THREE.Box3().setFromObject(envoltura);
    volumen.applyMatrix4(inversa);
    const centro = volumen.getCenter(new THREE.Vector3());
    const tamano = volumen.getSize(new THREE.Vector3());
    const relleno = new THREE.PointLight(0xf6f5f2, 0.36, Math.max(tamano.y, 4.5), 2);
    relleno.position.set(centro.x + tamano.x * 0.14, centro.y + tamano.y * 0.04, centro.z - tamano.z * 0.02);
    const baja = new THREE.PointLight(0xf4f4f2, 0.16, Math.max(tamano.y * 0.55, 2.4), 2);
    baja.position.set(centro.x, volumen.min.y + tamano.y * 0.2, centro.z);
    grupo.add(relleno, baja);
    envoltura.traverse((nodo) => {
        const pieza = (nodo.name || '').toLowerCase();
        if (!nodo.isMesh || !pieza.includes('rgb')) {
            return;
        }
        const cajaAnillo = new THREE.Box3().setFromObject(nodo);
        if (cajaAnillo.isEmpty()) {
            return;
        }
        const luz = new THREE.PointLight(colorAnillo(pieza), 0.34, 1.15, 2);
        luz.position.copy(cajaAnillo.getCenter(new THREE.Vector3()).applyMatrix4(inversa));
        grupo.add(luz);
    });
    gabinete.add(grupo);
}

function controlVidrio(mallas) {
    return {
        get visible() {
            return mallas.length > 0 && mallas.every((malla) => malla.visible);
        },
        set visible(valor) {
            mallas.forEach((malla) => {
                malla.visible = valor;
            });
        },
    };
}

function reflejarBotonVidrio(visible) {
    const boton = document.getElementById('pc-visualizador-vidrio');
    if (!boton) {
        return;
    }
    const icono = boton.querySelector('i');
    boton.setAttribute('aria-pressed', visible ? 'true' : 'false');
    boton.setAttribute('aria-label', visible ? 'Ocultar vidrio' : 'Mostrar vidrio');
    boton.title = visible ? 'Ocultar vidrio' : 'Mostrar vidrio';
    if (icono) {
        icono.classList.toggle('fa-eye', visible);
        icono.classList.toggle('fa-eye-slash', !visible);
    }
}

function tornilloLateral(x, y, z, mat) {
    const tornillo = cilindro(0.011, 0.016, mat.aceroClaro);
    tornillo.rotation.z = Math.PI / 2;
    tornillo.position.set(x, y, z);
    tornillo.userData.adorno = true;
    return tornillo;
}

const aceroJaula = new THREE.MeshStandardMaterial({
    color: 0x24262b, roughness: 0.74, metalness: 0.16, envMapIntensity: 0,
});

function lateralJaula(grupo, x, suelo, cz, pasoY) {
    const grueso = 0.018;
    const alto = 0.655;
    const fondo = 1.6;
    const cinta = 0.032;
    const poste = 0.036;
    const y0 = suelo - 0.0125;
    const centroY = suelo + 0.315;
    const barra = (y, h, z, largo) => {
        const pieza = caja(grueso, h, largo, aceroJaula);
        pieza.position.set(x, y, z);
        grupo.add(pieza);
    };
    const z0 = cz - fondo / 2;
    const centros = [z0 + poste / 2, cz - 0.27, cz + 0.27, z0 + fondo - poste / 2];
    centros.forEach((z) => {
        barra(centroY, alto, z, poste);
    });
    for (let i = 0; i < centros.length - 1; i += 1) {
        const desde = centros[i] + poste / 2;
        const hasta = centros[i + 1] - poste / 2;
        const largo = hasta - desde;
        if (largo <= 0.02) {
            continue;
        }
        const medio = (desde + hasta) / 2;
        barra(y0 + cinta / 2, cinta, medio, largo);
        barra(y0 + alto - cinta / 2, cinta, medio, largo);
        barra(suelo + pasoY - 0.008, 0.02, medio, largo);
    }
}

function agregarJaula(gabinete, mat) {
    const ficha = fichaGabinete('Micro-ATX');
    const bahia = ficha.hdd;
    const sata = ficha.sata;
    const grupo = new THREE.Group();
    grupo.name = 'jaula-discos';
    grupo.userData.adorno = true;
    const cx = bahia.x;
    const cz = bahia.z;
    const suelo = bahia.y;
    const bandeja = caja(1.06, 0.02, 1.6, aceroJaula);
    bandeja.position.set(cx, suelo - 0.012, cz);
    grupo.add(bandeja);
    lateralJaula(grupo, cx - 0.521, suelo, cz, bahia.pasoY);
    lateralJaula(grupo, cx + 0.521, suelo, cz, bahia.pasoY);
    [-0.46, 0.46].forEach((lado) => {
        const riel = caja(0.07, 0.012, 1.52, aceroJaula);
        riel.position.set(cx + lado, suelo + bahia.pasoY - 0.008, cz);
        grupo.add(riel);
    });
    [-0.45, 0.3].forEach((z) => {
        [0, 1].forEach((nivel) => {
            const y = suelo + bahia.pasoY * nivel + 0.13;
            grupo.add(tornilloLateral(cx - 0.538, y, cz + z, mat));
            grupo.add(tornilloLateral(cx + 0.538, y, cz + z, mat));
        });
    });
    for (let i = 0; i < 2; i += 1) {
        const x = sata.x + (sata.pasoX || 0) * i;
        const z = sata.z + (sata.paso || 0) * i;
        const soporte = caja(0.76, 0.012, 1.06, aceroJaula);
        soporte.position.set(x, sata.y - 0.008, z);
        const labioA = caja(0.012, 0.028, 1.06, aceroJaula);
        labioA.position.set(x - 0.374, sata.y + 0.006, z);
        const labioB = caja(0.012, 0.028, 1.06, aceroJaula);
        labioB.position.set(x + 0.374, sata.y + 0.006, z);
        grupo.add(soporte, labioA, labioB);
        grupo.add(tornilloLateral(x - 0.386, sata.y + 0.02, z - 0.28, mat));
        grupo.add(tornilloLateral(x + 0.386, sata.y + 0.02, z + 0.28, mat));
    }
    grupo.traverse((nodo) => {
        nodo.userData.adorno = true;
        nodo.raycast = () => {};
    });
    gabinete.add(grupo);
}

function agregarVentiladores(gabinete, envoltura, mat, ventiladores) {
    const interior = cajaLocal(gabinete, (nodo) => {
        let actual = nodo;
        while (actual) {
            if (actual === envoltura) {
                return true;
            }
            actual = actual.parent;
        }
        return false;
    });
    if (interior.isEmpty()) {
        return;
    }
    const tamano = interior.getSize(new THREE.Vector3());
    const centro = interior.getCenter(new THREE.Vector3());
    const radio = tamano.y * 0.085;
    const puestos = [
        [centro.x, interior.min.y + tamano.y * 0.68, interior.min.z + tamano.z * 0.14, radio],
        [centro.x, interior.min.y + tamano.y * 0.7, interior.max.z - tamano.z * 0.16, radio * 0.92],
        [centro.x, interior.min.y + tamano.y * 0.4, interior.max.z - tamano.z * 0.16, radio * 0.92],
    ];
    const coloresFan = [0xb388ff, 0x5ee7ff, 0x4d7dff];
    puestos.forEach((puesto, indice) => {
        const fan = ventilador(puesto[3], mat);
        fan.traverse((nodo) => {
            if (nodo.isMesh && nodo.material === mat.rgb) {
                nodo.material = materialRgb(coloresFan[indice], 1.05);
            }
        });
        fan.position.set(puesto[0], puesto[1], puesto[2]);
        fan.userData.adorno = true;
        gabinete.add(fan);
        ventiladores.push(fan);
        const cerco = new THREE.Mesh(TORO, mat.acero);
        cerco.scale.set(puesto[3] * 1.08, puesto[3] * 1.08, puesto[3] * 0.22);
        cerco.position.copy(fan.position);
        cerco.position.z += indice === 0 ? -puesto[3] * 0.12 : puesto[3] * 0.12;
        cerco.raycast = () => {};
        cerco.userData.adorno = true;
        gabinete.add(cerco);
    });
    for (let i = 0; i < 5; i += 1) {
        const lama = caja(tamano.x * 0.62, 0.01, 0.018, mat.acero);
        lama.position.set(centro.x, interior.max.y - 0.03, centro.z - tamano.z * 0.12 + i * 0.09);
        lama.raycast = () => {};
        lama.userData.adorno = true;
        gabinete.add(lama);
    }
}

let cajaProcedural = null;
let cargaGabinete = 0;

function destinoProcedural(gabinete) {
    if (!cajaProcedural) {
        cajaProcedural = cajaLocal(gabinete, (nodo) => nodo.userData.carcasa);
    }
    return cajaProcedural;
}

function asegurarEscala(gabinete) {
    if (gabinete.userData.escalaLista) {
        return Promise.resolve();
    }
    const url = new URL('../modelos/gabinete/pc-case.glb', import.meta.url);
    url.searchParams.set('v', 'gabinete1');
    return cargarModelo(url).then((gltf) => {
        gltf.scene.updateWorldMatrix(true, true);
        const origen = new THREE.Box3().setFromObject(gltf.scene);
        const altoOrigen = origen.max.y - origen.min.y;
        const destino = destinoProcedural(gabinete);
        const altoDestino = destino.max.y - destino.min.y;
        if (altoOrigen > 0 && altoDestino > 0) {
            fijarEscala(altoDestino / altoOrigen);
        }
        gabinete.userData.escalaLista = true;
    });
}

function quitarCarcasa(gabinete, ventiladores) {
    const quitar = gabinete.children.filter((hijo) => hijo.userData && (hijo.userData.carcasa || hijo.userData.adorno));
    quitar.forEach((hijo) => {
        hijo.traverse((nodo) => {
            if (nodo.userData && nodo.userData.ventilador) {
                const indice = ventiladores.indexOf(nodo);
                if (indice >= 0) {
                    ventiladores.splice(indice, 1);
                }
            }
        });
        gabinete.remove(hijo);
    });
}

function montarAspas(raiz, ventiladores) {
    const aspas = [];
    raiz.traverse((nodo) => {
        if (nodo.isMesh && (nodo.name || '').toLowerCase().includes('blades')) {
            aspas.push(nodo);
        }
    });
    aspas.forEach((aspa) => {
        if (!aspa.geometry.boundingBox) {
            aspa.geometry.computeBoundingBox();
        }
        const centro = aspa.geometry.boundingBox.getCenter(new THREE.Vector3());
        const pivote = new THREE.Group();
        pivote.position.copy(centro);
        aspa.position.sub(centro);
        aspa.parent.add(pivote);
        pivote.add(aspa);
        pivote.userData.ventilador = true;
        pivote.userData.eje = 'z';
        ventiladores.push(pivote);
    });
}

function formatoMontaje(estado) {
    if (estado && estado.gabinete && estado.gabinete.formato) {
        return estado.gabinete.formato;
    }
    if (estado && estado.placa && estado.placa.formato) {
        return estado.placa.formato;
    }
    return undefined;
}

function incorporarGabineteDetallado(gabinete, mat, ventiladores, aviso, formato) {
    const ficha = fichaGabinete(formato);
    if (gabinete.userData.modelo === ficha.id && gabinete.userData.origen === 'glb') {
        return asegurarEscala(gabinete);
    }
    if (aviso) {
        aviso.hidden = false;
    }
    const turno = ++cargaGabinete;
    const url = new URL(`../modelos/${ficha.archivo}`, import.meta.url);
    url.searchParams.set('v', 'gabinete2');
    return Promise.all([cargarModelo(url), asegurarEscala(gabinete)]).then(([gltf]) => {
        if (turno !== cargaGabinete) {
            return;
        }
        const destino = destinoProcedural(gabinete);
        const vidrios = prepararGabinete(gltf.scene, mat, Boolean(ficha.propios || ficha.compacto));
        if (destino.isEmpty() || (!vidrios.length && !ficha.compacto)) {
            throw new Error('gabinete glb incompleto');
        }
        if (gltf.scene.parent) {
            gltf.scene.parent.remove(gltf.scene);
        }
        gltf.scene.position.set(0, 0, 0);
        gltf.scene.rotation.set(0, 0, 0);
        gltf.scene.scale.set(1, 1, 1);
        gltf.scene.updateWorldMatrix(true, true);
        const origen = new THREE.Box3().setFromObject(gltf.scene);
        const altoOrigen = origen.max.y - origen.min.y;
        const altoDestino = destino.max.y - destino.min.y;
        if (!(altoOrigen > 0) || !(altoDestino > 0)) {
            throw new Error('gabinete glb sin escala');
        }
        const escala = ficha.compacto ? metros() : altoDestino / altoOrigen;
        const centroOrigen = origen.getCenter(new THREE.Vector3());
        const centroDestino = destino.getCenter(new THREE.Vector3());
        const envoltura = new THREE.Group();
        envoltura.name = 'gabinete-glb';
        envoltura.userData.carcasa = true;
        envoltura.scale.setScalar(escala);
        envoltura.position.set(
            ficha.compacto ? -centroOrigen.x * escala : centroDestino.x - centroOrigen.x * escala,
            ficha.compacto ? -origen.min.y * escala : destino.min.y - origen.min.y * escala,
            ficha.compacto ? -centroOrigen.z * escala : centroDestino.z - centroOrigen.z * escala,
        );
        envoltura.add(gltf.scene);
        if (ficha.propios && !gltf.scene.userData.aspas) {
            montarAspas(gltf.scene, ventiladores);
            gltf.scene.userData.aspas = true;
        } else if (ficha.propios) {
            gltf.scene.traverse((nodo) => {
                if (nodo.userData && nodo.userData.ventilador) {
                    ventiladores.push(nodo);
                }
            });
        }
        quitarCarcasa(gabinete, ventiladores);
        gabinete.add(envoltura);
        if (ficha.propios) {
            iluminarMid(gabinete, envoltura);
            agregarJaula(gabinete, mat);
        } else if (ficha.compacto) {
            iluminarMid(gabinete, envoltura);
        } else {
            agregarVentiladores(gabinete, envoltura, mat, ventiladores);
        }
        if (typeof gabinete.userData.ambiente === 'function') {
            gabinete.userData.ambiente(Boolean(ficha.propios));
        }
        gabinete.userData.vidrio = controlVidrio(vidrios);
        if (ficha.compacto) {
            gabinete.userData.vidrio.visible = false;
        }
        reflejarBotonVidrio(gabinete.userData.vidrio.visible);
        gabinete.userData.origen = 'glb';
        gabinete.userData.modelo = ficha.id;
        gabinete.userData.escalaGlb = gabinete.userData.escalaLista ? undefined : escala;
        window.hwVistaGabinete = ficha.id;
        if (gabinete.userData.pisoOriginal == null) {
            gabinete.userData.pisoOriginal = gabinete.position.y;
        }
        gabinete.position.y = ficha.compacto ? 0 : gabinete.userData.pisoOriginal;
        if (ficha.compacto && typeof gabinete.userData.encuadrarCompacto === 'function') {
            gabinete.updateWorldMatrix(true, true);
            gabinete.userData.encuadrarCompacto(new THREE.Box3().setFromObject(envoltura));
        } else if (gabinete.userData.marcoCompacto && typeof gabinete.userData.encuadrarTorre === 'function') {
            gabinete.userData.encuadrarTorre();
        }
        if (gabinete.userData.marco) {
            gabinete.remove(gabinete.userData.marco);
            gabinete.userData.marco = null;
        }
        marcar(gabinete);
    }).catch((error) => {
        gabinete.userData.origen = 'procedural';
        window.hwVistaGabinete = 'procedural';
        window.hwVistaGabineteError = String((error && error.message) || error);
    }).finally(() => {
        if (aviso) {
            aviso.hidden = true;
        }
    });
}

function fijarContorno(grupo, visible) {
    const marco = grupo && grupo.userData && grupo.userData.marco;
    if (!marco || !marco.userData.capas) {
        return;
    }
    marco.userData.capas.forEach((capa) => {
        capa.visible = visible;
    });
}

function marcar(grupo) {
    if (!grupo.userData.clave || grupo.userData.clave === 'gabinete') {
        return;
    }
    const marco = new THREE.Group();
    marco.userData.esMarco = true;
    marco.userData.capas = [];
    const mallas = [];
    grupo.traverse((nodo) => {
        if (nodo.isMesh && !nodo.userData.esMarco && nodo.geometry && !nodo.isInstancedMesh) {
            mallas.push(nodo);
        }
    });
    const factor = 1.015;
    mallas.forEach((nodo) => {
        if (!nodo.geometry.boundingBox) {
            nodo.geometry.computeBoundingBox();
        }
        const centro = nodo.geometry.boundingBox.getCenter(new THREE.Vector3());
        const capa = new THREE.Mesh(nodo.geometry, grupo.userData.materialSeleccion);
        capa.scale.setScalar(factor);
        capa.position.copy(centro).multiplyScalar(1 - factor);
        capa.visible = false;
        capa.userData.esMarco = true;
        capa.castShadow = false;
        capa.receiveShadow = false;
        capa.raycast = () => {};
        nodo.add(capa);
        marco.userData.capas.push(capa);
    });
    grupo.userData.marco = marco;
}

function medidaPlaca(formato, ranurasDato) {
    let medida = { alto: 2.15, ancho: 2.45, ranuras: 4, clave: 'atx' };
    if (formato === 'Micro-ATX') {
        medida = { alto: 1.7, ancho: 1.9, ranuras: 2, clave: 'matx' };
    } else if (formato === 'Mini-ITX') {
        medida = { alto: 1.32, ancho: 1.32, ranuras: 2, clave: 'itx' };
    }
    const ranuras = Number(ranurasDato);
    if (Number.isFinite(ranuras) && ranuras > 0) {
        medida.ranuras = Math.min(4, ranuras);
    }
    return medida;
}

function crearPlaca(formato, ranurasDato, mat) {
    const medida = medidaPlaca(formato, ranurasDato);
    const grupo = new THREE.Group();
    const pcb = caja(0.045, medida.alto, medida.ancho, mat.pcb);
    grupo.add(pcb);
    const pistas = caja(0.006, medida.alto * 0.82, medida.ancho * 0.72, mat.pcbOscuro);
    pistas.position.x = 0.026;
    grupo.add(pistas);
    const socket = new THREE.Group();
    socket.position.set(0.03, medida.alto * 0.16, -medida.ancho * 0.16);
    socket.add(caja(0.03, 0.42, 0.42, mat.plastico));
    const marcoSocket = caja(0.012, 0.5, 0.5, mat.aceroClaro);
    marcoSocket.position.x = 0.02;
    socket.add(marcoSocket);
    grupo.add(socket);
    grupo.userData.socket = socket.position.clone();
    for (let i = 0; i < medida.ranuras; i += 1) {
        const ranura = caja(0.035, 0.16, 0.1, mat.plastico);
        ranura.position.set(0.03, medida.alto * 0.2, medida.ancho * 0.02 + i * 0.18);
        grupo.add(ranura);
    }
    grupo.userData.ram = {
        y: medida.alto * 0.28,
        z0: medida.ancho * 0.02,
        paso: 0.18,
        cantidad: medida.ranuras,
    };
    const pcie = caja(0.04, 0.08, 1.15, mat.plastico);
    pcie.position.set(0.03, -medida.alto * 0.22, -medida.ancho * 0.02);
    grupo.add(pcie);
    grupo.userData.pcie = pcie.position.clone();
    const disipador = caja(0.08, 0.28, 0.55, mat.aluminio);
    disipador.position.set(0.06, medida.alto * 0.18, medida.ancho * 0.28);
    grupo.add(disipador, laminas(8, 0.5, 0.22, mat.aluminio));
    grupo.children[grupo.children.length - 1].position.set(0.11, medida.alto * 0.18, medida.ancho * 0.28);
    const chipset = caja(0.06, 0.22, 0.32, mat.aluminio);
    chipset.position.set(0.05, -medida.alto * 0.05, medida.ancho * 0.3);
    grupo.add(chipset);
    const condensadores = new THREE.InstancedMesh(CILINDRO, mat.aluminio, 10);
    for (let i = 0; i < 10; i += 1) {
        dummy.position.set(0.045, medida.alto * 0.34, -medida.ancho * 0.38 + i * 0.07);
        dummy.rotation.set(0, 0, Math.PI / 2);
        dummy.scale.set(0.025, 0.07, 0.025);
        dummy.updateMatrix();
        condensadores.setMatrixAt(i, dummy.matrix);
    }
    grupo.add(condensadores);
    const alimentacion = caja(0.05, 0.12, 0.28, mat.plasticoClaro);
    alimentacion.position.set(0.04, -medida.alto * 0.38, medida.ancho * 0.34);
    const cpuPower = caja(0.05, 0.1, 0.16, mat.plastico);
    cpuPower.position.set(0.04, medida.alto * 0.4, -medida.ancho * 0.36);
    grupo.add(alimentacion, cpuPower);
    const m2 = caja(0.012, 0.08, 0.42, mat.pcbOscuro);
    m2.position.set(0.03, -medida.alto * 0.02, -medida.ancho * 0.32);
    grupo.add(m2);
    grupo.userData.m2 = m2.position.clone();
    grupo.userData.medida = medida.clave;
    return grupo;
}

function crearCpu(mat) {
    const grupo = new THREE.Group();
    grupo.add(caja(0.03, 0.38, 0.38, mat.pcb));
    const ihs = caja(0.035, 0.3, 0.3, mat.aceroClaro);
    ihs.position.x = 0.03;
    const tapa = caja(0.012, 0.22, 0.22, mat.aluminio);
    tapa.position.x = 0.05;
    grupo.add(ihs, tapa);
    return grupo;
}

function crearRam(mat) {
    const grupo = new THREE.Group();
    const pcb = caja(0.02, 0.55, 0.12, mat.pcb);
    grupo.add(pcb);
    const contactos = caja(0.008, 0.08, 0.1, mat.oro);
    contactos.position.y = -0.3;
    const izquierda = caja(0.03, 0.42, 0.02, mat.aluminio);
    izquierda.position.set(0.02, 0.04, -0.045);
    const derecha = izquierda.clone();
    derecha.position.z = 0.045;
    const luz = caja(0.008, 0.06, 0.1, mat.led);
    luz.position.set(0.03, 0.28, 0);
    grupo.add(contactos, izquierda, derecha, luz);
    return grupo;
}

function marcoVentiladorGpu(x, z, mat) {
    const grupo = new THREE.Group();
    const y = -0.016;
    const lado = 0.086;
    const borde = 0.005;
    const frente = caja(lado, 0.004, borde, mat.aluminio);
    frente.position.set(x, y, z - lado / 2);
    const atras = frente.clone();
    atras.position.z = z + lado / 2;
    const ladoA = caja(borde, 0.004, lado, mat.aluminio);
    ladoA.position.set(x - lado / 2, y, z);
    const ladoB = ladoA.clone();
    ladoB.position.x = x + lado / 2;
    frente.material = mat.gpuBorde;
    atras.material = mat.gpuBorde;
    ladoA.material = mat.gpuBorde;
    ladoB.material = mat.gpuBorde;
    grupo.add(frente, atras, ladoA, ladoB);
    return grupo;
}

function crearGpu(ventiladores, mat) {
    const largo = ventiladores >= 3 ? 0.3 : 0.24;
    const doble = ventiladores < 3;
    const grupo = new THREE.Group();
    const carcasa = caja(0.11, doble ? 0.022 : 0.038, largo, doble ? mat.gpuCuerpo : mat.plastico);
    carcasa.position.set(0.06, doble ? -0.008 : 0, largo / 2);
    grupo.add(carcasa);
    if (doble) {
        const tapa = caja(0.11, 0.012, largo * 0.78, mat.gpuTapa);
        tapa.position.set(0.06, 0.013, largo * 0.4);
        const nariz = caja(0.094, 0.02, 0.03, mat.gpuCuerpo);
        nariz.position.set(0.06, -0.004, largo - 0.02);
        const ceja = caja(0.1, 0.003, largo * 0.68, mat.gpuBorde);
        ceja.position.set(0.06, 0.017, largo * 0.36);
        grupo.add(tapa, nariz, ceja);
        for (let i = 0; i < 7; i += 1) {
            const aleta = caja(0.072, 0.003, 0.004, mat.aluminio);
            aleta.position.set(0.055, 0.016, 0.045 + i * (largo * 0.09));
            grupo.add(aleta);
        }
        for (let i = 0; i < 4; i += 1) {
            const corte = caja(0.006, 0.01, 0.018, mat.plasticoClaro);
            corte.position.set(0.108, -0.002, 0.05 + i * 0.042);
            grupo.add(corte);
        }
    }
    const backplate = caja(0.105, 0.012, largo * 0.92, mat.acero);
    backplate.name = 'backplate-gpu';
    backplate.position.set(0.055, 0.02, largo / 2);
    const soporte = caja(0.02, 0.11, 0.012, mat.aceroClaro);
    soporte.name = 'soporte-gpu';
    soporte.position.set(0.05, 0.03, -0.005);
    grupo.add(backplate, soporte);
    for (let i = 0; i < ventiladores; i += 1) {
        const fan = ventilador(0.042, mat);
        fan.rotation.x = -Math.PI / 2;
        const z = 0.03 + ((i + 0.5) * (largo - 0.04)) / ventiladores;
        fan.position.set(0.055, -0.024, z);
        grupo.add(fan);
        if (doble) {
            grupo.add(marcoVentiladorGpu(0.055, z, mat));
        }
    }
    const conector = caja(0.018, 0.012, 0.02, mat.plasticoClaro);
    conector.position.set(0.04, doble ? 0.013 : 0.02, largo - 0.03);
    const tira = caja(0.006, 0.01, largo * 0.62, mat.rgb);
    tira.position.set(0.108, -0.012, largo * 0.48);
    grupo.add(conector, tira);
    if (doble) {
        grupo.children.forEach((nodo) => {
            if (nodo.name !== 'soporte-gpu') {
                nodo.position.x -= 0.008;
            }
        });
    }
    return grupo;
}

function crearAire(mat) {
    const grupo = new THREE.Group();
    const base = caja(0.05, 0.34, 0.34, mat.cobre);
    grupo.add(base);
    for (let i = 0; i < 3; i += 1) {
        const curva = new THREE.CatmullRomCurve3([
            new THREE.Vector3(0.02, -0.08 + i * 0.08, -0.08),
            new THREE.Vector3(0.28, 0.15, 0),
            new THREE.Vector3(0.08, 0.42, 0.08),
        ]);
        const tubo = new THREE.TubeGeometry(curva, 16, 0.028, 6, false);
        tubo.userData.descartable = true;
        grupo.add(new THREE.Mesh(tubo, mat.cobre));
    }
    const bloque = laminas(16, 0.7, 0.7, mat.aluminio);
    bloque.position.set(0.22, 0.28, 0);
    const fan = ventilador(0.38, mat);
    fan.position.set(0.42, 0.28, 0);
    grupo.add(bloque, fan);
    return grupo;
}

function crearLiquida(bloque, radiadorPos, mat) {
    const grupo = new THREE.Group();
    const bomba = new THREE.Group();
    bomba.position.copy(bloque);
    const cuerpo = cilindro(0.16, 0.07, mat.plastico);
    cuerpo.rotation.z = Math.PI / 2;
    const tapa = cilindro(0.1, 0.02, mat.aceroClaro);
    tapa.rotation.z = Math.PI / 2;
    tapa.position.x = 0.04;
    bomba.add(cuerpo, tapa);
    grupo.add(bomba);
    const radiador = new THREE.Group();
    radiador.position.copy(radiadorPos);
    radiador.add(caja(0.12, 0.28, 0.03, mat.acero));
    const aletas = laminas(14, 0.03, 0.24, mat.aluminio);
    radiador.add(aletas);
    for (let i = 0; i < 2; i += 1) {
        const fan = ventilador(0.06, mat);
        fan.position.set(0, -0.08 + i * 0.16, 0.04);
        radiador.add(fan);
    }
    grupo.add(radiador);
    [0.04, -0.04].forEach((desfase, indice) => {
        const curva = new THREE.CatmullRomCurve3([
            new THREE.Vector3(bloque.x + 0.08, bloque.y + desfase, bloque.z),
            new THREE.Vector3((bloque.x + radiadorPos.x) / 2, Math.max(bloque.y, radiadorPos.y) + 0.35, (bloque.z + radiadorPos.z) / 2),
            new THREE.Vector3(radiadorPos.x, radiadorPos.y + (indice === 0 ? 0.08 : -0.08), radiadorPos.z),
        ]);
        const tubo = new THREE.TubeGeometry(curva, 24, 0.018, 7, false);
        tubo.userData.descartable = true;
        grupo.add(new THREE.Mesh(tubo, mat.plastico));
    });
    return grupo;
}

function crearFuente(mat) {
    const grupo = new THREE.Group();
    grupo.add(caja(1.35, 0.72, 1.5, mat.acero));
    const rejilla = laminas(8, 0.7, 0.7, mat.aceroClaro);
    rejilla.position.set(0.69, 0, 0);
    rejilla.rotation.y = Math.PI / 2;
    const fan = ventilador(0.28, mat);
    fan.position.set(0.7, 0, 0);
    const interruptor = caja(0.04, 0.08, 0.14, mat.plasticoClaro);
    interruptor.position.set(0.69, 0.22, -0.55);
    const conector = caja(0.08, 0.16, 0.2, mat.plastico);
    conector.position.set(-0.2, 0.2, 0.78);
    grupo.add(rejilla, fan, interruptor, conector);
    return grupo;
}

function crearDisco(clase, mat) {
    const grupo = new THREE.Group();
    if (clase === 'm2') {
        grupo.add(caja(0.012, 0.09, 0.46, mat.pcbOscuro));
        const chip = caja(0.02, 0.06, 0.1, mat.plastico);
        chip.position.set(0.014, 0, 0.08);
        const control = caja(0.018, 0.05, 0.07, mat.aceroClaro);
        control.position.set(0.012, 0, -0.1);
        grupo.add(chip, control);
        return grupo;
    }
    if (clase === 'hdd') {
        grupo.add(caja(0.22, 1.02, 1.45, mat.acero));
        const tapa = cilindro(0.28, 0.03, mat.aceroClaro);
        tapa.rotation.z = Math.PI / 2;
        tapa.position.x = 0.12;
        const etiqueta = caja(0.01, 0.35, 0.7, mat.plasticoClaro);
        etiqueta.position.set(0.12, 0.15, 0.15);
        grupo.add(tapa, etiqueta);
        return grupo;
    }
    grupo.add(caja(0.08, 0.72, 1.02, mat.aluminio));
    const etiqueta = caja(0.012, 0.4, 0.62, mat.plastico);
    etiqueta.position.x = 0.045;
    grupo.add(etiqueta);
    return grupo;
}

function crearGabinete(mat) {
    const grupo = new THREE.Group();
    const ancho = 2.35;
    const alto = 4.55;
    const fondo = 4.35;
    const poste = (x, z) => {
        const pieza = caja(0.08, alto, 0.08, mat.acero);
        pieza.position.set(x, 0, z);
        grupo.add(pieza);
    };
    poste(-ancho / 2, -fondo / 2);
    poste(ancho / 2, -fondo / 2);
    poste(-ancho / 2, fondo / 2);
    poste(ancho / 2, fondo / 2);
    const superior = caja(ancho, 0.08, fondo, mat.acero);
    superior.position.y = alto / 2;
    const inferior = caja(ancho, 0.08, fondo, mat.acero);
    inferior.position.y = -alto / 2;
    const trasera = caja(ancho - 0.12, alto - 0.16, 0.05, mat.acero);
    trasera.position.set(0, 0, -fondo / 2);
    const izquierda = caja(0.05, alto - 0.2, fondo - 0.16, mat.acero);
    izquierda.position.x = -ancho / 2;
    grupo.add(superior, inferior, trasera, izquierda);
    const ceja = caja(ancho - 0.02, 0.28, 0.1, mat.plastico);
    ceja.position.set(0, alto / 2 - 0.24, fondo / 2);
    const baseFrente = caja(ancho - 0.02, 0.42, 0.1, mat.plastico);
    baseFrente.position.set(0, -alto / 2 + 0.32, fondo / 2);
    const pilarIzquierdo = caja(0.14, alto - 0.85, 0.1, mat.plastico);
    pilarIzquierdo.position.set(-ancho / 2 + 0.08, 0.05, fondo / 2);
    const pilarDerecho = pilarIzquierdo.clone();
    pilarDerecho.position.x = ancho / 2 - 0.08;
    grupo.add(ceja, baseFrente, pilarIzquierdo, pilarDerecho);
    const ranuras = new THREE.InstancedMesh(CAJA, mat.aceroClaro, 14);
    for (let i = 0; i < 14; i += 1) {
        dummy.position.set(0, -1.5 + i * 0.22, fondo / 2 + 0.05);
        dummy.rotation.set(0, 0, 0);
        dummy.scale.set(1.7, 0.035, 0.03);
        dummy.updateMatrix();
        ranuras.setMatrixAt(i, dummy.matrix);
    }
    grupo.add(ranuras);
    const bandeja = caja(0.04, 2.7, 2.7, mat.acero);
    bandeja.position.set(-0.95, 0.45, -0.35);
    const shroud = caja(ancho - 0.45, 0.05, fondo - 0.55, mat.acero);
    shroud.position.set(0.12, -1.02, 0.15);
    const tabique = caja(0.05, 0.85, fondo - 0.7, mat.acero);
    tabique.position.set(-0.72, -1.48, 0.1);
    grupo.add(bandeja, shroud, tabique);
    const vidrio = caja(0.025, alto - 0.28, fondo - 0.28, mat.vidrio);
    vidrio.position.set(ancho / 2 - 0.01, 0.02, 0);
    vidrio.raycast = () => {};
    grupo.add(vidrio);
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sz]) => {
        const pata = cilindro(0.09, 0.12, mat.plastico);
        pata.position.set(sx * (ancho / 2 - 0.18), -alto / 2 - 0.06, sz * (fondo / 2 - 0.22));
        grupo.add(pata);
    });
    const boton = cilindro(0.07, 0.04, mat.led);
    boton.position.set(0.55, alto / 2 + 0.03, fondo / 2 - 0.35);
    const usb1 = caja(0.08, 0.03, 0.16, mat.plasticoClaro);
    usb1.position.set(-0.15, alto / 2 + 0.02, fondo / 2 - 0.35);
    const usb2 = usb1.clone();
    usb2.position.x = 0.12;
    grupo.add(boton, usb1, usb2);
    for (let i = 0; i < 7; i += 1) {
        const slot = caja(0.03, 0.12, 0.9, mat.aceroClaro);
        slot.position.set(-0.15, -0.55 + i * 0.16, -fondo / 2 - 0.01);
        grupo.add(slot);
    }
    const tornillos = new THREE.InstancedMesh(CILINDRO, mat.aceroClaro, 12);
    const puntos = [
        [-1.05, 2.05, -1.9], [1.05, 2.05, -1.9], [-1.05, -2.05, -1.9], [1.05, -2.05, -1.9],
        [-1.05, 2.05, 1.9], [1.05, 2.05, 1.9], [-1.05, -0.9, 0.4], [0.9, -0.9, 0.4],
        [-0.7, 1.5, -0.2], [-0.7, 0.2, -0.2], [-0.7, 1.5, -1.2], [-0.7, 0.2, -1.2],
    ];
    puntos.forEach((punto, indice) => {
        dummy.position.set(punto[0], punto[1], punto[2]);
        dummy.rotation.set(0, 0, Math.PI / 2);
        dummy.scale.set(0.035, 0.04, 0.035);
        dummy.updateMatrix();
        tornillos.setMatrixAt(indice, dummy.matrix);
    });
    grupo.add(tornillos);
    [0.4, -0.5].forEach((y) => {
        const pasacable = new THREE.Mesh(TORO, mat.plastico);
        pasacable.scale.set(0.16, 0.16, 0.16);
        pasacable.position.set(-0.55, y, -0.15);
        grupo.add(pasacable);
    });
    const trasero = ventilador(0.42, mat);
    trasero.position.set(0.15, 1.15, -fondo / 2 + 0.08);
    grupo.add(trasero);
    [-0.55, 0.55].forEach((y) => {
        const fan = ventilador(0.4, mat);
        fan.position.set(0, y, fondo / 2 - 0.18);
        grupo.add(fan);
    });
    grupo.userData.vidrio = vidrio;
    grupo.userData.clave = 'gabinete';
    return grupo;
}

function claseDisco(disco) {
    if (!disco) {
        return 'sata';
    }
    if (disco.model_name === 'almacenamiento_hdd') {
        return disco.formato === '2.5"' ? 'sata' : 'hdd';
    }
    if (disco.formato === 'M.2 2280') {
        return 'm2';
    }
    return 'sata';
}

function ventiladoresGpu(gpu) {
    const largo = Number(gpu && gpu.largo);
    if (Number.isFinite(largo) && largo >= 280) {
        return 3;
    }
    return 2;
}

function altoRadiador(cooler) {
    const mm = Number(cooler && cooler.radiador);
    if (Number.isFinite(mm) && mm >= 360) {
        return 1.65;
    }
    return 1.15;
}

function modulosRam(ram) {
    const porProducto = Number(ram.modulos);
    const cantidad = Number(ram.cantidad) > 0 ? Number(ram.cantidad) : 1;
    if (Number.isFinite(porProducto) && porProducto > 0) {
        return Math.min(4, porProducto * cantidad);
    }
    return Math.min(4, cantidad);
}

function precioVisible(valor) {
    if (typeof window.hwPesos === 'function') {
        return window.hwPesos(valor);
    }
    const entero = Math.round(Number(valor) || 0);
    return `$${String(Math.abs(entero)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')}`;
}

function iniciar() {
    const raiz = document.getElementById('pc-visualizador');
    const lienzo = document.getElementById('pc-visualizador-lienzo');
    const aviso = document.getElementById('pc-visualizador-fallback');
    const conteo = document.getElementById('pc-visualizador-conteo');
    const ficha = document.getElementById('pc-visualizador-ficha');
    if (!raiz || !lienzo || !aviso || !conteo || !ficha) {
        return;
    }

    let renderer;
    try {
        const prueba = document.createElement('canvas');
        if (!prueba.getContext('webgl2') && !prueba.getContext('webgl')) {
            throw new Error('WebGL no disponible');
        }
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    } catch (error) {
        aviso.hidden = false;
        return;
    }

    const tactil = window.matchMedia('(pointer: coarse)').matches;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, tactil ? 1.25 : 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.AgXToneMapping;
    renderer.toneMappingExposure = 1;
    renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    lienzo.appendChild(renderer.domElement);

    const escena = new THREE.Scene();
    const camara = new THREE.PerspectiveCamera(32, 1, 0.1, 80);
    const controles = new OrbitControls(camara, renderer.domElement);
    controles.enablePan = false;
    controles.enableDamping = true;
    controles.maxPolarAngle = Math.PI * 0.92;

    escena.add(new THREE.HemisphereLight(0xf4f4f2, 0x1c1e22, 0.9));
    const ambiente = new THREE.AmbientLight(0xf4f4f2, 0.5);
    const principal = new THREE.DirectionalLight(0xfff8f2, 1.55);
    principal.position.set(4.2, 7.5, 3.2);
    principal.castShadow = true;
    principal.shadow.mapSize.set(tactil ? 512 : 1024, tactil ? 512 : 1024);
    principal.shadow.bias = -0.0006;
    principal.shadow.camera.near = 0.2;
    principal.shadow.camera.far = 30;
    principal.shadow.camera.left = -6;
    principal.shadow.camera.right = 6;
    principal.shadow.camera.top = 6;
    principal.shadow.camera.bottom = -6;
    const relleno = new THREE.DirectionalLight(0xf2f3f5, 0.22);
    relleno.position.set(-3.5, 2.2, -2);
    const frenteLuz = new THREE.DirectionalLight(0xf4f6f8, 0.34);
    frenteLuz.position.set(1.6, 2.4, 3.6);
    const interior = new THREE.PointLight(0xf6f5f2, 0.9, 8, 2);
    interior.position.set(0.35, 0.35, 0.15);
    const interiorLateral = new THREE.PointLight(0xf4f4f2, 0.26, 7, 2);
    interiorLateral.position.set(1.1, 0.2, 0.4);
    const bahia = new THREE.PointLight(0xf3f3f1, 0.34, 5.5, 2);
    const clara = new THREE.PointLight(0xf4f4f2, 0.4, 10, 2);
    escena.add(ambiente, principal, relleno, frenteLuz, interior, interiorLateral, bahia, clara);
    const sombra = new THREE.Mesh(
        new THREE.PlaneGeometry(24, 24),
        new THREE.ShadowMaterial({ opacity: 0.22 }),
    );
    sombra.rotation.x = -Math.PI / 2;
    sombra.receiveShadow = true;
    sombra.raycast = () => {};
    escena.add(sombra);

    const mat = materialesBase();
    const gabinete = crearGabinete(mat);
    gabinete.userData.materialSeleccion = mat.seleccion;
    gabinete.children.forEach((hijo) => {
        hijo.traverse((nodo) => {
            nodo.userData.carcasa = true;
        });
    });
    escena.add(gabinete);
    gabinete.updateWorldMatrix(true, true);
    const apoyo = new THREE.Box3().setFromObject(gabinete);
    gabinete.position.y -= apoyo.min.y;
    sombra.position.y = 0.004;
    marcar(gabinete);
    const limitesEstables = new THREE.Box3().setFromObject(gabinete);
    const centroCaja = limitesEstables.getCenter(new THREE.Vector3());
    interior.position.set(centroCaja.x + 0.15, centroCaja.y + 0.15, centroCaja.z);
    interior.intensity = 0.9;
    interiorLateral.position.set(centroCaja.x + 0.45, centroCaja.y, centroCaja.z + 0.15);
    interiorLateral.intensity = 0.26;
    bahia.position.set(centroCaja.x, centroCaja.y - 1.55, centroCaja.z - 0.35);
    clara.position.set(centroCaja.x + 0.12, centroCaja.y + 0.95, centroCaja.z + 0.15);
    function ambienteGabinete(esMid) {
        interior.color.setHex(0xf6f5f2);
        interior.intensity = esMid ? 0.55 : 0.9;
        interiorLateral.color.setHex(0xf4f4f2);
        interiorLateral.intensity = 0.26;
        bahia.color.setHex(0xf3f3f1);
        bahia.intensity = 0.34;
        clara.color.setHex(0xf4f4f2);
        clara.intensity = esMid ? 0.32 : 0.4;
        relleno.color.setHex(0xf2f3f5);
        relleno.intensity = 0.22;
    }
    gabinete.userData.ambiente = ambienteGabinete;

    const piezas = new Map();
    const animaciones = [];
    const ventiladores = [];
    gabinete.traverse((nodo) => {
        if (nodo.userData && nodo.userData.ventilador) {
            ventiladores.push(nodo);
        }
    });
    const pendiente = window.hwArmadoPendiente;
    incorporarGabineteDetallado(
        gabinete,
        mat,
        ventiladores,
        document.getElementById('pc-visualizador-carga'),
        formatoMontaje(pendiente),
    );
    let seleccionado = null;
    let encendido = true;

    const marcoTorre = limitesEstables.clone();
    gabinete.userData.encuadrarCompacto = (caja) => {
        gabinete.userData.marcoCompacto = true;
        limitesEstables.copy(caja);
        centroCaja.copy(caja.getCenter(new THREE.Vector3()));
        encuadrar();
    };
    gabinete.userData.encuadrarTorre = () => {
        gabinete.userData.marcoCompacto = false;
        limitesEstables.copy(marcoTorre);
        centroCaja.copy(marcoTorre.getCenter(new THREE.Vector3()));
        encuadrar();
    };

    function encuadrar() {
        const limites = limitesEstables;
        if (limites.isEmpty()) {
            return;
        }
        const centro = limites.getCenter(new THREE.Vector3());
        const esfera = limites.getBoundingSphere(new THREE.Sphere());
        if (!Number.isFinite(esfera.radius) || esfera.radius < 0.05) {
            return;
        }
        const fovVertical = THREE.MathUtils.degToRad(camara.fov);
        const fovHorizontal = 2 * Math.atan(Math.tan(fovVertical / 2) * Math.max(camara.aspect, 0.2));
        let distancia = (1.2 / 1.3) * Math.max(
            esfera.radius / Math.sin(fovVertical / 2),
            esfera.radius / Math.sin(fovHorizontal / 2),
        );
        if (!Number.isFinite(distancia) || distancia < 0.2) {
            return;
        }
        const direccion = new THREE.Vector3(1.2, 0.46, 0.42).normalize();
        const esquinas = [
            new THREE.Vector3(limites.min.x, limites.min.y, limites.min.z),
            new THREE.Vector3(limites.min.x, limites.min.y, limites.max.z),
            new THREE.Vector3(limites.min.x, limites.max.y, limites.min.z),
            new THREE.Vector3(limites.min.x, limites.max.y, limites.max.z),
            new THREE.Vector3(limites.max.x, limites.min.y, limites.min.z),
            new THREE.Vector3(limites.max.x, limites.min.y, limites.max.z),
            new THREE.Vector3(limites.max.x, limites.max.y, limites.min.z),
            new THREE.Vector3(limites.max.x, limites.max.y, limites.max.z),
        ];
        const proyectado = new THREE.Vector3();
        for (let paso = 0; paso < 2; paso += 1) {
            camara.position.copy(centro).addScaledVector(direccion, distancia);
            camara.near = Math.max(0.05, distancia / 100);
            camara.far = distancia * 14;
            camara.updateProjectionMatrix();
            camara.updateMatrixWorld();
            let minX = Infinity;
            let maxX = -Infinity;
            let minY = Infinity;
            let maxY = -Infinity;
            esquinas.forEach((punto) => {
                proyectado.copy(punto).project(camara);
                if (!Number.isFinite(proyectado.x) || !Number.isFinite(proyectado.y)) {
                    return;
                }
                minX = Math.min(minX, proyectado.x);
                maxX = Math.max(maxX, proyectado.x);
                minY = Math.min(minY, proyectado.y);
                maxY = Math.max(maxY, proyectado.y);
            });
            if (!Number.isFinite(minX) || !Number.isFinite(minY)) {
                break;
            }
            const altoVisible = 2 * distancia * Math.tan(fovVertical / 2);
            const anchoVisible = altoVisible * camara.aspect;
            const derecha = new THREE.Vector3().setFromMatrixColumn(camara.matrixWorld, 0);
            const arriba = new THREE.Vector3().setFromMatrixColumn(camara.matrixWorld, 1);
            centro.addScaledVector(derecha, ((minX + maxX) / 2) * anchoVisible / 2);
            centro.addScaledVector(arriba, ((minY + maxY) / 2) * altoVisible / 2);
        }
        camara.position.copy(centro).addScaledVector(direccion, distancia);
        camara.updateProjectionMatrix();
        camara.updateMatrixWorld();
        let exceso = 0.96;
        esquinas.forEach((punto) => {
            proyectado.copy(punto).project(camara);
            if (!Number.isFinite(proyectado.x) || !Number.isFinite(proyectado.y)) {
                return;
            }
            exceso = Math.max(exceso, Math.abs(proyectado.x), Math.abs(proyectado.y));
        });
        if (exceso > 0.96 && exceso < 1.8) {
            distancia *= exceso / 0.96;
            camara.position.copy(centro).addScaledVector(direccion, distancia);
        }
        camara.near = Math.max(0.05, distancia / 100);
        camara.far = distancia * 14;
        controles.target.copy(centro);
        controles.minDistance = distancia * 0.42;
        controles.maxDistance = distancia * 2.4;
        camara.updateProjectionMatrix();
        controles.update();
        controles.saveState();
    }

    let medidaEncuadre = { ancho: 0, alto: 0 };
    function ajustar(reencuadrar) {
        const ancho = lienzo.clientWidth;
        const alto = lienzo.clientHeight;
        if (!ancho || !alto) {
            return;
        }
        const cambioGrande = Math.abs(ancho - medidaEncuadre.ancho) > 40
            || Math.abs(alto - medidaEncuadre.alto) > 40;
        camara.aspect = ancho / alto;
        renderer.setSize(ancho, alto, false);
        if (reencuadrar || medidaEncuadre.ancho === 0 || cambioGrande) {
            encuadrar();
            medidaEncuadre = { ancho, alto };
            return;
        }
        camara.updateProjectionMatrix();
    }
    ajustar(true);
    window.requestAnimationFrame(() => ajustar(true));
    const observador = new ResizeObserver(() => ajustar(false));
    observador.observe(lienzo);

    function liberar(objeto) {
        if (typeof objeto.userData.soltar === 'function') {
            objeto.userData.soltar();
        }
        objeto.traverse((nodo) => {
            if (nodo.geometry && nodo.geometry.userData.descartable) {
                nodo.geometry.dispose();
            }
        });
    }

    function desplazar(grupo, destino, duracion, alFinal) {
        animaciones.push({
            grupo,
            inicio: grupo.position.clone(),
            destino: destino.clone(),
            t0: performance.now(),
            duracion,
            alFinal,
        });
    }

    function anclar(grupo, fichaPieza, clave) {
        grupo.userData.ficha = fichaPieza;
        grupo.userData.clave = clave;
        grupo.userData.materialSeleccion = mat.seleccion;
        grupo.userData.remarcar = () => {
            if (!grupo.parent) {
                return;
            }
            if (grupo.userData.marco && grupo.userData.marco.userData.capas) {
                grupo.userData.marco.userData.capas.forEach((capa) => {
                    capa.removeFromParent();
                });
                grupo.userData.marco = null;
            }
            marcar(grupo);
        };
        grupo.traverse((nodo) => {
            if (nodo.isMesh) {
                nodo.castShadow = true;
                nodo.receiveShadow = true;
            }
            if (nodo.userData && nodo.userData.ventilador) {
                ventiladores.push(nodo);
            }
        });
        gabinete.add(grupo);
        marcar(grupo);
    }

    function origenPlaca(estado) {
        return medidaPlaca(estado.placa && estado.placa.formato, estado.placa && estado.placa.ranuras);
    }

    function plan(estado) {
        const pedidos = [];
        const medida = origenPlaca(estado);
        const formato = estado.placa && estado.placa.formato;
        const formatoCaja = formatoMontaje(estado);
        const base = posePlaca(formato, formatoCaja);
        if (estado.placa) {
            pedidos.push({
                clave: `placa:${estado.placa.id}:${medida.clave}:${medida.ranuras}:${formatoCaja || ''}`,
                ficha: estado.placa,
                posicion: base.clone(),
                crear: () => crearPiezaGlb('placa', { formato, formatoCaja }, () => crearPlaca(formato, estado.placa.ranuras, mat), ventiladores),
            });
        }
        const superficie = anclaPlaca('socket', formato, 0, formatoCaja);
        if (estado.cpu) {
            pedidos.push({
                clave: `cpu:${estado.cpu.id}`,
                ficha: estado.cpu,
                posicion: superficie.clone(),
                crear: () => crearPiezaGlb('cpu', {}, () => crearCpu(mat), ventiladores),
            });
        }
        if (estado.cooler) {
            const liquida = estado.cooler.tipo === 'Líquida';
            const altura = altoRadiador(estado.cooler);
            const alturaCuerpo = Number(estado.cooler.altura);
            const bajoPerfil = !liquida && Number.isFinite(alturaCuerpo) && alturaCuerpo > 0 && alturaCuerpo <= 80;
            const bloque = asientoCooler(formato, formatoCaja);
            pedidos.push({
                clave: `cooler:${estado.cooler.id}:${liquida ? 'liq' : (bajoPerfil ? 'bajo' : 'aire')}:${altura}`,
                ficha: estado.cooler,
                posicion: liquida ? new THREE.Vector3(0, 0, 0) : bloque,
                crear: () => (liquida
                    ? crearLiquida(bloque, new THREE.Vector3(0.2, 1.25, 1.55), mat)
                    : crearPiezaGlb(bajoPerfil ? 'aireBajo' : 'aire', {}, () => crearAire(mat), ventiladores)),
            });
        }
        let usados = 0;
        (estado.rams || []).forEach((ram, indiceLinea) => {
            const total = modulosRam(ram);
            for (let i = 0; i < total; i += 1) {
                const indice = usados;
                usados += 1;
                const ranuraDimm = anclaPlaca('dimm', formato, indice, formatoCaja);
                const posicion = indice < medida.ranuras && ranuraDimm
                    ? ranuraDimm
                    : base.clone().add(new THREE.Vector3(0.35, 0.4 - indice * 0.2, 0.8));
                pedidos.push({
                    clave: `ram:${indiceLinea}:${ram.id}:${i}:${medida.clave}`,
                    ficha: ram,
                    posicion,
                    crear: () => crearPiezaGlb('ram', {}, () => crearRam(mat), ventiladores),
                });
            }
        });
        if (estado.gpu) {
            const fans = ventiladoresGpu(estado.gpu);
            const largoGpu = Number(estado.gpu.largo);
            const ranura = anclaPlaca('pcie', formato, 0, formatoCaja);
            pedidos.push({
                clave: `gpu:${estado.gpu.id}:${fans}:${formato || ''}:${Number.isFinite(largoGpu) ? largoGpu : ''}`,
                ficha: estado.gpu,
                posicion: ranura,
                crear: () => {
                    if (fans >= 3) {
                        return crearPiezaGlb('gpu', {}, () => crearGpu(fans, mat), ventiladores);
                    }
                    const armarCorta = () => {
                        const tarjeta = crearGpu(fans, mat);
                        if (formato === 'Micro-ATX') {
                            const soporte = tarjeta.getObjectByName('soporte-gpu');
                            if (soporte) {
                                soporte.position.set(-0.005, -0.036, -0.005);
                            }
                            const tapa = tarjeta.getObjectByName('backplate-gpu');
                            if (tapa) {
                                tapa.position.y = 0.013;
                            }
                        }
                        return tarjeta;
                    };
                    if (Number.isFinite(largoGpu) && largoGpu > 0 && largoGpu <= 170) {
                        return crearPiezaGlb('gpuItx', { formato }, armarCorta, ventiladores);
                    }
                    if (formato === 'Micro-ATX' || formato === 'ATX') {
                        return crearPiezaGlb('gpuCorta', { formato }, armarCorta, ventiladores);
                    }
                    if (Number.isFinite(largoGpu) && largoGpu < 280) {
                        return crearPiezaGlb('gpuCorta', { formato }, armarCorta, ventiladores);
                    }
                    return presentar(armarCorta(), 'gpu2');
                },
            });
        }
        const conteoDisco = { hdd: 0, sata: 0, m2: 0 };
        let anclaM2Previa = null;
        let omitidos = 0;
        (estado.discos || []).forEach((disco) => {
            const clase = claseDisco(disco);
            const pedidas = Number(disco.cantidad);
            const pedidasNum = Math.max(1, Math.min(4, Number.isFinite(pedidas) ? Math.floor(pedidas) : 1));
            const enTorre = formatoCaja === 'Micro-ATX' || formatoCaja === 'ATX';
            const fichaCaja = fichaGabinete(formatoCaja);
            if (clase !== 'm2' && !fichaCaja[clase]) {
                omitidos += pedidasNum;
                return;
            }
            const tope = clase === 'm2' ? (formato === 'ATX' ? 3 : 2) : (enTorre ? 2 : 1);
            const copias = clase === 'm2' || enTorre ? pedidasNum : 1;
            for (let copia = 0; copia < copias; copia += 1) {
                const n = conteoDisco[clase];
                if (n >= tope) {
                    omitidos += copias - copia;
                    break;
                }
                let posicion;
                let tipo;
                const ranuraM2 = clase === 'm2' ? puntoM2(formato, n) : null;
                if (clase === 'm2') {
                    tipo = 'm2';
                    posicion = anclaPlaca('m2', formato, n, formatoCaja);
                    if (anclaM2Previa && posicion && posicion.distanceTo(anclaM2Previa) < 0.012) {
                        posicion = posicion.clone();
                        posicion.y += 0.018 * (n + 1);
                    }
                    anclaM2Previa = posicion;
                } else if (clase === 'hdd') {
                    tipo = 'hdd';
                    posicion = puesto('hdd', n, formatoCaja);
                } else {
                    tipo = 'sata';
                    posicion = puesto('sata', n, formatoCaja);
                }
                conteoDisco[clase] += 1;
                pedidos.push({
                    clave: `disco:${disco.id}:${clase}:${n}`,
                    ficha: disco,
                    posicion,
                    crear: () => crearPiezaGlb(tipo, {
                        formato,
                        pivote: ranuraM2 && ranuraM2.pivote,
                        reverso: Boolean(ranuraM2 && ranuraM2.reverso),
                    }, () => crearDisco(clase, mat), ventiladores),
                });
            }
        });
        const avisoBahias = document.getElementById('pc-visualizador-bahias');
        if (avisoBahias) {
            avisoBahias.hidden = omitidos < 1;
            avisoBahias.textContent = omitidos > 0
                ? 'Hay unidades de almacenamiento que no caben en las bahías de esta vista.'
                : '';
        }
        if (estado.fuente) {
            pedidos.push({
                clave: `fuente:${estado.fuente.id}:${formato || ''}:${/sfx/i.test(estado.fuente.nombre || '') ? 'sfx' : 'atx'}:${formatoCaja || ''}`,
                ficha: estado.fuente,
                posicion: puesto('fuente', 0, formatoCaja),
                crear: () => crearPiezaGlb('fuente', {
                    formato: formatoCaja,
                    sfx: /sfx/i.test(estado.fuente.nombre || ''),
                }, () => crearFuente(mat), ventiladores),
            });
        }
        dibujarMarcadores(formato, formatoCaja);
        return pedidos;
    }

    function dibujarMarcadores(formato, formatoCaja) {
        const previo = gabinete.getObjectByName('marcadores-ancla');
        if (previo) {
            gabinete.remove(previo);
        }
        if (!window.hwMarcadores || !formato) {
            return;
        }
        const grupo = new THREE.Group();
        grupo.name = 'marcadores-ancla';
        const puntos = [
            [anclaPlaca('socket', formato, 0, formatoCaja), 0xff3355],
            [anclaPlaca('pcie', formato, 0, formatoCaja), 0x3388ff],
            [anclaPlaca('m2', formato, 0, formatoCaja), 0xffcc33],
        ];
        for (let i = 0; i < 4; i += 1) {
            const punto = anclaPlaca('dimm', formato, i, formatoCaja);
            if (punto) {
                puntos.push([punto, 0x33dd66]);
            }
        }
        puntos.forEach(([punto, color]) => {
            const esfera = new THREE.Mesh(
                new THREE.SphereGeometry(0.04, 10, 8),
                new THREE.MeshBasicMaterial({ color, depthTest: false }),
            );
            esfera.position.copy(punto);
            esfera.renderOrder = 5;
            esfera.raycast = () => {};
            grupo.add(esfera);
        });
        gabinete.add(grupo);
    }

    function retirar(registro, rapido) {
        const fuera = registro.grupo.position.clone();
        fuera.x += 2.3;
        desplazar(registro.grupo, fuera, rapido ? 120 : 360, () => {
            registro.grupo.traverse((nodo) => {
                if (nodo.userData && nodo.userData.ventilador) {
                    const indice = ventiladores.indexOf(nodo);
                    if (indice >= 0) {
                        ventiladores.splice(indice, 1);
                    }
                }
            });
            gabinete.remove(registro.grupo);
            liberar(registro.grupo);
            if (seleccionado === registro.grupo) {
                seleccionado = null;
                ficha.hidden = true;
            }
        });
        piezas.delete(registro.clave);
    }

    function mostrarFicha(datos) {
        if (!datos) {
            ficha.textContent = 'Gabinete genérico';
        } else {
            const partes = [datos.categoria, datos.marca, datos.nombre, precioVisible(datos.precio)]
                .filter((valor) => valor);
            ficha.textContent = partes.join(' · ');
        }
        ficha.hidden = false;
    }

    function elegir(grupo) {
        fijarContorno(apuntado, false);
        seleccionado = grupo;
        fijarContorno(grupo, false);
        mostrarFicha(grupo.userData.ficha || null);
        if (modoInspeccion === 2) {
            aplicarInspeccion();
        }
    }

    function acercar(grupo) {
        const centro = new THREE.Vector3();
        new THREE.Box3().setFromObject(grupo).getCenter(centro);
        const offset = camara.position.clone().sub(controles.target);
        if (offset.length() > 3.2) {
            offset.setLength(3.2);
        }
        animaciones.push({
            camara: true,
            inicio: camara.position.clone(),
            destino: centro.clone().add(offset),
            miraInicio: controles.target.clone(),
            miraFin: centro.clone(),
            t0: performance.now(),
            duracion: 450,
        });
    }

    let estadoActual = null;
    function tapasM2(formato, cantidad) {
        if (formato !== 'Micro-ATX' && formato !== 'ATX') {
            return;
        }
        piezas.forEach((registro) => {
            if (!String(registro.clave).startsWith('placa:')) {
                return;
            }
            const aplicar = () => {
                registro.grupo.traverse((nodo) => {
                    const nombre = (nodo.name || '').replace(/\s/g, '_');
                    const ocultar = nombre.startsWith('M2_heatsink_cover')
                        ? cantidad >= 1
                        : nombre.startsWith('Chipset_and_M2_heatsink') && cantidad >= 2;
                    if (!nombre.startsWith('M2_heatsink_cover') && !nombre.startsWith('Chipset_and_M2_heatsink')) {
                        return;
                    }
                    nodo.visible = !ocultar;
                    nodo.raycast = ocultar ? () => {} : THREE.Mesh.prototype.raycast;
                });
            };
            aplicar();
            const carga = registro.grupo.userData.carga;
            if (carga && typeof carga.then === 'function') {
                carga.then(aplicar);
            }
        });
    }

    function sincronizar(estado) {
        if (!encendido || !estado) {
            return;
        }
        estadoActual = estado;
        let ocupadas = 0;
        ['placa', 'cpu', 'cooler', 'gpu', 'gabinete', 'fuente'].forEach((clave) => {
            if (estado[clave]) {
                ocupadas += 1;
            }
        });
        if (estado.rams && estado.rams.length) {
            ocupadas += 1;
        }
        if (estado.discos && estado.discos.length) {
            ocupadas += 1;
        }
        conteo.textContent = `${ocupadas} de 8 categorías`;
        gabinete.userData.ficha = estado.gabinete || null;
        if (!seleccionado || seleccionado === gabinete) {
            mostrarFicha(gabinete.userData.ficha);
        }
        const formatoCase = formatoMontaje(estado);
        if (gabinete.userData.modelo !== fichaGabinete(formatoCase).id) {
            incorporarGabineteDetallado(
                gabinete,
                mat,
                ventiladores,
                document.getElementById('pc-visualizador-carga'),
                formatoCase,
            ).then(() => {
                if (!estadoActual) {
                    return;
                }
                const vigente = formatoMontaje(estadoActual);
                if (gabinete.userData.modelo === fichaGabinete(vigente).id) {
                    sincronizar(estadoActual);
                }
            });
            return;
        }
        const pedidos = plan(estado);
        const claves = new Set(pedidos.map((pedido) => pedido.clave));
        const altas = pedidos.filter((pedido) => !piezas.has(pedido.clave)).length;
        const bajas = [...piezas.keys()].filter((clave) => !claves.has(clave)).length;
        const rapido = altas + bajas > 2;
        piezas.forEach((registro, clave) => {
            if (!claves.has(clave)) {
                retirar(registro, rapido);
            }
        });
        pedidos.forEach((pedido) => {
            const previa = piezas.get(pedido.clave);
            if (previa) {
                previa.grupo.userData.ficha = pedido.ficha;
                if (previa.grupo.position.distanceTo(pedido.posicion) > 0.05) {
                    desplazar(previa.grupo, pedido.posicion, rapido ? 140 : 280);
                }
                return;
            }
            const grupo = pedido.crear();
            grupo.position.copy(pedido.posicion);
            anclar(grupo, pedido.ficha, pedido.clave);
            const registro = { clave: pedido.clave, grupo };
            piezas.set(pedido.clave, registro);
            grupo.position.x += 2.3;
            desplazar(grupo, pedido.posicion, rapido ? 160 : 520);
        });
        tapasM2(
            estado.placa && estado.placa.formato,
            pedidos.filter((pedido) => pedido.clave.includes(':m2:')).length,
        );
        aplicarInspeccion();
    }

    function piezaBajo(evento) {
        const recta = renderer.domElement.getBoundingClientRect();
        const x = ((evento.clientX - recta.left) / recta.width) * 2 - 1;
        const y = -((evento.clientY - recta.top) / recta.height) * 2 + 1;
        const rayo = new THREE.Raycaster();
        rayo.setFromCamera(new THREE.Vector2(x, y), camara);
        const golpes = rayo.intersectObject(gabinete, true);
        for (let i = 0; i < golpes.length; i += 1) {
            let nodo = golpes[i].object;
            while (nodo) {
                if (nodo.userData && nodo.userData.clave) {
                    return nodo;
                }
                nodo = nodo.parent;
            }
        }
        return null;
    }

    let apuntado = null;
    function ocultarApuntado() {
        fijarContorno(apuntado, false);
        apuntado = null;
    }
    renderer.domElement.addEventListener('pointerdown', (evento) => {
        const pieza = piezaBajo(evento);
        if (pieza) {
            elegir(pieza);
        }
    });
    renderer.domElement.addEventListener('pointerleave', () => {
        ocultarApuntado();
    });
    if (!tactil) {
        renderer.domElement.addEventListener('pointermove', (evento) => {
            const pieza = piezaBajo(evento);
            const objetivo = pieza && pieza.userData.clave !== 'gabinete' ? pieza : null;
            renderer.domElement.style.cursor = pieza ? 'pointer' : '';
            if (pieza && pieza !== seleccionado) {
                mostrarFicha(pieza.userData.ficha || null);
            }
            if (objetivo === apuntado) {
                return;
            }
            fijarContorno(apuntado, false);
            apuntado = objetivo;
            if (apuntado && apuntado !== seleccionado) {
                fijarContorno(apuntado, true);
            }
        });
    }

    function zoom(factor) {
        const desplazamiento = camara.position.clone().sub(controles.target);
        const distancia = THREE.MathUtils.clamp(
            desplazamiento.length() * factor,
            controles.minDistance,
            controles.maxDistance,
        );
        desplazamiento.setLength(distancia);
        camara.position.copy(controles.target).add(desplazamiento);
    }

    document.getElementById('pc-visualizador-camara').addEventListener('click', () => {
        encuadrar();
    });
    alEscalar(() => {
        window.setTimeout(() => {
            if (estadoActual) {
                sincronizar(estadoActual);
            }
        }, 0);
    });
    const botonVidrio = document.getElementById('pc-visualizador-vidrio');
    botonVidrio.addEventListener('click', () => {
        const visible = !gabinete.userData.vidrio.visible;
        gabinete.userData.vidrio.visible = visible;
        reflejarBotonVidrio(visible);
    });
    let modoInspeccion = 0;
    const botonInspeccion = document.getElementById('pc-visualizador-inspeccion');
    function aplicarInspeccion() {
        const translucido = modoInspeccion > 0;
        gabinete.traverse((nodo) => {
            if (!nodo.isMesh || !nodo.userData) {
                return;
            }
            const cubierta = nodo.userData.panel === 'cubierta';
            if (nodo.userData.panel !== 'cuerpo' && !cubierta) {
                return;
            }
            const lista = Array.isArray(nodo.material) ? nodo.material : [nodo.material];
            lista.forEach((material) => {
                if (!material || material.opacity == null) {
                    return;
                }
                material.transparent = translucido;
                material.opacity = translucido ? (cubierta ? 0.1 : 0.42) : 1;
                material.depthWrite = !translucido;
                material.needsUpdate = true;
            });
        });
        gabinete.children.forEach((hijo) => {
            if (!hijo.userData || !hijo.userData.clave) {
                return;
            }
            hijo.visible = modoInspeccion !== 2 || hijo === seleccionado;
        });
    }
    if (botonInspeccion) {
        botonInspeccion.addEventListener('click', () => {
            modoInspeccion = (modoInspeccion + 1) % 3;
            aplicarInspeccion();
            const textos = ['Ver interior del gabinete', 'Aislar pieza seleccionada', 'Volver a la vista completa'];
            botonInspeccion.setAttribute('aria-pressed', modoInspeccion === 0 ? 'false' : 'true');
            botonInspeccion.setAttribute('aria-label', textos[modoInspeccion]);
            botonInspeccion.title = textos[modoInspeccion];
        });
    }
    document.getElementById('pc-visualizador-acercar').addEventListener('click', () => {
        if (seleccionado) {
            acercar(seleccionado);
            return;
        }
        zoom(0.82);
    });
    document.getElementById('pc-visualizador-alejar').addEventListener('click', () => zoom(1.22));
    const botonAmpliar = document.getElementById('pc-visualizador-ampliar');
    botonAmpliar.addEventListener('click', () => {
        if (document.fullscreenElement === raiz) {
            document.exitFullscreen();
            return;
        }
        if (raiz.requestFullscreen) {
            raiz.requestFullscreen();
        }
    });

    window.hwRecibirArmado = sincronizar;
    if (window.hwArmadoPendiente) {
        sincronizar(window.hwArmadoPendiente);
        window.hwArmadoPendiente = null;
    }

    function cuadro() {
        if (!encendido) {
            return;
        }
        const ahora = performance.now();
        for (let i = animaciones.length - 1; i >= 0; i -= 1) {
            const animacion = animaciones[i];
            const avance = Math.min(1, (ahora - animacion.t0) / animacion.duracion);
            const suave = avance < 0.5 ? 2 * avance * avance : 1 - ((-2 * avance + 2) ** 2) / 2;
            if (animacion.camara) {
                camara.position.lerpVectors(animacion.inicio, animacion.destino, suave);
                controles.target.lerpVectors(animacion.miraInicio, animacion.miraFin, suave);
            } else {
                animacion.grupo.position.lerpVectors(animacion.inicio, animacion.destino, suave);
            }
            if (avance >= 1) {
                if (animacion.alFinal) {
                    animacion.alFinal();
                }
                animaciones.splice(i, 1);
            }
        }
        ventiladores.forEach((fan) => {
            const eje = (fan.userData && fan.userData.eje) || 'z';
            fan.rotation[eje] += 0.06;
        });
        controles.update();
        renderer.render(escena, camara);
        window.requestAnimationFrame(cuadro);
    }
    cuadro();

    window.addEventListener('pagehide', () => {
        encendido = false;
        observador.disconnect();
        controles.dispose();
        renderer.dispose();
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
} else {
    iniciar();
}
