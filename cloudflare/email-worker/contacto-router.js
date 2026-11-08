/**
 * Reenvío exclusivo de contacto@hardwarehouse.cl.
 *
 * Este archivo no lo despliega Railway ni el release de Django.
 * Hay que publicarlo aparte con Wrangler y asociarlo, en Email Routing,
 * solo a la dirección personalizada contacto@hardwarehouse.cl.
 * Los dos destinos deben estar verificados en Cloudflare antes del forward.
 */

const DESTINO_PUBLICO = "contacto@hardwarehouse.cl";
const DESTINOS = [
  "trabajadorhardwarehouse@gmail.com",
  "administradorhardwarehouse@gmail.com",
];
// Esos dos buzones corresponden a WORKER_EMAIL y ADMIN_EMAIL.
// Django no los lee. Verifícalos en Cloudflare antes de publicar el Worker.

function direccion(valor) {
  const texto = String(valor || "").trim().toLowerCase();
  const entreAngulos = texto.match(/<([^>]+)>/);
  return (entreAngulos ? entreAngulos[1] : texto).trim();
}

export default {
  async email(message) {
    if (direccion(message.to) !== DESTINO_PUBLICO) {
      message.setReject("Esta regla solo atiende contacto@hardwarehouse.cl");
      return;
    }
    for (const destino of DESTINOS) {
      await message.forward(destino);
    }
  },
};
