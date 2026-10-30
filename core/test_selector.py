from pathlib import Path

from django.test import SimpleTestCase


class SelectorCompactoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.js = Path(__file__).resolve().parent.joinpath(
            'static', 'core', 'js', 'pc-builder.js',
        ).read_text(encoding='utf-8')

    def test_la_tarjeta_muestra_estado_y_oculta_el_motivo(self):
        funcion = self._funcion('detalleRecomendacion')
        self.assertIn('armado-estado-badge', funcion)
        self.assertIn('armado-estado-ok', self.js)
        self.assertIn('armado-estado-no', self.js)
        self.assertIn('armado-estado-revisar', self.js)
        visual = self._funcion('estadoVisual')
        self.assertIn('Compatible', visual)
        self.assertIn('Incompatible', visual)
        self.assertIn('No verificada', visual)
        self.assertIn('Disponible', visual)
        self.assertIn('armado-estado-disponible', visual)
        self.assertNotIn('Parcial', visual)
        self.assertIn('armado-opcion-precio', self.js)
        self.assertNotIn('text-success flex-shrink-0', self.js)
        self.assertIn('<details class="armado-detalles">', funcion)
        self.assertIn('Ver motivo', funcion)
        self.assertIn('Ver detalles', funcion)
        self.assertIn('textosServidor(candidato)', funcion)
        self.assertNotIn('text-danger', funcion)
        self.assertNotIn('text-warning', funcion)
        self.assertNotIn('text-success', funcion)

    def test_las_caracteristicas_principales_no_repiten_el_detalle_tecnico(self):
        ram = self._funcion('caracteristicasPrincipales')
        self.assertIn("categoriaModal === 'memoria_ram'", ram)
        self.assertIn('tipo_ddr', ram)
        self.assertIn('capacidad_gb', ram)
        self.assertIn('velocidad_mhz', ram)
        self.assertIn('formato_ram', ram)
        self.assertNotIn('modulos_por_producto', ram)
        self.assertNotIn('Velocidad indicada', ram)
        self.assertIn('Velocidad indicada', self._funcion('lineasEspecificacion'))
        self.assertIn('specYaVisible', self._funcion('specsSecundarias'))

    def test_el_filtro_y_la_seleccion_siguen_disponibles(self):
        self.assertIn('id="solo-compatibles"', self.js)
        self.assertIn("candidato.estado !== 'compatible'", self.js)
        self.assertIn('function handleSelectionChange', self.js)
        self.assertIn('function activarSeleccion', self.js)
        self.assertIn(".closest('.armado-detalles')", self.js)
        self.assertNotIn('function checkCompatibility', self.js)
        self.assertNotIn('function evaluarSocket', self.js)

    def test_el_mismo_resumen_cubre_el_resto_de_selectores(self):
        ram = self._funcion('caracteristicasPrincipales')
        for categoria in (
            'procesador',
            'placa_madre',
            'tarjeta_grafica',
            'fuente_de_poder',
            'gabinete',
            'refrigeracion_cooler',
            'almacenamiento',
        ):
            self.assertIn(f"categoriaModal === '{categoria}'", ram)

    def _funcion(self, nombre):
        marca = f'function {nombre}'
        inicio = self.js.index(marca)
        self.assertGreaterEqual(inicio, 0, nombre)
        siguiente = self.js.index('\n    function ', inicio + len(marca))
        self.assertGreater(siguiente, inicio, nombre)
        return self.js[inicio:siguiente]
