-- HardWareHouse: datos de prueba (regiones, comunas, proveedores, productos)
-- Regenerar: python scripts/generate_seed_test_data.py
-- Precios y stock de productos son sintéticos; no son un precio de mercado verificado.
-- Este archivo hace TRUNCATE de pedidos, carritos y catálogo. No ejecutarlo en producción.
-- Para corregir solo el catálogo demo sin borrar pedidos:
--   python manage.py sincronizar_catalogo_demo --dry-run
--   python manage.py sincronizar_catalogo_demo --apply
SET client_encoding = 'UTF8';
BEGIN;

-- Este TRUNCATE borra pedidos, carritos y catálogo. No sirve para actualizar un catálogo ya cargado.
TRUNCATE TABLE
  core_itempedido,
  core_pagoboleta,
  core_pedido,
  core_itemcarrito,
  core_carrito,
  core_favorito,
  core_comentario,
  core_ventilador,
  core_refrigeracioncooler,
  core_fuentedepoder,
  core_gabinete,
  core_almacenamientohdd,
  core_almacenamientossd,
  core_placamadre,
  core_memoriaram,
  core_tarjetagrafica,
  core_procesador,
  core_proveedor,
  core_comuna,
  core_region
RESTART IDENTITY CASCADE;

INSERT INTO core_region (id, numero, nombre) VALUES
(1, 15, 'Arica y Parinacota'),
(2, 1, 'Tarapacá'),
(3, 2, 'Antofagasta'),
(4, 3, 'Atacama'),
(5, 4, 'Coquimbo'),
(6, 5, 'Valparaíso'),
(7, 6, 'Libertador General Bernardo O''Higgins'),
(8, 7, 'Maule'),
(9, 16, 'Ñuble'),
(10, 8, 'Biobío'),
(11, 9, 'La Araucanía'),
(12, 14, 'Los Ríos'),
(13, 10, 'Los Lagos'),
(14, 11, 'Aysén del General Carlos Ibáñez del Campo'),
(15, 12, 'Magallanes y de la Antártica Chilena'),
(16, 13, 'Región Metropolitana de Santiago');

INSERT INTO core_comuna (id, nombre, region_id) VALUES
(1, 'Arica', 1),
(2, 'Camarones', 1),
(3, 'Putre', 1),
(4, 'General Lagos', 1),
(5, 'Iquique', 2),
(6, 'Alto Hospicio', 2),
(7, 'Pozo Almonte', 2),
(8, 'Camiña', 2),
(9, 'Colchane', 2),
(10, 'Huara', 2),
(11, 'Pica', 2),
(12, 'Antofagasta', 3),
(13, 'Mejillones', 3),
(14, 'Sierra Gorda', 3),
(15, 'Taltal', 3),
(16, 'Calama', 3),
(17, 'Ollagüe', 3),
(18, 'San Pedro de Atacama', 3),
(19, 'Tocopilla', 3),
(20, 'María Elena', 3),
(21, 'Copiapó', 4),
(22, 'Caldera', 4),
(23, 'Tierra Amarilla', 4),
(24, 'Chañaral', 4),
(25, 'Diego de Almagro', 4),
(26, 'Vallenar', 4),
(27, 'Alto del Carmen', 4),
(28, 'Freirina', 4),
(29, 'Huasco', 4),
(30, 'La Serena', 5),
(31, 'Coquimbo', 5),
(32, 'Andacollo', 5),
(33, 'La Higuera', 5),
(34, 'Paiguano', 5),
(35, 'Vicuña', 5),
(36, 'Illapel', 5),
(37, 'Canela', 5),
(38, 'Los Vilos', 5),
(39, 'Salamanca', 5),
(40, 'Ovalle', 5),
(41, 'Combarbalá', 5),
(42, 'Monte Patria', 5),
(43, 'Punitaqui', 5),
(44, 'Río Hurtado', 5),
(45, 'Valparaíso', 6),
(46, 'Casablanca', 6),
(47, 'Concón', 6),
(48, 'Juan Fernández', 6),
(49, 'Puchuncaví', 6),
(50, 'Quintero', 6),
(51, 'Viña del Mar', 6),
(52, 'Isla de Pascua', 6),
(53, 'Los Andes', 6),
(54, 'Calle Larga', 6),
(55, 'Rinconada', 6),
(56, 'San Esteban', 6),
(57, 'La Ligua', 6),
(58, 'Cabildo', 6),
(59, 'Papudo', 6),
(60, 'Petorca', 6),
(61, 'Zapallar', 6),
(62, 'Quillota', 6),
(63, 'Calera', 6),
(64, 'Hijuelas', 6),
(65, 'La Cruz', 6),
(66, 'Nogales', 6),
(67, 'San Antonio', 6),
(68, 'Algarrobo', 6),
(69, 'Cartagena', 6),
(70, 'El Quisco', 6),
(71, 'El Tabo', 6),
(72, 'Santo Domingo', 6),
(73, 'San Felipe', 6),
(74, 'Catemu', 6),
(75, 'Llaillay', 6),
(76, 'Panquehue', 6),
(77, 'Putaendo', 6),
(78, 'Santa María', 6),
(79, 'Quilpué', 6),
(80, 'Limache', 6),
(81, 'Olmué', 6),
(82, 'Villa Alemana', 6),
(83, 'Rancagua', 7),
(84, 'Codegua', 7),
(85, 'Coinco', 7),
(86, 'Coltauco', 7),
(87, 'Doñihue', 7),
(88, 'Graneros', 7),
(89, 'Las Cabras', 7),
(90, 'Machalí', 7),
(91, 'Malloa', 7),
(92, 'Mostazal', 7),
(93, 'Olivar', 7),
(94, 'Peumo', 7),
(95, 'Pichidegua', 7),
(96, 'Quinta de Tilcoco', 7),
(97, 'Rengo', 7),
(98, 'Requínoa', 7),
(99, 'San Vicente', 7),
(100, 'Pichilemu', 7),
(101, 'La Estrella', 7),
(102, 'Litueche', 7),
(103, 'Marchihue', 7),
(104, 'Navidad', 7),
(105, 'Paredones', 7),
(106, 'San Fernando', 7),
(107, 'Chépica', 7),
(108, 'Chimbarongo', 7),
(109, 'Lolol', 7),
(110, 'Nancagua', 7),
(111, 'Palmilla', 7),
(112, 'Peralillo', 7),
(113, 'Placilla', 7),
(114, 'Pumanque', 7),
(115, 'Santa Cruz', 7),
(116, 'Talca', 8),
(117, 'Constitución', 8),
(118, 'Curepto', 8),
(119, 'Empedrado', 8),
(120, 'Maule', 8),
(121, 'Pelarco', 8),
(122, 'Pencahue', 8),
(123, 'Río Claro', 8),
(124, 'San Clemente', 8),
(125, 'San Rafael', 8),
(126, 'Cauquenes', 8),
(127, 'Chanco', 8),
(128, 'Pelluhue', 8),
(129, 'Curicó', 8),
(130, 'Hualañé', 8),
(131, 'Licantén', 8),
(132, 'Molina', 8),
(133, 'Rauco', 8),
(134, 'Romeral', 8),
(135, 'Sagrada Familia', 8),
(136, 'Teno', 8),
(137, 'Vichuquén', 8),
(138, 'Linares', 8),
(139, 'Colbún', 8),
(140, 'Longaví', 8),
(141, 'Parral', 8),
(142, 'Retiro', 8),
(143, 'San Javier', 8),
(144, 'Villa Alegre', 8),
(145, 'Yerbas Buenas', 8),
(146, 'Cobquecura', 9),
(147, 'Coelemu', 9),
(148, 'Ninhue', 9),
(149, 'Portezuelo', 9),
(150, 'Quirihue', 9),
(151, 'Ránquil', 9),
(152, 'Treguaco', 9),
(153, 'Bulnes', 9),
(154, 'Chillán Viejo', 9),
(155, 'Chillán', 9),
(156, 'El Carmen', 9),
(157, 'Pemuco', 9),
(158, 'Pinto', 9),
(159, 'Quillón', 9),
(160, 'San Ignacio', 9),
(161, 'Yungay', 9),
(162, 'Coihueco', 9),
(163, 'Ñiquén', 9),
(164, 'San Carlos', 9),
(165, 'San Fabián', 9),
(166, 'San Nicolás', 9),
(167, 'Concepción', 10),
(168, 'Coronel', 10),
(169, 'Chiguayante', 10),
(170, 'Florida', 10),
(171, 'Hualqui', 10),
(172, 'Lota', 10),
(173, 'Penco', 10),
(174, 'San Pedro de la Paz', 10),
(175, 'Santa Juana', 10),
(176, 'Talcahuano', 10),
(177, 'Tomé', 10),
(178, 'Hualpén', 10),
(179, 'Lebu', 10),
(180, 'Arauco', 10),
(181, 'Cañete', 10),
(182, 'Contulmo', 10),
(183, 'Curanilahue', 10),
(184, 'Los Álamos', 10),
(185, 'Tirúa', 10),
(186, 'Los Ángeles', 10),
(187, 'Antuco', 10),
(188, 'Cabrero', 10),
(189, 'Laja', 10),
(190, 'Mulchén', 10),
(191, 'Nacimiento', 10),
(192, 'Negrete', 10),
(193, 'Quilaco', 10),
(194, 'Quilleco', 10),
(195, 'San Rosendo', 10),
(196, 'Santa Bárbara', 10),
(197, 'Tucapel', 10),
(198, 'Yumbel', 10),
(199, 'Alto Biobío', 10),
(200, 'Temuco', 11),
(201, 'Carahue', 11),
(202, 'Cunco', 11),
(203, 'Curarrehue', 11),
(204, 'Freire', 11),
(205, 'Galvarino', 11),
(206, 'Gorbea', 11),
(207, 'Lautaro', 11),
(208, 'Loncoche', 11),
(209, 'Melipeuco', 11),
(210, 'Nueva Imperial', 11),
(211, 'Padre las Casas', 11),
(212, 'Perquenco', 11),
(213, 'Pitrufquén', 11),
(214, 'Pucón', 11),
(215, 'Saavedra', 11),
(216, 'Teodoro Schmidt', 11),
(217, 'Toltén', 11),
(218, 'Vilcún', 11),
(219, 'Villarrica', 11),
(220, 'Cholchol', 11),
(221, 'Angol', 11),
(222, 'Collipulli', 11),
(223, 'Curacautín', 11),
(224, 'Ercilla', 11),
(225, 'Lonquimay', 11),
(226, 'Los Sauces', 11),
(227, 'Lumaco', 11),
(228, 'Purén', 11),
(229, 'Renaico', 11),
(230, 'Traiguén', 11),
(231, 'Victoria', 11),
(232, 'Valdivia', 12),
(233, 'Corral', 12),
(234, 'Lanco', 12),
(235, 'Los Lagos', 12),
(236, 'Máfil', 12),
(237, 'Mariquina', 12),
(238, 'Paillaco', 12),
(239, 'Panguipulli', 12),
(240, 'La Unión', 12),
(241, 'Futrono', 12),
(242, 'Lago Ranco', 12),
(243, 'Río Bueno', 12),
(244, 'Puerto Montt', 13),
(245, 'Calbuco', 13),
(246, 'Cochamó', 13),
(247, 'Fresia', 13),
(248, 'Frutillar', 13),
(249, 'Los Muermos', 13),
(250, 'Llanquihue', 13),
(251, 'Maullín', 13),
(252, 'Puerto Varas', 13),
(253, 'Castro', 13),
(254, 'Ancud', 13),
(255, 'Chonchi', 13),
(256, 'Curaco de Vélez', 13),
(257, 'Dalcahue', 13),
(258, 'Puqueldón', 13),
(259, 'Queilén', 13),
(260, 'Quellón', 13),
(261, 'Quemchi', 13),
(262, 'Quinchao', 13),
(263, 'Osorno', 13),
(264, 'Puerto Octay', 13),
(265, 'Purranque', 13),
(266, 'Puyehue', 13),
(267, 'Río Negro', 13),
(268, 'San Juan de la Costa', 13),
(269, 'San Pablo', 13),
(270, 'Chaitén', 13),
(271, 'Futaleufú', 13),
(272, 'Hualaihué', 13),
(273, 'Palena', 13),
(274, 'Coihaique', 14),
(275, 'Lago Verde', 14),
(276, 'Aisén', 14),
(277, 'Cisnes', 14),
(278, 'Guaitecas', 14),
(279, 'Cochrane', 14),
(280, 'O''Higgins', 14),
(281, 'Tortel', 14),
(282, 'Chile Chico', 14),
(283, 'Río Ibáñez', 14),
(284, 'Punta Arenas', 15),
(285, 'Laguna Blanca', 15),
(286, 'Río Verde', 15),
(287, 'San Gregorio', 15),
(288, 'Cabo de Hornos (Ex Navarino)', 15),
(289, 'Antártica', 15),
(290, 'Porvenir', 15),
(291, 'Primavera', 15),
(292, 'Timaukel', 15),
(293, 'Natales', 15),
(294, 'Torres del Paine', 15),
(295, 'Cerrillos', 16),
(296, 'Cerro Navia', 16),
(297, 'Conchalí', 16),
(298, 'El Bosque', 16),
(299, 'Estación Central', 16),
(300, 'Huechuraba', 16),
(301, 'Independencia', 16),
(302, 'La Cisterna', 16),
(303, 'La Florida', 16),
(304, 'La Granja', 16),
(305, 'La Pintana', 16),
(306, 'La Reina', 16),
(307, 'Las Condes', 16),
(308, 'Lo Barnechea', 16),
(309, 'Lo Espejo', 16),
(310, 'Lo Prado', 16),
(311, 'Macul', 16),
(312, 'Maipú', 16),
(313, 'Ñuñoa', 16),
(314, 'Pedro Aguirre Cerda', 16),
(315, 'Peñalolén', 16),
(316, 'Providencia', 16),
(317, 'Pudahuel', 16),
(318, 'Quilicura', 16),
(319, 'Quinta Normal', 16),
(320, 'Recoleta', 16),
(321, 'Renca', 16),
(322, 'San Joaquín', 16),
(323, 'San Miguel', 16),
(324, 'San Ramón', 16),
(325, 'Vitacura', 16),
(326, 'Puente Alto', 16),
(327, 'Pirque', 16),
(328, 'San José de Maipo', 16),
(329, 'Buin', 16),
(330, 'Calera de Tango', 16),
(331, 'Paine', 16),
(332, 'San Bernardo', 16),
(333, 'Alhué', 16),
(334, 'Curacaví', 16),
(335, 'María Pinto', 16),
(336, 'Melipilla', 16),
(337, 'San Pedro', 16),
(338, 'Talagante', 16),
(339, 'Colina', 16),
(340, 'Lampa', 16),
(341, 'Tiltil', 16),
(342, 'Santiago', 16);

INSERT INTO core_proveedor (id, nombre, logo) VALUES
(1, 'Intel', NULL),
(2, 'AMD', NULL),
(3, 'NVIDIA', NULL),
(4, 'ASUS', NULL),
(5, 'Gigabyte', NULL),
(6, 'MSI', NULL),
(7, 'ASRock', NULL),
(8, 'EVGA', NULL),
(9, 'Zotac', NULL),
(10, 'PNY', NULL),
(11, 'Palit', NULL),
(12, 'Gainward', NULL),
(13, 'Sapphire', NULL),
(14, 'PowerColor', NULL),
(15, 'XFX', NULL),
(16, 'Corsair', NULL),
(17, 'G.Skill', NULL),
(18, 'Kingston', NULL),
(19, 'Crucial', NULL),
(20, 'Samsung', NULL),
(21, 'Western Digital', NULL),
(22, 'Seagate', NULL),
(23, 'SanDisk', NULL),
(24, 'ADATA', NULL),
(25, 'TeamGroup', NULL),
(26, 'Patriot', NULL),
(27, 'HyperX', NULL),
(28, 'Thermaltake', NULL),
(29, 'Cooler Master', NULL),
(30, 'NZXT', NULL),
(31, 'be quiet!', NULL),
(32, 'Seasonic', NULL),
(33, 'FSP', NULL),
(34, 'Lian Li', NULL),
(35, 'Fractal Design', NULL),
(36, 'Phanteks', NULL),
(37, 'Silverstone', NULL),
(38, 'Antec', NULL),
(39, 'Montech', NULL),
(40, 'Noctua', NULL),
(41, 'Arctic', NULL),
(42, 'Deepcool', NULL),
(43, 'ID-COOLING', NULL),
(44, 'Scythe', NULL),
(45, 'Logitech', NULL),
(46, 'Razer', NULL),
(47, 'SteelSeries', NULL),
(48, 'BenQ', NULL),
(49, 'LG', NULL),
(50, 'AOC', NULL),
(51, 'Dell', NULL),
(52, 'HP', NULL),
(53, 'Lenovo', NULL),
(54, 'Acer', NULL),
(55, 'Apple', NULL),
(56, 'Qualcomm', NULL),
(57, 'MediaTek', NULL),
(58, 'Broadcom', NULL),
(59, 'Realtek', NULL),
(60, 'TP-Link', NULL),
(61, 'D-Link', NULL),
(62, 'Netgear', NULL),
(63, 'Ubiquiti', NULL),
(64, 'Synology', NULL),
(65, 'QNAP', NULL),
(66, 'ASUSTOR', NULL),
(67, 'Toshiba', NULL),
(68, 'Hitachi', NULL),
(69, 'Lexar', NULL),
(70, 'PNY Technologies', NULL),
(71, 'Inno3D', NULL),
(72, 'Colorful', NULL),
(73, 'Biostar', NULL),
(74, 'ECS', NULL),
(75, 'Supermicro', NULL),
(76, 'Tyan', NULL),
(77, 'GALAX', NULL),
(78, 'KFA2', NULL),
(79, 'Club 3D', NULL),
(80, 'VisionTek', NULL),
(81, 'Matrox', NULL),
(82, 'Intel Arc', NULL),
(83, 'Sparkle', NULL);

-- Productos demo. El proveedor se resuelve por nombre, no por un id fijo.
-- Precio y stock son sintéticos; no son un precio de mercado verificado.

-- procesador
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(1, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 3 3100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 3 3100 para socket AM4.', 90990.00, 5, NULL, 'AM4', 4, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(2, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 3 3300X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 3 3300X para socket AM4.', 111990.00, 6, NULL, 'AM4', 4, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(3, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 3 3200G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 3 3200G para socket AM4.', 102990.00, 7, NULL, 'AM4', 4, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(4, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 3600 para socket AM4.', 133990.00, 8, NULL, 'AM4', 6, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(5, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 3600X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 3600X para socket AM4.', 149990.00, 9, NULL, 'AM4', 6, 3.80, 95);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(6, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 3600XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 3600XT para socket AM4.', 160990.00, 10, NULL, 'AM4', 6, 3.80, 95);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(7, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 4500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 4500 para socket AM4.', 101990.00, 11, NULL, 'AM4', 6, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(8, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 4600G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 4600G para socket AM4.', 122990.00, 12, NULL, 'AM4', 6, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(9, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 5500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 5500 para socket AM4.', 113990.00, 13, NULL, 'AM4', 6, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(10, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 5600 para socket AM4.', 129990.00, 14, NULL, 'AM4', 6, 3.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(11, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 5600X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 5600X para socket AM4.', 160990.00, 15, NULL, 'AM4', 6, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(12, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 5600G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 5600G para socket AM4.', 151990.00, 4, NULL, 'AM4', 6, 3.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(13, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 3700X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 3700X para socket AM4.', 202990.00, 5, NULL, 'AM4', 8, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(14, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 3800X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 3800X para socket AM4.', 233990.00, 6, NULL, 'AM4', 8, 3.90, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(15, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 3800XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 3800XT para socket AM4.', 239990.00, 7, NULL, 'AM4', 8, 3.90, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(16, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 5700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 5700 para socket AM4.', 180990.00, 8, NULL, 'AM4', 8, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(17, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 5700X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 5700X para socket AM4.', 201990.00, 9, NULL, 'AM4', 8, 3.40, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(18, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 5700G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 5700G para socket AM4.', 192990.00, 10, NULL, 'AM4', 8, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(19, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 5800X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 5800X para socket AM4.', 253990.00, 11, NULL, 'AM4', 8, 3.80, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(20, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 5800X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 5800X3D para socket AM4.', 299990.00, 12, NULL, 'AM4', 8, 3.40, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(21, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 3900X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 3900X para socket AM4.', 330990.00, 13, NULL, 'AM4', 12, 3.80, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(22, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 3900XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 3900XT para socket AM4.', 351990.00, 14, NULL, 'AM4', 12, 3.80, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(23, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 3950X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 3950X para socket AM4.', 452990.00, 15, NULL, 'AM4', 16, 3.50, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(24, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 5900X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 5900X para socket AM4.', 353990.00, 4, NULL, 'AM4', 12, 3.70, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(25, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 5950X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 5950X para socket AM4.', 499990.00, 5, NULL, 'AM4', 16, 3.40, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(26, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 7500F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 7500F para socket AM5.', 160990.00, 6, NULL, 'AM5', 6, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(27, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 7600 para socket AM5.', 201990.00, 7, NULL, 'AM5', 6, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(28, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 7600X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 7600X para socket AM5.', 232990.00, 8, NULL, 'AM5', 6, 4.70, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(29, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 7600X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 7600X3D para socket AM5.', 253990.00, 9, NULL, 'AM5', 6, 4.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(30, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 8400F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 8400F para socket AM5.', 139990.00, 10, NULL, 'AM5', 6, 4.20, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(31, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 8500G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 8500G para socket AM5.', 170990.00, 11, NULL, 'AM5', 6, 3.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(32, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 8600G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 8600G para socket AM5.', 191990.00, 12, NULL, 'AM5', 6, 4.30, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(33, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 9600X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 9600X para socket AM5.', 252990.00, 13, NULL, 'AM5', 6, 3.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(34, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 7700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 7700 para socket AM5.', 283990.00, 14, NULL, 'AM5', 8, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(35, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 7700X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 7700X para socket AM5.', 319990.00, 15, NULL, 'AM5', 8, 4.50, 105);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(36, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 7800X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 7800X3D para socket AM5.', 400990.00, 4, NULL, 'AM5', 8, 4.20, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(37, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 8700F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 8700F para socket AM5.', 221990.00, 5, NULL, 'AM5', 8, 4.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(38, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 8700G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 8700G para socket AM5.', 282990.00, 6, NULL, 'AM5', 8, 4.20, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(39, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 9700X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 9700X para socket AM5.', 363990.00, 7, NULL, 'AM5', 8, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(40, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 7 9800X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 7 9800X3D para socket AM5.', 499990.00, 8, NULL, 'AM5', 8, 4.70, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(41, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 7900', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 7900 para socket AM5.', 400990.00, 9, NULL, 'AM5', 12, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(42, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 7900X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 7900X para socket AM5.', 451990.00, 10, NULL, 'AM5', 12, 4.70, 170);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(43, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 7900X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 7900X3D para socket AM5.', 502990.00, 11, NULL, 'AM5', 12, 4.40, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(44, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 9900X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 9900X para socket AM5.', 483990.00, 12, NULL, 'AM5', 12, 4.40, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(45, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 9900X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 9900X3D para socket AM5.', 549990.00, 13, NULL, 'AM5', 12, 4.40, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(46, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 7950X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 7950X para socket AM5.', 550990.00, 14, NULL, 'AM5', 16, 4.50, 170);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(47, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 7950X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 7950X3D para socket AM5.', 601990.00, 15, NULL, 'AM5', 16, 4.20, 120);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(48, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 9950X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 9950X para socket AM5.', 652990.00, 4, NULL, 'AM5', 16, 4.30, 170);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(49, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 9 9950X3D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 9 9950X3D para socket AM5.', 753990.00, 5, NULL, 'AM5', 16, 4.30, 170);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(50, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'AMD'), 'AMD Ryzen 5 8600F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador AMD Ryzen 5 8600F para socket AM5.', 149990.00, 6, NULL, 'AM5', 6, 4.30, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(51, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-10100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-10100 para socket LGA1200.', 100990.00, 7, NULL, 'LGA1200', 4, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(52, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-10100F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-10100F para socket LGA1200.', 91990.00, 8, NULL, 'LGA1200', 4, 3.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(53, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-10105', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-10105 para socket LGA1200.', 112990.00, 9, NULL, 'LGA1200', 4, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(54, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-10300', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-10300 para socket LGA1200.', 123990.00, 10, NULL, 'LGA1200', 4, 3.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(55, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-10320', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-10320 para socket LGA1200.', 129990.00, 11, NULL, 'LGA1200', 4, 3.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(56, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-10400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-10400 para socket LGA1200.', 150990.00, 12, NULL, 'LGA1200', 6, 2.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(57, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-10400F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-10400F para socket LGA1200.', 131990.00, 13, NULL, 'LGA1200', 6, 2.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(58, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-10500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-10500 para socket LGA1200.', 172990.00, 14, NULL, 'LGA1200', 6, 3.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(59, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-10600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-10600 para socket LGA1200.', 183990.00, 15, NULL, 'LGA1200', 6, 3.30, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(60, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-10600K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-10600K para socket LGA1200.', 199990.00, 4, NULL, 'LGA1200', 6, 4.10, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(61, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-11400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-11400 para socket LGA1200.', 170990.00, 5, NULL, 'LGA1200', 6, 2.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(62, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-11400F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-11400F para socket LGA1200.', 151990.00, 6, NULL, 'LGA1200', 6, 2.60, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(63, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-11500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-11500 para socket LGA1200.', 182990.00, 7, NULL, 'LGA1200', 6, 2.70, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(64, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-11600K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-11600K para socket LGA1200.', 233990.00, 8, NULL, 'LGA1200', 6, 3.90, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(65, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-10700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-10700 para socket LGA1200.', 249990.00, 9, NULL, 'LGA1200', 8, 2.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(66, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-10700F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-10700F para socket LGA1200.', 230990.00, 10, NULL, 'LGA1200', 8, 2.90, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(67, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-10700K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-10700K para socket LGA1200.', 281990.00, 11, NULL, 'LGA1200', 8, 3.80, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(68, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-11700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-11700 para socket LGA1200.', 272990.00, 12, NULL, 'LGA1200', 8, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(69, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-11700K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-11700K para socket LGA1200.', 303990.00, 13, NULL, 'LGA1200', 8, 3.60, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(70, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-10850K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-10850K para socket LGA1200.', 349990.00, 14, NULL, 'LGA1200', 10, 3.60, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(71, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-10900', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-10900 para socket LGA1200.', 340990.00, 15, NULL, 'LGA1200', 10, 2.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(72, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-10900F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-10900F para socket LGA1200.', 321990.00, 4, NULL, 'LGA1200', 10, 2.80, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(73, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-10900K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-10900K para socket LGA1200.', 402990.00, 5, NULL, 'LGA1200', 10, 3.70, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(74, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-11900', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-11900 para socket LGA1200.', 353990.00, 6, NULL, 'LGA1200', 8, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(75, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-11900K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-11900K para socket LGA1200.', 429990.00, 7, NULL, 'LGA1200', 8, 3.50, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(76, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-12100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-12100 para socket LGA1700.', 130990.00, 8, NULL, 'LGA1700', 4, 3.30, 60);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(77, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-12100F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-12100F para socket LGA1700.', 111990.00, 9, NULL, 'LGA1700', 4, 3.30, 58);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(78, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-13100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-13100 para socket LGA1700.', 142990.00, 10, NULL, 'LGA1700', 4, 3.40, 60);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(79, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i3-14100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i3-14100 para socket LGA1700.', 153990.00, 11, NULL, 'LGA1700', 4, 3.50, 60);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(80, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-12400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-12400 para socket LGA1700.', 179990.00, 12, NULL, 'LGA1700', 6, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(81, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-12400F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-12400F para socket LGA1700.', 160990.00, 13, NULL, 'LGA1700', 6, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(82, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-12600K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-12600K para socket LGA1700.', 251990.00, 14, NULL, 'LGA1700', 10, 3.70, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(83, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-12600KF', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-12600KF para socket LGA1700.', 232990.00, 15, NULL, 'LGA1700', 10, 3.70, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(84, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-13400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-13400 para socket LGA1700.', 223990.00, 4, NULL, 'LGA1700', 10, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(85, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-13400F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-13400F para socket LGA1700.', 199990.00, 5, NULL, 'LGA1700', 10, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(86, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-13500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-13500 para socket LGA1700.', 240990.00, 6, NULL, 'LGA1700', 14, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(87, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-13600K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-13600K para socket LGA1700.', 301990.00, 7, NULL, 'LGA1700', 14, 3.50, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(88, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-13600KF', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-13600KF para socket LGA1700.', 282990.00, 8, NULL, 'LGA1700', 14, 3.50, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(89, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-14400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-14400 para socket LGA1700.', 233990.00, 9, NULL, 'LGA1700', 10, 2.50, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(90, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i5-14600K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i5-14600K para socket LGA1700.', 319990.00, 10, NULL, 'LGA1700', 14, 3.50, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(91, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-12700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-12700 para socket LGA1700.', 300990.00, 11, NULL, 'LGA1700', 12, 2.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(92, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-12700F', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-12700F para socket LGA1700.', 281990.00, 12, NULL, 'LGA1700', 12, 2.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(93, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-12700K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-12700K para socket LGA1700.', 352990.00, 13, NULL, 'LGA1700', 12, 3.60, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(94, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-13700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-13700 para socket LGA1700.', 363990.00, 14, NULL, 'LGA1700', 16, 2.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(95, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-13700K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-13700K para socket LGA1700.', 399990.00, 15, NULL, 'LGA1700', 16, 3.40, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(96, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-14700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-14700 para socket LGA1700.', 390990.00, 4, NULL, 'LGA1700', 20, 2.10, 65);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(97, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i7-14700K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i7-14700K para socket LGA1700.', 431990.00, 5, NULL, 'LGA1700', 20, 3.40, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(98, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-12900K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-12900K para socket LGA1700.', 452990.00, 6, NULL, 'LGA1700', 16, 3.20, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(99, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-13900K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-13900K para socket LGA1700.', 553990.00, 7, NULL, 'LGA1700', 24, 3.00, 125);
INSERT INTO core_procesador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket, nucleos, frecuencia_base, potencia_referencia_watts) VALUES
(100, 'CPU', (SELECT id FROM core_proveedor WHERE nombre = 'Intel'), 'Intel Core i9-14900K', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Procesador Intel Core i9-14900K para socket LGA1700.', 599990.00, 8, NULL, 'LGA1700', 24, 3.20, 125);

-- tarjeta_grafica
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(1, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 150990.00, 5, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(2, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 191990.00, 6, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(3, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 222990.00, 7, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(4, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 293990.00, 8, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(5, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 349990.00, 9, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(6, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 400990.00, 10, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(7, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 331990.00, 11, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(8, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 152990.00, 12, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(9, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 193990.00, 13, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(10, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 219990.00, 14, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(11, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 290990.00, 15, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(12, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 351990.00, 4, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(13, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 402990.00, 5, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(14, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 333990.00, 6, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(15, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 149990.00, 7, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(16, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 190990.00, 8, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(17, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 221990.00, 9, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(18, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 292990.00, 10, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(19, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 353990.00, 11, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(20, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 399990.00, 12, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(21, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gigabyte GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 330990.00, 13, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(22, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 151990.00, 14, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(23, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 192990.00, 15, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(24, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 223990.00, 4, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(25, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 289990.00, 5, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(26, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 350990.00, 6, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(27, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 401990.00, 7, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(28, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Zotac'), 'Zotac GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Zotac GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 332990.00, 8, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(29, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 153990.00, 9, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(30, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 189990.00, 10, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(31, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 220990.00, 11, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(32, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 291990.00, 12, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(33, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 352990.00, 13, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(34, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 403990.00, 14, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(35, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PNY GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 329990.00, 15, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(36, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 150990.00, 4, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(37, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 191990.00, 5, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(38, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 222990.00, 6, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(39, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 293990.00, 7, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(40, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 349990.00, 8, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(41, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 400990.00, 9, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(42, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Palit'), 'Palit GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Palit GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 331990.00, 10, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(43, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 152990.00, 11, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(44, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 193990.00, 12, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(45, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 219990.00, 13, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(46, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 290990.00, 14, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(47, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 351990.00, 15, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(48, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 402990.00, 4, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(49, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica EVGA GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 333990.00, 5, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(50, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 149990.00, 6, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(51, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 190990.00, 7, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(52, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 221990.00, 8, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(53, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 292990.00, 9, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(54, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 353990.00, 10, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(55, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 399990.00, 11, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(56, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'GALAX'), 'GALAX GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica GALAX GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 330990.00, 12, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(57, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 151990.00, 13, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(58, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 192990.00, 14, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(59, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 223990.00, 15, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(60, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 289990.00, 4, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(61, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 350990.00, 5, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(62, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 401990.00, 6, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(63, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Inno3D'), 'Inno3D GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Inno3D GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 332990.00, 7, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(64, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce GTX 1650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce GTX 1650, 4 GB GDDR6, PCIe 3.0.', 153990.00, 8, NULL, 4, 'GDDR6', 'PCIe 3.0', 75, 300, 170);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(65, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce GTX 1660 Super', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce GTX 1660 Super, 6 GB GDDR6, PCIe 3.0.', 189990.00, 9, NULL, 6, 'GDDR6', 'PCIe 3.0', 125, 450, 230);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(66, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce RTX 2060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce RTX 2060, 6 GB GDDR6, PCIe 3.0.', 220990.00, 10, NULL, 6, 'GDDR6', 'PCIe 3.0', 160, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(67, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce RTX 3060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce RTX 3060, 12 GB GDDR6, PCIe 4.0.', 291990.00, 11, NULL, 12, 'GDDR6', 'PCIe 4.0', 170, 550, 242);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(68, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce RTX 3060 Ti', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce RTX 3060 Ti, 8 GB GDDR6, PCIe 4.0.', 352990.00, 12, NULL, 8, 'GDDR6', 'PCIe 4.0', 200, 600, 245);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(69, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce RTX 3070', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce RTX 3070, 8 GB GDDR6, PCIe 4.0.', 403990.00, 13, NULL, 8, 'GDDR6', 'PCIe 4.0', 220, 650, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(70, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Gainward'), 'Gainward GeForce RTX 4060', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Gainward GeForce RTX 4060, 8 GB GDDR6, PCIe 4.0.', 329990.00, 14, NULL, 8, 'GDDR6', 'PCIe 4.0', 115, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(71, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sapphire'), 'Sapphire Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sapphire Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 220990.00, 15, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(72, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sapphire'), 'Sapphire Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sapphire Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 351990.00, 4, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(73, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sapphire'), 'Sapphire Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sapphire Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 282990.00, 5, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(74, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sapphire'), 'Sapphire Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sapphire Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 533990.00, 6, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(75, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PowerColor'), 'PowerColor Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PowerColor Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 219990.00, 7, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(76, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PowerColor'), 'PowerColor Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PowerColor Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 350990.00, 8, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(77, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PowerColor'), 'PowerColor Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PowerColor Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 281990.00, 9, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(78, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'PowerColor'), 'PowerColor Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica PowerColor Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 532990.00, 10, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(79, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'XFX'), 'XFX Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica XFX Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 223990.00, 11, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(80, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'XFX'), 'XFX Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica XFX Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 349990.00, 12, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(81, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'XFX'), 'XFX Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica XFX Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 280990.00, 13, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(82, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'XFX'), 'XFX Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica XFX Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 531990.00, 14, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(83, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 222990.00, 15, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(84, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 353990.00, 4, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(85, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 279990.00, 5, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(86, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 530990.00, 6, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(87, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 221990.00, 7, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(88, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 352990.00, 8, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(89, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 283990.00, 9, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(90, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASUS Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 529990.00, 10, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(91, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Radeon RX 6600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI Radeon RX 6600, 8 GB GDDR6, PCIe 4.0.', 220990.00, 11, NULL, 8, 'GDDR6', 'PCIe 4.0', 132, 500, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(92, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Radeon RX 6700 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI Radeon RX 6700 XT, 12 GB GDDR6, PCIe 4.0.', 351990.00, 12, NULL, 12, 'GDDR6', 'PCIe 4.0', 230, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(93, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Radeon RX 7600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI Radeon RX 7600, 8 GB GDDR6, PCIe 4.0.', 282990.00, 13, NULL, 8, 'GDDR6', 'PCIe 4.0', 165, 550, 240);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(94, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Radeon RX 7800 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica MSI Radeon RX 7800 XT, 16 GB GDDR6, PCIe 4.0.', 533990.00, 14, NULL, 16, 'GDDR6', 'PCIe 4.0', 263, 700, 320);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(95, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sparkle'), 'Sparkle Arc A750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sparkle Arc A750, 8 GB GDDR6, PCIe 4.0.', 229990.00, 15, NULL, 8, 'GDDR6', 'PCIe 4.0', 225, 600, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(96, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sparkle'), 'Sparkle Arc A770', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sparkle Arc A770, 16 GB GDDR6, PCIe 4.0.', 300990.00, 4, NULL, 16, 'GDDR6', 'PCIe 4.0', 225, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(97, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'Sparkle'), 'Sparkle Arc B580', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica Sparkle Arc B580, 12 GB GDDR6, PCIe 4.0.', 281990.00, 5, NULL, 12, 'GDDR6', 'PCIe 4.0', 190, 600, 272);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(98, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Arc A750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Arc A750, 8 GB GDDR6, PCIe 4.0.', 232990.00, 6, NULL, 8, 'GDDR6', 'PCIe 4.0', 225, 600, 270);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(99, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Arc A770', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Arc A770, 16 GB GDDR6, PCIe 4.0.', 303990.00, 7, NULL, 16, 'GDDR6', 'PCIe 4.0', 225, 650, 280);
INSERT INTO core_tarjetagrafica (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, vram_gb, tipo_memoria, interfaz, consumo_referencia_watts, potencia_minima_fuente_watts, largo_mm) VALUES
(100, 'Tarjeta Gráfica', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Arc B580', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Tarjeta gráfica ASRock Arc B580, 12 GB GDDR6, PCIe 4.0.', 279990.00, 8, NULL, 12, 'GDDR6', 'PCIe 4.0', 190, 600, 272);

-- memoria_ram
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(1, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 40990.00, 5, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(2, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 41990.00, 6, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(3, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 42990.00, 7, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(4, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 43990.00, 8, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(5, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 39990.00, 9, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(6, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 40990.00, 10, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(7, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 41990.00, 11, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(8, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 16GB (2x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 42990.00, 12, NULL, 16, 'DDR4', 3200, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(9, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 43990.00, 13, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(10, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 39990.00, 14, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(11, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 40990.00, 15, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(12, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 41990.00, 4, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(13, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 42990.00, 5, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(14, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 43990.00, 6, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(15, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 39990.00, 7, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(16, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 16GB (2x8) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 8 GB.', 40990.00, 8, NULL, 16, 'DDR4', 3600, 2, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(17, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 81990.00, 9, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(18, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 82990.00, 10, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(19, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 83990.00, 11, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(20, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 79990.00, 12, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(21, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 80990.00, 13, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(22, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 81990.00, 14, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(23, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 82990.00, 15, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(24, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 32GB (2x16) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 83990.00, 4, NULL, 32, 'DDR4', 3200, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(25, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 79990.00, 5, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(26, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 80990.00, 6, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(27, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 81990.00, 7, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(28, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 82990.00, 8, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(29, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 83990.00, 9, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(30, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 79990.00, 10, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(31, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 80990.00, 11, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(32, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 32GB (2x16) DDR4-3600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 2 módulo(s) de 16 GB.', 81990.00, 12, NULL, 32, 'DDR4', 3600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(33, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 82990.00, 13, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(34, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 83990.00, 14, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(35, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 79990.00, 15, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(36, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 80990.00, 4, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(37, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 81990.00, 5, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(38, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 82990.00, 6, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(39, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 83990.00, 7, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(40, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 16GB DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 1 módulo(s) de 16 GB.', 79990.00, 8, NULL, 16, 'DDR4', 3200, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(41, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance LPX 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 40990.00, 9, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(42, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Ripjaws V 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 41990.00, 10, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(43, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 42990.00, 11, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(44, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'HyperX'), 'HyperX Fury 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 43990.00, 12, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(45, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Ballistix 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 39990.00, 13, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(46, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Steel 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 40990.00, 14, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(47, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Spectrix D50 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 41990.00, 15, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(48, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Vulcan Z 32GB (4x8) DDR4-3200', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 DIMM. El producto trae 4 módulo(s) de 8 GB.', 42990.00, 4, NULL, 32, 'DDR4', 3200, 4, 8, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(49, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 103990.00, 5, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(50, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 99990.00, 6, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(51, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 100990.00, 7, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(52, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Lancer 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 101990.00, 8, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(53, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Delta 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 102990.00, 9, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(54, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Venom 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 103990.00, 10, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(55, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 32GB (2x16) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 99990.00, 11, NULL, 32, 'DDR5', 5600, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(56, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 100990.00, 12, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(57, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 101990.00, 13, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(58, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 102990.00, 14, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(59, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Lancer 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 103990.00, 15, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(60, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Delta 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 99990.00, 4, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(61, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Venom 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 100990.00, 5, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(62, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 32GB (2x16) DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 16 GB.', 101990.00, 6, NULL, 32, 'DDR5', 6000, 2, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(63, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 182990.00, 7, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(64, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 183990.00, 8, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(65, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 179990.00, 9, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(66, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Lancer 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 180990.00, 10, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(67, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Delta 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 181990.00, 11, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(68, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Venom 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 182990.00, 12, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(69, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 64GB (2x32) DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 183990.00, 13, NULL, 64, 'DDR5', 5600, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(70, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 179990.00, 14, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(71, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 180990.00, 15, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(72, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 181990.00, 4, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(73, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Lancer 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 182990.00, 5, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(74, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force Delta 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 183990.00, 6, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(75, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot Viper Venom 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 179990.00, 7, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(76, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 64GB (2x32) DDR5-6400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 2 módulo(s) de 32 GB.', 180990.00, 8, NULL, 64, 'DDR5', 6400, 2, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(77, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Impact 16GB DDR4-3200 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 SO-DIMM. El producto trae 1 módulo(s) de 16 GB.', 51990.00, 9, NULL, 16, 'DDR4', 3200, 1, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(78, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial DDR4 SODIMM 16GB DDR4-3200 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 SO-DIMM. El producto trae 1 módulo(s) de 16 GB.', 52990.00, 10, NULL, 16, 'DDR4', 3200, 1, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(79, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance SODIMM 16GB (2x8) DDR4-3200 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR4 SO-DIMM. El producto trae 2 módulo(s) de 8 GB.', 53990.00, 11, NULL, 16, 'DDR4', 3200, 2, 8, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(80, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Impact 16GB DDR5-4800 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 SO-DIMM. El producto trae 1 módulo(s) de 16 GB.', 49990.00, 12, NULL, 16, 'DDR5', 4800, 1, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(81, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial DDR5 SODIMM 16GB DDR5-5600 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 SO-DIMM. El producto trae 1 módulo(s) de 16 GB.', 50990.00, 13, NULL, 16, 'DDR5', 5600, 1, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(82, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance SODIMM 32GB (2x16) DDR5-5600 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 SO-DIMM. El producto trae 2 módulo(s) de 16 GB.', 51990.00, 14, NULL, 32, 'DDR5', 5600, 2, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(83, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG Lancer SODIMM 16GB DDR5-4800 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 SO-DIMM. El producto trae 1 módulo(s) de 16 GB.', 52990.00, 15, NULL, 16, 'DDR5', 4800, 1, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(84, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup T-Force SODIMM 32GB (2x16) DDR5-5600 SO-DIMM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 SO-DIMM. El producto trae 2 módulo(s) de 16 GB.', 53990.00, 4, NULL, 32, 'DDR5', 5600, 2, 16, 'SO-DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(85, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 16GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 69990.00, 5, NULL, 16, 'DDR5', 5600, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(86, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 16GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 70990.00, 6, NULL, 16, 'DDR5', 5600, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(87, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 16GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 71990.00, 7, NULL, 16, 'DDR5', 5600, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(88, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 16GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 72990.00, 8, NULL, 16, 'DDR5', 5600, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(89, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 32GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 133990.00, 9, NULL, 32, 'DDR5', 5600, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(90, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 32GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 129990.00, 10, NULL, 32, 'DDR5', 5600, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(91, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 130990.00, 11, NULL, 32, 'DDR5', 5600, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(92, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 32GB DDR5-5600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 131990.00, 12, NULL, 32, 'DDR5', 5600, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(93, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 16GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 72990.00, 13, NULL, 16, 'DDR5', 6000, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(94, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 16GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 73990.00, 14, NULL, 16, 'DDR5', 6000, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(95, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 16GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 69990.00, 15, NULL, 16, 'DDR5', 6000, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(96, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 16GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 16 GB.', 70990.00, 4, NULL, 16, 'DDR5', 6000, 1, 16, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(97, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Vengeance 32GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 131990.00, 5, NULL, 32, 'DDR5', 6000, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(98, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'G.Skill'), 'G.Skill Trident Z5 32GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 132990.00, 6, NULL, 32, 'DDR5', 6000, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(99, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Beast 32GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 133990.00, 7, NULL, 32, 'DDR5', 6000, 1, 32, 'DIMM');
INSERT INTO core_memoriaram (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, tipo_ddr, velocidad_mhz, modulos_por_producto, capacidad_modulo_gb, formato_ram) VALUES
(100, 'Memoria RAM', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial Pro 32GB DDR5-6000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Memoria DDR5 DIMM. El producto trae 1 módulo(s) de 32 GB.', 129990.00, 8, NULL, 32, 'DDR5', 6000, 1, 32, 'DIMM');

-- placa_madre
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(1, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING B550-PLUS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 120990.00, 5, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(2, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX B550-A GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 121990.00, 6, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(3, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME B550-P', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 122990.00, 7, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(4, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME B550M-A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B550, socket AM4 y RAM DDR4.', 103990.00, 8, NULL, 'AM4', 'B550', 'Micro-ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(5, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX B550-I GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B550, socket AM4 y RAM DDR4.', 99990.00, 9, NULL, 'AM4', 'B550', 'Mini-ITX', 2, 'DDR4', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(6, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG B550 TOMAHAWK WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 120990.00, 10, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(7, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG B550 CARBON WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 121990.00, 11, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(8, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO B550-P WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 122990.00, 12, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(9, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO B550M-B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B550, socket AM4 y RAM DDR4.', 103990.00, 13, NULL, 'AM4', 'B550', 'Micro-ATX', 2, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(10, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG B550I EDGE WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B550, socket AM4 y RAM DDR4.', 99990.00, 14, NULL, 'AM4', 'B550', 'Mini-ITX', 2, 'DDR4', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(11, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550 AORUS ELITE AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 120990.00, 15, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(12, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550 GAMING X AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 121990.00, 4, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(13, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550 AORUS MASTER', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 122990.00, 5, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(14, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550M DS3H', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B550, socket AM4 y RAM DDR4.', 103990.00, 6, NULL, 'AM4', 'B550', 'Micro-ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(15, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550I AORUS ULTRA', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B550, socket AM4 y RAM DDR4.', 99990.00, 7, NULL, 'AM4', 'B550', 'Mini-ITX', 2, 'DDR4', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(16, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550 Steel Legend WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 120990.00, 8, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(17, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550 Phantom Gaming 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 121990.00, 9, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(18, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550 Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 122990.00, 10, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(19, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550M Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B550, socket AM4 y RAM DDR4.', 103990.00, 11, NULL, 'AM4', 'B550', 'Micro-ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(20, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550I Lightning WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B550, socket AM4 y RAM DDR4.', 99990.00, 12, NULL, 'AM4', 'B550', 'Mini-ITX', 2, 'DDR4', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(21, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ProArt B550-CREATOR', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 120990.00, 13, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(22, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG B550 TOMAHAWK MAX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 121990.00, 14, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(23, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B550 AORUS PRO AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 122990.00, 15, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(24, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B550 Taichi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 123990.00, 4, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(25, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING B550-PLUS WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B550, socket AM4 y RAM DDR4.', 119990.00, 5, NULL, 'AM4', 'B550', 'ATX', 4, 'DDR4', 'DIMM', 128);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(26, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING B650-PLUS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 190990.00, 6, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(27, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX B650-A GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 191990.00, 7, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(28, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME B650-P', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 192990.00, 8, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(29, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME B650M-A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B650, socket AM5 y RAM DDR5.', 173990.00, 9, NULL, 'AM5', 'B650', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(30, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX B650-I GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B650, socket AM5 y RAM DDR5.', 169990.00, 10, NULL, 'AM5', 'B650', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(31, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG B650 TOMAHAWK WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 190990.00, 11, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(32, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG B650 CARBON WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 191990.00, 12, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(33, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO B650-P WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 192990.00, 13, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(34, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO B650M-B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B650, socket AM5 y RAM DDR5.', 173990.00, 14, NULL, 'AM5', 'B650', 'Micro-ATX', 2, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(35, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG B650I EDGE WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B650, socket AM5 y RAM DDR5.', 169990.00, 15, NULL, 'AM5', 'B650', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(36, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650 AORUS ELITE AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 190990.00, 4, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(37, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650 GAMING X AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 191990.00, 5, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(38, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650 AORUS MASTER', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 192990.00, 6, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(39, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650M DS3H', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B650, socket AM5 y RAM DDR5.', 173990.00, 7, NULL, 'AM5', 'B650', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(40, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650I AORUS ULTRA', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B650, socket AM5 y RAM DDR5.', 169990.00, 8, NULL, 'AM5', 'B650', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(41, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650 Steel Legend WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 190990.00, 9, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(42, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650 Phantom Gaming 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 191990.00, 10, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(43, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650 Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 192990.00, 11, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(44, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650M Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset B650, socket AM5 y RAM DDR5.', 173990.00, 12, NULL, 'AM5', 'B650', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(45, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650I Lightning WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset B650, socket AM5 y RAM DDR5.', 169990.00, 13, NULL, 'AM5', 'B650', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(46, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ProArt B650-CREATOR', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 190990.00, 14, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(47, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG B650 TOMAHAWK MAX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 191990.00, 15, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(48, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte B650 AORUS PRO AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 192990.00, 4, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(49, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock B650 Taichi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 193990.00, 5, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(50, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING B650-PLUS WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset B650, socket AM5 y RAM DDR5.', 189990.00, 6, NULL, 'AM5', 'B650', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(51, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING X670-PLUS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 290990.00, 7, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(52, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX X670-A GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 291990.00, 8, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(53, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME X670-P', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 292990.00, 9, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(54, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME X670M-A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset X670, socket AM5 y RAM DDR5.', 273990.00, 10, NULL, 'AM5', 'X670', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(55, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX X670-I GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset X670, socket AM5 y RAM DDR5.', 269990.00, 11, NULL, 'AM5', 'X670', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(56, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG X670 TOMAHAWK WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 290990.00, 12, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(57, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG X670 CARBON WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 291990.00, 13, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(58, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO X670-P WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 292990.00, 14, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(59, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO X670M-B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset X670, socket AM5 y RAM DDR5.', 273990.00, 15, NULL, 'AM5', 'X670', 'Micro-ATX', 2, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(60, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG X670I EDGE WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset X670, socket AM5 y RAM DDR5.', 269990.00, 4, NULL, 'AM5', 'X670', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(61, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670 AORUS ELITE AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 290990.00, 5, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(62, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670 GAMING X AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 291990.00, 6, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(63, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670 AORUS MASTER', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 292990.00, 7, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(64, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670M DS3H', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset X670, socket AM5 y RAM DDR5.', 273990.00, 8, NULL, 'AM5', 'X670', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(65, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670I AORUS ULTRA', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset X670, socket AM5 y RAM DDR5.', 269990.00, 9, NULL, 'AM5', 'X670', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(66, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670 Steel Legend WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 290990.00, 10, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(67, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670 Phantom Gaming 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 291990.00, 11, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(68, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670 Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 292990.00, 12, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(69, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670M Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset X670, socket AM5 y RAM DDR5.', 273990.00, 13, NULL, 'AM5', 'X670', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(70, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670I Lightning WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset X670, socket AM5 y RAM DDR5.', 269990.00, 14, NULL, 'AM5', 'X670', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(71, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ProArt X670-CREATOR', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 290990.00, 15, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(72, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG X670 TOMAHAWK MAX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 291990.00, 4, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(73, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte X670 AORUS PRO AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 292990.00, 5, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(74, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock X670 Taichi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 293990.00, 6, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(75, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING X670-PLUS WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset X670, socket AM5 y RAM DDR5.', 289990.00, 7, NULL, 'AM5', 'X670', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(76, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING Z790-PLUS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 250990.00, 8, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(77, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX Z790-A GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 251990.00, 9, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(78, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME Z790-P', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 252990.00, 10, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(79, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PRIME Z790M-A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 233990.00, 11, NULL, 'LGA1700', 'Z790', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(80, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG STRIX Z790-I GAMING', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset Z790, socket LGA1700 y RAM DDR5.', 229990.00, 12, NULL, 'LGA1700', 'Z790', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(81, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG Z790 TOMAHAWK WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 250990.00, 13, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(82, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG Z790 CARBON WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 251990.00, 14, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(83, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO Z790-P WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 252990.00, 15, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(84, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI PRO Z790M-B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 233990.00, 4, NULL, 'LGA1700', 'Z790', 'Micro-ATX', 2, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(85, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG Z790I EDGE WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset Z790, socket LGA1700 y RAM DDR5.', 229990.00, 5, NULL, 'LGA1700', 'Z790', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(86, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790 AORUS ELITE AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 250990.00, 6, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(87, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790 GAMING X AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 251990.00, 7, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(88, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790 AORUS MASTER', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 252990.00, 8, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(89, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790M DS3H', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 233990.00, 9, NULL, 'LGA1700', 'Z790', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(90, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790I AORUS ULTRA', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset Z790, socket LGA1700 y RAM DDR5.', 229990.00, 10, NULL, 'LGA1700', 'Z790', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(91, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790 Steel Legend WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 250990.00, 11, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(92, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790 Phantom Gaming 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 251990.00, 12, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(93, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790 Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 252990.00, 13, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(94, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790M Pro RS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Micro-ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 233990.00, 14, NULL, 'LGA1700', 'Z790', 'Micro-ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(95, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790I Lightning WiFi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa Mini-ITX con chipset Z790, socket LGA1700 y RAM DDR5.', 229990.00, 15, NULL, 'LGA1700', 'Z790', 'Mini-ITX', 2, 'DDR5', 'DIMM', 64);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(96, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ProArt Z790-CREATOR', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 250990.00, 4, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(97, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG Z790 TOMAHAWK MAX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 251990.00, 5, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(98, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte Z790 AORUS PRO AX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 252990.00, 6, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(99, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASRock'), 'ASRock Z790 Taichi', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 253990.00, 7, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);
INSERT INTO core_placamadre (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, socket_cpu, chipset, formato, ranuras_ram, tipo_ram_soportado, formato_ram_soportado, capacidad_maxima_ram_gb) VALUES
(100, 'Placa Madre', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF GAMING Z790-PLUS WIFI', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Placa ATX con chipset Z790, socket LGA1700 y RAM DDR5.', 249990.00, 8, NULL, 'LGA1700', 'Z790', 'ATX', 4, 'DDR5', 'DIMM', 192);

-- almacenamiento_ssd
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(1, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 990 PRO 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 130990.00, 5, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(2, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 990 PRO 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 171990.00, 6, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(3, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 990 PRO 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 252990.00, 7, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(4, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 980 250GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 53990.00, 8, NULL, 250, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(5, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 980 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 49990.00, 9, NULL, 500, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(6, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 980 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 50990.00, 10, NULL, 1000, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(7, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 970 EVO Plus 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 71990.00, 11, NULL, 500, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(8, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 970 EVO Plus 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 72990.00, 12, NULL, 1000, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(9, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 970 EVO Plus 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 113990.00, 13, NULL, 2000, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(10, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 870 EVO 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 59990.00, 14, NULL, 500, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(11, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 870 EVO 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 60990.00, 15, NULL, 1000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(12, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 870 EVO 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 101990.00, 4, NULL, 2000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(13, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 870 EVO 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 182990.00, 5, NULL, 4000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(14, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN850X 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 123990.00, 6, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(15, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN850X 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 159990.00, 7, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(16, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN850X 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 240990.00, 8, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(17, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SN580 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 56990.00, 9, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(18, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SN580 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 57990.00, 10, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(19, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SN580 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 98990.00, 11, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(20, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SA510 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 49990.00, 12, NULL, 500, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(21, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SA510 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 50990.00, 13, NULL, 1000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(22, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue SA510 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 91990.00, 14, NULL, 2000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(23, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P3 Plus 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 52990.00, 15, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(24, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P3 Plus 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 53990.00, 4, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(25, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P3 Plus 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 89990.00, 5, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(26, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P3 Plus 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 170990.00, 6, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(27, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial MX500 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 56990.00, 7, NULL, 500, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(28, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial MX500 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 57990.00, 8, NULL, 1000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(29, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial MX500 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 98990.00, 9, NULL, 2000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(30, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial MX500 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 174990.00, 10, NULL, 4000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(31, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV2 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 40990.00, 11, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(32, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV2 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 41990.00, 12, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(33, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV2 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 82990.00, 13, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(34, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston KC3000 512GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 83990.00, 14, NULL, 512, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(35, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston KC3000 1024GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 79990.00, 15, NULL, 1024, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(36, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston KC3000 2048GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 120990.00, 4, NULL, 2048, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(37, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston A400 240GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 26990.00, 5, NULL, 240, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(38, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston A400 480GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 27990.00, 6, NULL, 480, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(39, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston A400 960GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 28990.00, 7, NULL, 960, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(40, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 530 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 139990.00, 8, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(41, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 530 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 180990.00, 9, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(42, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 530 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 261990.00, 10, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(43, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA Legend 960 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 102990.00, 11, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(44, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA Legend 960 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 143990.00, 12, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(45, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA Legend 960 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 219990.00, 13, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(46, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Ultra 3D 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 55990.00, 14, NULL, 500, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(47, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Ultra 3D 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 56990.00, 15, NULL, 1000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(48, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Ultra 3D 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 97990.00, 4, NULL, 2000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(49, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Ultra 3D 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 178990.00, 5, NULL, 4000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(50, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 PRO 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 124990.00, 6, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(51, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 PRO 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 165990.00, 7, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(52, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 PRO 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 246990.00, 8, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(53, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot P400 Lite 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 47990.00, 9, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(54, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot P400 Lite 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 48990.00, 10, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(55, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Patriot'), 'Patriot P400 Lite 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 84990.00, 11, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(56, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup MP44 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 50990.00, 12, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(57, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup MP44 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 51990.00, 13, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(58, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'TeamGroup'), 'TeamGroup MP44 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 92990.00, 14, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(59, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY CS3140 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 113990.00, 15, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(60, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY CS3140 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 149990.00, 4, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(61, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'PNY'), 'PNY CS3140 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 230990.00, 5, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(62, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte AORUS Gen4 7300 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 121990.00, 6, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(63, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte AORUS Gen4 7300 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 162990.00, 7, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(64, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Spatium M480 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 118990.00, 8, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(65, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI Spatium M480 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 154990.00, 9, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(66, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA SU650 256GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 30990.00, 10, NULL, 256, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(67, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA SU650 512GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 31990.00, 11, NULL, 512, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(68, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA SU650 1024GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 32990.00, 12, NULL, 1024, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(69, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV3 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 48990.00, 13, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(70, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV3 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 44990.00, 14, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(71, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV3 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 85990.00, 15, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(72, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston NV3 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 166990.00, 4, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(73, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 860 EVO 250GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 47990.00, 5, NULL, 250, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(74, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 860 EVO 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 48990.00, 6, NULL, 500, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(75, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 860 EVO 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 44990.00, 7, NULL, 1000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(76, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 860 EVO 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 85990.00, 8, NULL, 2000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(77, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 860 EVO 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD SATA III en formato 2.5".', 166990.00, 9, NULL, 4000, 'SATA III', '2.5"');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(78, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 990 EVO 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 112990.00, 10, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(79, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Samsung'), 'Samsung 990 EVO 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 153990.00, 11, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(80, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN770 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 79990.00, 12, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(81, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN770 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 80990.00, 13, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(82, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black SN770 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 121990.00, 14, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(83, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P5 Plus 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 92990.00, 15, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(84, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P5 Plus 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 93990.00, 4, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(85, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Crucial'), 'Crucial P5 Plus 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 129990.00, 5, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(86, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Renegade 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 90990.00, 6, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(87, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Renegade 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 91990.00, 7, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(88, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Renegade 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 132990.00, 8, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(89, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Kingston'), 'Kingston Fury Renegade 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 213990.00, 9, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(90, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 CORE 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 99990.00, 10, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(91, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 CORE 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 140990.00, 11, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(92, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair MP600 CORE 4000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 221990.00, 12, NULL, 4000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(93, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 520 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 102990.00, 13, NULL, 500, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(94, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 520 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 103990.00, 14, NULL, 1000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(95, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate FireCuda 520 2000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 4.0 en formato M.2 2280.', 139990.00, 15, NULL, 2000, 'NVMe PCIe 4.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(96, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Extreme 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 70990.00, 4, NULL, 500, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(97, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'SanDisk'), 'SanDisk Extreme 1000GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 71990.00, 5, NULL, 1000, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(98, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG SX8200 Pro 512GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 82990.00, 6, NULL, 512, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(99, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG SX8200 Pro 1024GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 83990.00, 7, NULL, 1024, 'NVMe PCIe 3.0', 'M.2 2280');
INSERT INTO core_almacenamientossd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, interfaz, formato) VALUES
(100, 'SSD', (SELECT id FROM core_proveedor WHERE nombre = 'ADATA'), 'ADATA XPG SX8200 Pro 2048GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. SSD NVMe PCIe 3.0 en formato M.2 2280.', 119990.00, 8, NULL, 2048, 'NVMe PCIe 3.0', 'M.2 2280');

-- almacenamiento_hdd
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(1, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 50990.00, 5, NULL, 500, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(2, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 56990.00, 6, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(3, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 62990.00, 7, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(4, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 73990.00, 8, NULL, 4000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(5, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 79990.00, 9, NULL, 6000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(6, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 90990.00, 10, NULL, 8000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(7, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 126990.00, 11, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(8, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 132990.00, 12, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(9, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 143990.00, 13, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(10, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 149990.00, 14, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(11, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 160990.00, 15, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(12, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Barracuda Pro 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 171990.00, 4, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(13, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 97990.00, 5, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(14, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 103990.00, 6, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(15, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 3TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 104990.00, 7, NULL, 3000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(16, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 110990.00, 8, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(17, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 121990.00, 9, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(18, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 132990.00, 10, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(19, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 143990.00, 11, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(20, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 149990.00, 12, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(21, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 160990.00, 13, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(22, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 171990.00, 14, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(23, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 182990.00, 15, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(24, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 193990.00, 4, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(25, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 199990.00, 5, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(26, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 210990.00, 6, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(27, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 16TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 231990.00, 7, NULL, 16000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(28, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate IronWolf Pro 18TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 242990.00, 8, NULL, 18000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(29, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 88990.00, 9, NULL, 1000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(30, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 89990.00, 10, NULL, 2000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(31, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 3TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 95990.00, 11, NULL, 3000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(32, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 101990.00, 12, NULL, 4000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(33, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 112990.00, 13, NULL, 6000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(34, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 123990.00, 14, NULL, 8000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(35, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk AI 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 219990.00, 15, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(36, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk AI 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 230990.00, 4, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(37, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk AI 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 241990.00, 5, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(38, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate SkyHawk AI 16TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 262990.00, 6, NULL, 16000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(39, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos 7E8 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 108990.00, 7, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(40, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos 7E8 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 109990.00, 8, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(41, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos 7E8 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 120990.00, 9, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(42, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos 7E8 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 131990.00, 10, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(43, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos 7E8 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 142990.00, 11, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(44, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos X16 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 303990.00, 12, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(45, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos X16 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 309990.00, 13, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(46, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos X16 14TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 320990.00, 14, NULL, 14000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(47, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Seagate'), 'Seagate Exos X16 16TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 331990.00, 15, NULL, 16000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(48, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 52990.00, 4, NULL, 500, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(49, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 58990.00, 5, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(50, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 59990.00, 6, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(51, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 3TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 65990.00, 7, NULL, 3000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(52, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 71990.00, 8, NULL, 4000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(53, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Blue 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 82990.00, 9, NULL, 6000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(54, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 93990.00, 10, NULL, 500, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(55, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 94990.00, 11, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(56, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 100990.00, 12, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(57, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 111990.00, 13, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(58, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 122990.00, 14, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(59, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 133990.00, 15, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(60, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Black 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 139990.00, 4, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(61, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 105990.00, 5, NULL, 1000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(62, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 111990.00, 6, NULL, 2000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(63, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 3TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 117990.00, 7, NULL, 3000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(64, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 123990.00, 8, NULL, 4000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(65, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 129990.00, 9, NULL, 6000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(66, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 140990.00, 10, NULL, 8000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(67, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 151990.00, 11, NULL, 10000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(68, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Plus 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 256 MB de caché.', 162990.00, 12, NULL, 12000, 5400, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(69, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 173990.00, 13, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(70, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 179990.00, 14, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(71, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 190990.00, 15, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(72, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 201990.00, 4, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(73, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 212990.00, 5, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(74, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Red Pro 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 223990.00, 6, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(75, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 94990.00, 7, NULL, 1000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(76, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 100990.00, 8, NULL, 2000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(77, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 111990.00, 9, NULL, 4000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(78, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 122990.00, 10, NULL, 6000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(79, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 133990.00, 11, NULL, 8000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(80, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Purple 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 5400 RPM con 64 MB de caché.', 139990.00, 12, NULL, 10000, 5400, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(81, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 155990.00, 13, NULL, 1000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(82, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 161990.00, 14, NULL, 2000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(83, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 172990.00, 15, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(84, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 183990.00, 4, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(85, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 189990.00, 5, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(86, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 200990.00, 6, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(87, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Western Digital'), 'Western Digital Gold 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 211990.00, 7, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(88, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 500GB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 52990.00, 8, NULL, 500, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(89, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 1TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 58990.00, 9, NULL, 1000, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(90, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 2TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 59990.00, 10, NULL, 2000, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(91, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 3TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 65990.00, 11, NULL, 3000, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(92, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 71990.00, 12, NULL, 4000, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(93, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba P300 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 64 MB de caché.', 82990.00, 13, NULL, 6000, 7200, 64);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(94, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 4TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 153990.00, 14, NULL, 4000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(95, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 6TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 159990.00, 15, NULL, 6000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(96, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 8TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 170990.00, 4, NULL, 8000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(97, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 10TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 181990.00, 5, NULL, 10000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(98, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 12TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 192990.00, 6, NULL, 12000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(99, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 14TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 203990.00, 7, NULL, 14000, 7200, 256);
INSERT INTO core_almacenamientohdd (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, capacidad_gb, velocidad_rpm, cache_mb) VALUES
(100, 'Disco Duro HDD', (SELECT id FROM core_proveedor WHERE nombre = 'Toshiba'), 'Toshiba X300 16TB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Disco mecánico 7200 RPM con 256 MB de caché.', 209990.00, 8, NULL, 16000, 7200, 256);

-- gabinete
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(1, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 4000D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 90990.00, 5, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(2, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 4000D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 81990.00, 6, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(3, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 5000D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 152990.00, 7, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(4, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 5000D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 143990.00, 8, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(5, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 7000D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 450 mm.', 219990.00, 9, NULL, 'ATX', TRUE, 'Acero', 450);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(6, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 275R Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 370 mm.', 70990.00, 10, NULL, 'ATX', TRUE, 'Acero', 370);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(7, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 220T RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 300 mm.', 91990.00, 11, NULL, 'ATX', TRUE, 'Acero', 300);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(8, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 2000D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 365 mm.', 132990.00, 12, NULL, 'Mini-ITX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(9, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 2500D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 400 mm.', 123990.00, 13, NULL, 'Micro-ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(10, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H5 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 365 mm.', 99990.00, 14, NULL, 'ATX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(11, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H5 Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 365 mm.', 150990.00, 15, NULL, 'ATX', TRUE, 'Vidrio Templado', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(12, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H6 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 365 mm.', 131990.00, 4, NULL, 'ATX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(13, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H7 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 142990.00, 5, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(14, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H7 Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 183990.00, 6, NULL, 'ATX', TRUE, 'Vidrio Templado', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(15, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H9 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 435 mm.', 169990.00, 7, NULL, 'ATX', TRUE, 'Acero', 435);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(16, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H9 Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 435 mm.', 230990.00, 8, NULL, 'ATX', TRUE, 'Vidrio Templado', 435);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(17, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H510', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 381 mm.', 91990.00, 9, NULL, 'ATX', TRUE, 'Acero', 381);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(18, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H510 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 381 mm.', 102990.00, 10, NULL, 'ATX', TRUE, 'Acero', 381);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(19, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H210', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 325 mm.', 93990.00, 11, NULL, 'Mini-ITX', TRUE, 'Acero', 325);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(20, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Lancool 215', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 370 mm.', 89990.00, 12, NULL, 'ATX', TRUE, 'Acero', 370);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(21, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Lancool 216', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 392 mm.', 110990.00, 13, NULL, 'ATX', TRUE, 'Acero', 392);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(22, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Lancool II Mesh', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 384 mm.', 121990.00, 14, NULL, 'ATX', TRUE, 'Acero', 384);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(23, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li O11 Dynamic', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 420 mm.', 152990.00, 15, NULL, 'ATX', FALSE, 'Vidrio Templado', 420);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(24, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li O11 Dynamic EVO', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 442 mm.', 183990.00, 4, NULL, 'ATX', FALSE, 'Vidrio Templado', 442);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(25, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li O11 Air Mini', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 362 mm.', 119990.00, 5, NULL, 'Micro-ATX', TRUE, 'Acero', 362);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(26, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li A4-H2O', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 322 mm.', 150990.00, 6, NULL, 'Mini-ITX', FALSE, 'Aluminio', 322);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(27, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Meshify 2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 440 mm.', 151990.00, 7, NULL, 'ATX', TRUE, 'Acero', 440);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(28, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Meshify 2 Compact', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 132990.00, 8, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(29, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Meshify C', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 315 mm.', 103990.00, 9, NULL, 'ATX', TRUE, 'Acero', 315);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(30, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Pop Air', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 380 mm.', 89990.00, 10, NULL, 'ATX', TRUE, 'Acero', 380);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(31, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Pop Mini Air', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 365 mm.', 80990.00, 11, NULL, 'Micro-ATX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(32, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design North', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 355 mm.', 151990.00, 12, NULL, 'ATX', TRUE, 'Acero', 355);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(33, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Torrent', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 423 mm.', 202990.00, 13, NULL, 'ATX', TRUE, 'Acero', 423);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(34, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Define 7', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 440 mm.', 173990.00, 14, NULL, 'ATX', FALSE, 'Acero', 440);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(35, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Ridge', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 335 mm.', 129990.00, 15, NULL, 'Mini-ITX', TRUE, 'Aluminio', 335);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(36, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Eclipse G360A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 90990.00, 4, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(37, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Eclipse G500A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 435 mm.', 131990.00, 5, NULL, 'ATX', TRUE, 'Acero', 435);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(38, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Eclipse P400A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 420 mm.', 102990.00, 6, NULL, 'ATX', TRUE, 'Acero', 420);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(39, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Eclipse P500A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 435 mm.', 143990.00, 7, NULL, 'ATX', TRUE, 'Acero', 435);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(40, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Evolv Shift XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 335 mm.', 149990.00, 8, NULL, 'Mini-ITX', TRUE, 'Acero', 335);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(41, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master TD500 Mesh', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 410 mm.', 110990.00, 9, NULL, 'ATX', TRUE, 'Acero', 410);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(42, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master NR200P', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 330 mm.', 101990.00, 10, NULL, 'Mini-ITX', TRUE, 'Acero', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(43, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master NR600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 410 mm.', 72990.00, 11, NULL, 'ATX', FALSE, 'Acero', 410);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(44, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MB311L', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 340 mm.', 53990.00, 12, NULL, 'Micro-ATX', TRUE, 'Acero', 340);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(45, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterBox Q300L', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 360 mm.', 49990.00, 13, NULL, 'Micro-ATX', FALSE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(46, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master HAF 500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 410 mm.', 130990.00, 14, NULL, 'ATX', TRUE, 'Acero', 410);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(47, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Base 500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 369 mm.', 101990.00, 15, NULL, 'ATX', TRUE, 'Acero', 369);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(48, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Base 500DX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 369 mm.', 122990.00, 4, NULL, 'ATX', TRUE, 'Vidrio Templado', 369);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(49, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Shadow Base 800', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 430 mm.', 153990.00, 5, NULL, 'ATX', TRUE, 'Acero', 430);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(50, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Base 600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 425 mm.', 109990.00, 6, NULL, 'ATX', TRUE, 'Acero', 425);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(51, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Versa H18', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 350 mm.', 50990.00, 7, NULL, 'Micro-ATX', FALSE, 'Acero', 350);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(52, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake S100 TG', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 330 mm.', 61990.00, 8, NULL, 'Micro-ATX', TRUE, 'Vidrio Templado', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(53, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake View 170 TG', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 340 mm.', 72990.00, 9, NULL, 'Micro-ATX', TRUE, 'Vidrio Templado', 340);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(54, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Core P3', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 450 mm.', 153990.00, 10, NULL, 'ATX', FALSE, 'Acero', 450);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(55, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Versa H26', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 380 mm.', 69990.00, 11, NULL, 'ATX', TRUE, 'Acero', 380);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(56, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone FARA R1', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 365 mm.', 70990.00, 12, NULL, 'ATX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(57, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone FARA R1 Pro', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 365 mm.', 81990.00, 13, NULL, 'ATX', TRUE, 'Acero', 365);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(58, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone PS15', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 350 mm.', 52990.00, 14, NULL, 'Micro-ATX', TRUE, 'Acero', 350);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(59, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone RL08', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 330 mm.', 133990.00, 15, NULL, 'Mini-ITX', TRUE, 'Aluminio', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(60, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone SETA H1', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 392 mm.', 119990.00, 4, NULL, 'ATX', TRUE, 'Acero', 392);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(61, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AIR 100', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 330 mm.', 60990.00, 5, NULL, 'Micro-ATX', TRUE, 'Acero', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(62, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AIR 100 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 330 mm.', 71990.00, 6, NULL, 'Micro-ATX', TRUE, 'Acero', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(63, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AIR 903 Max', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 92990.00, 7, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(64, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AIR 903 Base', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 83990.00, 8, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(65, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech SKY TWO', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 109990.00, 9, NULL, 'ATX', TRUE, 'Vidrio Templado', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(66, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NX410', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 60990.00, 10, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(67, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NX416L', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 71990.00, 11, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(68, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec DF700 Flux', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 405 mm.', 102990.00, 12, NULL, 'ATX', TRUE, 'Acero', 405);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(69, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec P10C', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 415 mm.', 113990.00, 13, NULL, 'ATX', FALSE, 'Acero', 415);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(70, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NX200M', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 330 mm.', 49990.00, 14, NULL, 'Micro-ATX', TRUE, 'Acero', 330);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(71, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Lancool 205 Mesh', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 350 mm.', 80990.00, 15, NULL, 'ATX', TRUE, 'Acero', 350);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(72, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Eclipse G300A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 355 mm.', 71990.00, 4, NULL, 'Micro-ATX', TRUE, 'Acero', 355);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(73, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Focus 2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 405 mm.', 82990.00, 5, NULL, 'ATX', TRUE, 'Acero', 405);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(74, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H1', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 305 mm.', 203990.00, 6, NULL, 'Mini-ITX', TRUE, 'Acero', 305);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(75, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 3000D Airflow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 360 mm.', 79990.00, 7, NULL, 'ATX', TRUE, 'Acero', 360);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(76, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair 3500X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 410 mm.', 120990.00, 8, NULL, 'ATX', TRUE, 'Vidrio Templado', 410);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(77, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG Forge 112R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 340 mm.', 71990.00, 9, NULL, 'ATX', TRUE, 'Acero', 340);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(78, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG Forge 321R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 390 mm.', 92990.00, 10, NULL, 'ATX', TRUE, 'Acero', 390);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(79, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG Gungnir 110R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 340 mm.', 103990.00, 11, NULL, 'ATX', TRUE, 'Acero', 340);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(80, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG Forge M100R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 300 mm.', 59990.00, 12, NULL, 'Micro-ATX', TRUE, 'Acero', 300);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(81, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF Gaming GT502', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 170990.00, 13, NULL, 'ATX', TRUE, 'Acero', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(82, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS A21', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 380 mm.', 71990.00, 14, NULL, 'Micro-ATX', TRUE, 'Acero', 380);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(83, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS PA602', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 450 mm.', 202990.00, 15, NULL, 'ATX', TRUE, 'Acero', 450);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(84, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterBox 520', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 410 mm.', 103990.00, 4, NULL, 'ATX', TRUE, 'Acero', 410);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(85, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Base 500 FX', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 369 mm.', 149990.00, 5, NULL, 'ATX', TRUE, 'Vidrio Templado', 369);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(86, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake View 200 TG', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 390 mm.', 90990.00, 6, NULL, 'ATX', TRUE, 'Vidrio Templado', 390);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(87, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone FARA B1', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 370 mm.', 71990.00, 7, NULL, 'ATX', TRUE, 'Acero', 370);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(88, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech XR', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 390 mm.', 102990.00, 8, NULL, 'ATX', TRUE, 'Vidrio Templado', 390);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(89, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec C8', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 395 mm.', 133990.00, 9, NULL, 'ATX', TRUE, 'Vidrio Templado', 395);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(90, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Lancool 207', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 375 mm.', 99990.00, 10, NULL, 'ATX', TRUE, 'Acero', 375);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(91, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Pop XL Air', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 430 mm.', 120990.00, 11, NULL, 'ATX', TRUE, 'Acero', 430);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(92, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks XT View', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 415 mm.', 121990.00, 12, NULL, 'ATX', TRUE, 'Vidrio Templado', 415);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(93, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT H3 Flow', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 364 mm.', 82990.00, 13, NULL, 'Micro-ATX', TRUE, 'Acero', 364);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(94, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Frame 4000D', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 397 mm.', 113990.00, 14, NULL, 'ATX', TRUE, 'Acero', 397);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(95, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte C301 Glass', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 400 mm.', 99990.00, 15, NULL, 'ATX', TRUE, 'Vidrio Templado', 400);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(96, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool CC560', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 370 mm.', 60990.00, 4, NULL, 'ATX', TRUE, 'Acero', 370);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(97, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool CH510', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 380 mm.', 71990.00, 5, NULL, 'ATX', TRUE, 'Acero', 380);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(98, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool CK560', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete ATX. Admite GPU de hasta 380 mm.', 82990.00, 6, NULL, 'ATX', TRUE, 'Acero', 380);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(99, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool CH360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Micro-ATX. Admite GPU de hasta 320 mm.', 63990.00, 7, NULL, 'Micro-ATX', TRUE, 'Acero', 320);
INSERT INTO core_gabinete (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, formato_soporte, ventiladores_incluidos, material, largo_max_gpu_mm) VALUES
(100, 'Gabinete', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool CH160', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Gabinete Mini-ITX. Admite GPU de hasta 305 mm.', 69990.00, 8, NULL, 'Mini-ITX', TRUE, 'Acero', 305);

-- fuente_de_poder
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(1, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RM650x', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 104990.00, 5, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(2, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RM750x', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 109990.00, 6, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(3, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RM850x', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 114990.00, 7, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(4, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RM1000x', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 121990.00, 8, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(5, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair CX550', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Bronze.', 59990.00, 9, NULL, 550, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(6, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair CX650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Bronze.', 64990.00, 10, NULL, 650, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(7, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair CX750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 69990.00, 11, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(8, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus GX-650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 116990.00, 12, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(9, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus GX-750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 121990.00, 13, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(10, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus GX-850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 121990.00, 14, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(11, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus GX-1000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 128990.00, 15, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(12, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Prime TX-850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Titanium.', 263990.00, 4, NULL, 850, '80+ Titanium', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(13, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Prime TX-1000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Titanium.', 270990.00, 5, NULL, 1000, '80+ Titanium', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(14, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Power 12 M 650W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 117990.00, 6, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(15, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Power 12 M 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 117990.00, 7, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(16, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Power 12 M 850W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 122990.00, 8, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(17, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! System Power 10 550W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Bronze.', 61990.00, 9, NULL, 550, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(18, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! System Power 10 650W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Bronze.', 66990.00, 10, NULL, 650, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(19, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! System Power 10 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 71990.00, 11, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(20, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 650 G6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 123990.00, 12, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(21, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 750 G6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 128990.00, 13, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(22, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 850 G6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 133990.00, 14, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(23, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 1000 G6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 140990.00, 15, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(24, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Bronze 550', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Bronze.', 58990.00, 4, NULL, 550, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(25, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Bronze 650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Bronze.', 58990.00, 5, NULL, 650, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(26, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Bronze 750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 63990.00, 6, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(27, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master V750 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 139990.00, 7, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(28, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master V850 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 144990.00, 8, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(29, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF1 650W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 107990.00, 9, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(30, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF1 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 107990.00, 10, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(31, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF1 850W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 112990.00, 11, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(32, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro G 650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 105990.00, 12, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(33, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro G 750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 110990.00, 13, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(34, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro G 850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 115990.00, 14, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(35, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix 750G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 157990.00, 15, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(36, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix 850G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 162990.00, 4, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(37, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix 1000G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 169990.00, 5, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(38, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG A750G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 140990.00, 6, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(39, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG A850G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 145990.00, 7, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(40, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG A1000G', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 147990.00, 8, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(41, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT C750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 128990.00, 9, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(42, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT C850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 133990.00, 10, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(43, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone DA650 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 116990.00, 11, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(44, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone DA750 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 121990.00, 12, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(45, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone DA850 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 121990.00, 13, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(46, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NE550 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Gold.', 90990.00, 14, NULL, 550, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(47, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NE650 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 95990.00, 15, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(48, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NE750 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 100990.00, 4, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(49, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NE850 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 105990.00, 5, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(50, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec NE1000 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 107990.00, 6, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(51, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Smart 500W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 500 W, certificación 80+ White.', 38990.00, 7, NULL, 500, '80+ White', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(52, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Smart 600W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 600 W, certificación 80+ White.', 43990.00, 8, NULL, 600, '80+ White', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(53, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Smart 700W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 700 W, certificación 80+ White.', 48990.00, 9, NULL, 700, '80+ White', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(54, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair HX750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 181990.00, 10, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(55, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair HX850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 181990.00, 11, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(56, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair HX1000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Platinum.', 188990.00, 12, NULL, 1000, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(57, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus PX-750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 169990.00, 13, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(58, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Focus PX-850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 174990.00, 14, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(59, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro PTM 650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Platinum.', 147990.00, 15, NULL, 650, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(60, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro PTM 750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 147990.00, 4, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(61, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'FSP'), 'FSP Hydro PTM 850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 152990.00, 5, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(62, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Power 13 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Titanium.', 239990.00, 6, NULL, 750, '80+ Titanium', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(63, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Power 13 850W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Titanium.', 244990.00, 7, NULL, 850, '80+ Titanium', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(64, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Power 13 1000W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Titanium.', 251990.00, 8, NULL, 1000, '80+ Titanium', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(65, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 750 P6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 167990.00, 9, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(66, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA SuperNOVA 850 P6', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 172990.00, 10, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(67, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RMe650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 95990.00, 11, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(68, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RMe750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 100990.00, 12, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(69, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RMe850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 105990.00, 13, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(70, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RMe1000', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 107990.00, 14, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(71, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair SF750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 158990.00, 15, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(72, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair SF850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 163990.00, 4, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(73, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Core GM-500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 500 W, certificación 80+ Gold.', 70990.00, 5, NULL, 500, '80+ Gold', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(74, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Core GM-650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 77990.00, 6, NULL, 650, '80+ Gold', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(75, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Seasonic'), 'Seasonic Core GM-750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 77990.00, 7, NULL, 750, '80+ Gold', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(76, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Straight Power 12 650W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Platinum.', 164990.00, 8, NULL, 650, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(77, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Straight Power 12 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Platinum.', 169990.00, 9, NULL, 750, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(78, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Straight Power 12 850W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Platinum.', 174990.00, 10, NULL, 850, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(79, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Straight Power 12 1000W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Platinum.', 181990.00, 11, NULL, 1000, '80+ Platinum', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(80, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA BQ 500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 500 W, certificación 80+ Bronze.', 47990.00, 12, NULL, 500, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(81, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA BQ 600', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 600 W, certificación 80+ Bronze.', 52990.00, 13, NULL, 600, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(82, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA BQ 700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 700 W, certificación 80+ Bronze.', 57990.00, 14, NULL, 700, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(83, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'EVGA'), 'EVGA BQ 750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 60990.00, 15, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(84, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Gold 550', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Gold.', 83990.00, 4, NULL, 550, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(85, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Gold 650', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 83990.00, 5, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(86, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Gold 750', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 88990.00, 6, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(87, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MWE Gold 850', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 93990.00, 7, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(88, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF3 750W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Gold.', 140990.00, 8, NULL, 750, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(89, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF3 850W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 850 W, certificación 80+ Gold.', 145990.00, 9, NULL, 850, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(90, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF3 1000W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 147990.00, 10, NULL, 1000, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(91, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughpower GF3 1200W', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1200 W, certificación 80+ Gold.', 156990.00, 11, NULL, 1200, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(92, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG A550BN', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Bronze.', 51990.00, 12, NULL, 550, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(93, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG A650BN', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Bronze.', 56990.00, 13, NULL, 650, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(94, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG A750BN', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 61990.00, 14, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(95, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF Gaming 550B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Bronze.', 69990.00, 15, NULL, 550, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(96, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF Gaming 650B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Bronze.', 74990.00, 4, NULL, 650, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(97, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF Gaming 750B', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 750 W, certificación 80+ Bronze.', 79990.00, 5, NULL, 750, '80+ Bronze', FALSE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(98, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT C550 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 550 W, certificación 80+ Gold.', 102990.00, 6, NULL, 550, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(99, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT C650 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 650 W, certificación 80+ Gold.', 107990.00, 7, NULL, 650, '80+ Gold', TRUE);
INSERT INTO core_fuentedepoder (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, potencia_watts, certificacion, modular) VALUES
(100, 'Fuente de Poder', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT C1000 Gold', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Fuente 1000 W, certificación 80+ Gold.', 117990.00, 8, NULL, 1000, '80+ Gold', TRUE);

-- refrigeracion
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(1, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-D15', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 90990.00, 5, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(2, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-D15S', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 81990.00, 6, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(3, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-U12A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 102990.00, 7, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(4, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-U12S', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 73990.00, 8, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(5, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-U9S', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 59990.00, 9, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(6, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-L9a-AM4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5.', 50990.00, 10, NULL, 'Aire', 'AM4, AM5', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(7, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-L9i-1700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con LGA1700, LGA1200.', 51990.00, 11, NULL, 'Aire', 'LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(8, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-L12S', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 72990.00, 12, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(9, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-D12L', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 83990.00, 13, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(10, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Freezer 36', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 39990.00, 14, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(11, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Freezer 34 eSports', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 35990.00, 15, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(12, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Freezer 34 eSports Duo', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 46990.00, 4, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(13, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Rock 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 72990.00, 5, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(14, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Rock Pro 4', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 93990.00, 6, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(15, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Rock 2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 39990.00, 7, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(16, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Dark Rock Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 100990.00, 8, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(17, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Hyper 212 Black', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 41990.00, 9, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(18, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Hyper 212 Halo', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 52990.00, 10, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(19, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MA624 Stealth', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 83990.00, 11, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(20, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool AK400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 29990.00, 12, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(21, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool AK620', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 60990.00, 13, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(22, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool AG400', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 26990.00, 14, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(23, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool AG620', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 52990.00, 15, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(24, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING SE-224-XTS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 28990.00, 4, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(25, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING SE-226-XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 34990.00, 5, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(26, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING IS-55', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700.', 40990.00, 6, NULL, 'Aire', 'AM4, AM5, LGA1700', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(27, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Fuma 2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 61990.00, 7, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(28, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Fuma 3', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 62990.00, 8, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(29, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Mugen 5', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 53990.00, 9, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(30, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake UX200 SE', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 29990.00, 10, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(31, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake TOUGHAIR 510', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 60990.00, 11, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(32, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Freezer 7 X', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con LGA1700, LGA1200.', 21990.00, 12, NULL, 'Aire', 'LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(33, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Hyper 212 EVO V2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 37990.00, 13, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(34, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NH-U14S', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 83990.00, 14, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(35, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Rock Slim 2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 29990.00, 15, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(36, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool AK500', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 45990.00, 4, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(37, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING SE-214-XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 24990.00, 5, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(38, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Big Shuriken 3', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 52990.00, 6, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(39, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Alpine 23', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5.', 18990.00, 7, NULL, 'Aire', 'AM4, AM5', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(40, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Alpine 17', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con LGA1700.', 14990.00, 8, NULL, 'Aire', 'LGA1700', NULL);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(41, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE H100i RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 130990.00, 9, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(42, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE H115i RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 151990.00, 10, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(43, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE H150i RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 172990.00, 11, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(44, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE LINK H100i', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 163990.00, 12, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(45, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE LINK H150i', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 199990.00, 13, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(46, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 130990.00, 14, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(47, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken 280', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 151990.00, 15, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(48, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 182990.00, 4, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(49, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken Elite 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 173990.00, 5, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(50, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken Elite 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 219990.00, 6, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(51, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer II 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 90990.00, 7, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(52, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer II 280', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 101990.00, 8, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(53, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer II 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 112990.00, 9, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(54, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer III 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 103990.00, 10, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(55, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer III 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 119990.00, 11, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(56, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer III 280', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 110990.00, 12, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(57, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool LS520', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 91990.00, 13, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(58, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool LS720', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 122990.00, 14, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(59, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool LT720', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 133990.00, 15, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(60, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Loop 2 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 109990.00, 4, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(61, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Loop 2 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 140990.00, 5, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(62, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Silent Loop 2 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 131990.00, 6, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(63, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Silent Loop 2 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 162990.00, 7, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(64, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterLiquid 240L Core', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 83990.00, 8, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(65, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterLiquid 360L Core', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 99990.00, 9, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(66, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake TH240 V2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 90990.00, 10, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(67, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake TH360 V2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 121990.00, 11, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(68, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING ZoomFlow 240 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 72990.00, 12, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(69, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING Dashflow 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 93990.00, 13, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(70, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Ryujin III 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 249990.00, 14, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(71, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Ryujin III 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 300990.00, 15, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(72, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG CoreLiquid 240R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 101990.00, 4, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(73, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAG CoreLiquid 360R', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 132990.00, 5, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(74, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Lumen S24', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 103990.00, 6, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(75, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Lumen S36', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 119990.00, 7, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(76, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Galahad II Trinity 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 130990.00, 8, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(77, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li Galahad II Trinity 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 161990.00, 9, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(78, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Glacier One 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 112990.00, 10, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(79, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks Glacier One 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 143990.00, 11, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(80, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone IceGem 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 89990.00, 12, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(81, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone IceGem 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 120990.00, 13, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(82, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec Symphony 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 81990.00, 14, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(83, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec Symphony 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 102990.00, 15, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(84, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech HyperFlow 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 83990.00, 4, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(85, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech HyperFlow 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 99990.00, 5, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(86, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool LS320', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 80990.00, 6, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(87, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterLiquid 240 Atmos', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 121990.00, 7, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(88, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Nautilus 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 102990.00, 8, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(89, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair Nautilus 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 133990.00, 9, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(90, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT Kraken 240 RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 149990.00, 10, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(91, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic Liquid Freezer III 420', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 420 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 140990.00, 11, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 420);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(92, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Loop 2 280', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 121990.00, 12, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(93, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake TH280 V2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 280 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 112990.00, 13, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 280);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(94, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING ZoomFlow 360 XT', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 93990.00, 14, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(95, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MPG CoreLiquid K360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 169990.00, 15, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(96, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix LC II 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 150990.00, 4, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(97, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix LC II 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 181990.00, 5, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(98, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li GA II Lite 240', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 240 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 92990.00, 6, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 240);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(99, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li GA II Lite 360', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Refrigeración líquida con radiador de 360 mm. Compatible con AM4, AM5, LGA1700 y LGA1200.', 113990.00, 7, NULL, 'Líquida', 'AM4, AM5, LGA1700, LGA1200', 360);
INSERT INTO core_refrigeracioncooler (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tipo, socket_compatibles, tamanho_radiador_mm) VALUES
(100, 'Refrigeración', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Mugen 6 Dual', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Cooler por aire compatible con AM4, AM5, LGA1700, LGA1200.', 69990.00, 8, NULL, 'Aire', 'AM4, AM5, LGA1700, LGA1200', NULL);

-- ventilador
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(1, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A12x25 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 30990.00, 5, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(2, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A14 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 31990.00, 6, NULL, 140, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(3, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-P12 redux-1700', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 17990.00, 7, NULL, 120, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(4, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-F12 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 28990.00, 8, NULL, 120, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(5, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-S12A PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 24990.00, 9, NULL, 120, 1200, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(6, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A12x15 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 25990.00, 10, NULL, 120, 1850, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(7, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P12 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 11990.00, 11, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(8, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P14 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 13990.00, 12, NULL, 140, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(9, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P12 PWM PST', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 13, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(10, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P14 PWM PST', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 12990.00, 14, NULL, 140, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(11, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P12 Max', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 15, NULL, 120, 3300, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(12, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic BioniX P120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 14990.00, 4, NULL, 120, 2100, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(13, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair AF120 Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 22990.00, 5, NULL, 120, 1850, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(14, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair AF140 Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 26990.00, 6, NULL, 140, 1600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(15, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE AF120 RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 24990.00, 7, NULL, 120, 1850, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(16, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE AF140 RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 28990.00, 8, NULL, 140, 1600, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(17, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair ML120 RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 31990.00, 9, NULL, 120, 2400, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(18, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair SP120 RGB Elite', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 22990.00, 10, NULL, 120, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(19, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Silent Wings 4 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 28990.00, 11, NULL, 120, 2500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(20, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Silent Wings 4 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 27990.00, 12, NULL, 140, 1900, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(21, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Wings 2 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 13990.00, 13, NULL, 120, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(22, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Wings 2 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 16990.00, 14, NULL, 140, 1000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(23, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Light Wings 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 27990.00, 15, NULL, 120, 1700, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(24, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Light Wings 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 31990.00, 4, NULL, 140, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(25, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master SickleFlow 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 12990.00, 5, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(26, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master SickleFlow 120 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 17990.00, 6, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(27, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Mobius 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 21990.00, 7, NULL, 120, 2050, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(28, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Mobius 120 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 27990.00, 8, NULL, 120, 2050, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(29, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master Mobius 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 26990.00, 9, NULL, 140, 1900, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(30, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT F120 RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 19990.00, 10, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(31, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT F140 RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 23990.00, 11, NULL, 140, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(32, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT F120Q', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 16990.00, 12, NULL, 120, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(33, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughfan 12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 22990.00, 13, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(34, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Toughfan 14', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 26990.00, 14, NULL, 140, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(35, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake Pure 12 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 14990.00, 15, NULL, 120, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(36, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake SWAFAN EX12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 25990.00, 4, NULL, 120, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(37, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool RF120 FS', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 14990.00, 5, NULL, 120, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(38, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool FK120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 6, NULL, 120, 1850, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(39, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool FC120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 20990.00, 7, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(40, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING ZF-12025', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 12990.00, 8, NULL, 120, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(41, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING NO-12015', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 9, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(42, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks T30-120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 36990.00, 10, NULL, 120, 3000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(43, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks SK120 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 17990.00, 11, NULL, 120, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(44, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P12 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 18990.00, 12, NULL, 120, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(45, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P14 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 16990.00, 13, NULL, 140, 1900, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(46, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A14 chromax', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 33990.00, 14, NULL, 140, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(47, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RS120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 16990.00, 15, NULL, 120, 2100, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(48, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair RS140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 19990.00, 4, NULL, 140, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(49, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li UNI FAN SL120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 28990.00, 5, NULL, 120, 1900, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(50, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li UNI FAN SL140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 27990.00, 6, NULL, 140, 1600, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(51, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li UNI FAN P28', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 30990.00, 7, NULL, 120, 2600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(52, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Aspect 12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 16990.00, 8, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(53, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Aspect 14', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 19990.00, 9, NULL, 140, 1700, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(54, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Dynamic X2 GP-12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 16990.00, 10, NULL, 120, 1200, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(55, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone Air Blazer 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 12990.00, 11, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(56, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec Fusion 120 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 15990.00, 12, NULL, 120, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(57, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AX120 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 11990.00, 13, NULL, 120, 1600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(58, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Silent Wings Pro 4 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 35990.00, 14, NULL, 120, 3000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(59, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A12x25 G2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 38990.00, 15, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(60, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic F12 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 8990.00, 4, NULL, 120, 1350, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(61, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master SickleFlow 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 15990.00, 5, NULL, 140, 1400, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(62, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT F120 RGB Core', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 24990.00, 6, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(63, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool FL120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 17990.00, 7, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(64, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake CT120 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 20990.00, 8, NULL, 120, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(65, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING DF-12025', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 14990.00, 9, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(66, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks M25-120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 13990.00, 10, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(67, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE LINK QX120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 41990.00, 11, NULL, 120, 2400, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(68, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair iCUE LINK QX140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 47990.00, 12, NULL, 140, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(69, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Wings 3 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 18990.00, 13, NULL, 120, 1600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(70, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Pure Wings 3 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 16990.00, 14, NULL, 140, 1200, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(71, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A9 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 92 mm.', 20990.00, 15, NULL, 92, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(72, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P8 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 80 mm.', 10990.00, 4, NULL, 80, 3000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(73, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Kaze Flex 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 17990.00, 5, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(74, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Wonder Tornado 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 23990.00, 6, NULL, 120, 2500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(75, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li UNI FAN SL-INF 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 29990.00, 7, NULL, 120, 2100, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(76, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MEG SILENT GALE P12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 25990.00, 8, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(77, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS TUF Gaming TF120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 21990.00, 9, NULL, 120, 1900, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(78, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte AORUS GP-ARGB 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 22990.00, 10, NULL, 120, 1700, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(79, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Momentum 12', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 20990.00, 11, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(80, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Fractal Design'), 'Fractal Design Momentum 14', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 18990.00, 12, NULL, 140, 1600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(81, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Silverstone'), 'Silverstone Air Penetrator 120i', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 13, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(82, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Thermaltake'), 'Thermaltake SWAFAN EX14', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 29990.00, 14, NULL, 140, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(83, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool FC120 A-RGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 20990.00, 15, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(84, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Cooler Master'), 'Cooler Master MasterFan MF120 Halo', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 23990.00, 4, NULL, 120, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(85, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Corsair'), 'Corsair AF120 Slim', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 19990.00, 5, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(86, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Noctua'), 'Noctua NF-A14x25 G2', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 40990.00, 6, NULL, 140, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(87, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P12 Pro', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 14990.00, 7, NULL, 120, 3000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(88, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'be quiet!'), 'be quiet! Light Wings 120 High Speed', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 30990.00, 8, NULL, 120, 2500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(89, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Phanteks'), 'Phanteks D30-120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 28990.00, 9, NULL, 120, 2000, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(90, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'NZXT'), 'NZXT F140Q', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 16990.00, 10, NULL, 140, 1500, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(91, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Montech'), 'Montech AX140 PWM', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 13990.00, 11, NULL, 140, 1600, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(92, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Antec'), 'Antec Fusion 140 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 18990.00, 12, NULL, 140, 1400, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(93, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ID-COOLING'), 'ID-COOLING AS-120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 15990.00, 13, NULL, 120, 1800, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(94, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Scythe'), 'Scythe Kaze Flex 140', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 20990.00, 14, NULL, 140, 1200, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(95, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Lian Li'), 'Lian Li UNI FAN TL 120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm con RGB.', 32990.00, 15, NULL, 120, 2600, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(96, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'MSI'), 'MSI MAX F12A', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 15990.00, 4, NULL, 120, 2000, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(97, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'ASUS'), 'ASUS ROG Strix XF120', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 31990.00, 5, NULL, 120, 1800, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(98, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Gigabyte'), 'Gigabyte AORUS 140 ARGB', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm con RGB.', 25990.00, 6, NULL, 140, 1500, TRUE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(99, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Deepcool'), 'Deepcool FK120 Triple', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 120 mm.', 28990.00, 7, NULL, 120, 1850, FALSE);
INSERT INTO core_ventilador (id, categoria, proveedor_id, nombre, descripcion, precio, stock, imagen, tamanho_mm, velocidad_rpm, rgb) VALUES
(100, 'Ventilador', (SELECT id FROM core_proveedor WHERE nombre = 'Arctic'), 'Arctic P14 Pro', 'Precio y stock sintéticos de demostración; no son un precio de mercado verificado. Ventilador de 140 mm.', 14990.00, 8, NULL, 140, 2500, FALSE);

SELECT setval(pg_get_serial_sequence('core_region', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_region));
SELECT setval(pg_get_serial_sequence('core_comuna', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_comuna));
SELECT setval(pg_get_serial_sequence('core_proveedor', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_proveedor));
SELECT setval(pg_get_serial_sequence('core_procesador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_procesador));
SELECT setval(pg_get_serial_sequence('core_tarjetagrafica', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_tarjetagrafica));
SELECT setval(pg_get_serial_sequence('core_memoriaram', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_memoriaram));
SELECT setval(pg_get_serial_sequence('core_placamadre', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_placamadre));
SELECT setval(pg_get_serial_sequence('core_almacenamientossd', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_almacenamientossd));
SELECT setval(pg_get_serial_sequence('core_almacenamientohdd', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_almacenamientohdd));
SELECT setval(pg_get_serial_sequence('core_gabinete', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_gabinete));
SELECT setval(pg_get_serial_sequence('core_fuentedepoder', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_fuentedepoder));
SELECT setval(pg_get_serial_sequence('core_refrigeracioncooler', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_refrigeracioncooler));
SELECT setval(pg_get_serial_sequence('core_ventilador', 'id'), (SELECT COALESCE(MAX(id), 1) FROM core_ventilador));

COMMIT;
