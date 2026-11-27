# Montaje de modelos 3D

El visualizador no guarda coordenadas de piezas en la escena. Cada modelo se incorpora con su archivo GLB y una ficha en `core/static/core/js/pc-modelos.js`. `pc-visualizer.js` solo pide el punto de montaje y coloca la pieza.

## Responsabilidades

- Archivos GLB: `core/static/core/modelos/<pieza>/`.
- Escala, rotación y pivote: `EJES`, `APOYO` y `PIVOTE` en `pc-modelos.js`.
- Anclas de la placa y bahías del gabinete: objeto `REFERENCIA` en el mismo archivo.
- Ensamblaje: `posePlaca`, `anclaPlaca`, `asientoCooler` y `puesto`. El armador llama estas funciones.
- Materiales, vidrio e iluminación: `pc-visualizer.js`. El tinte de cada GLB está en `estilizar`.

La escala de cada pieza es uniforme y sale de la altura de `pc-case.glb`, también cuando se muestra otro gabinete. La placa ATX usa `atx-motherboard.glb` y la Micro-ATX usa `matx-motherboard.glb`. Las dos comparten la rotación y el signo en X, y cada una tiene su pivote. ATX y Micro-ATX usan `mid-tower.glb` y la ficha `GABINETE_MID`: la bandeja, el borde trasero y la bahía de la fuente se midieron en ese interior. Mini-ITX usa `mini-itx.glb` y la ficha `GABINETE_ITX`, en metros del archivo y a la misma escala que las piezas, sin estirar la caja a la altura del mid-tower. La ATX conserva 305 × 244 mm; su pivote es el centro de ese PCB (0,1525 m, −0,122 m), no el de la Micro-ATX. El tercer M.2, en x = 0,052 m, solo existe en la ATX. La fuente se apoya en el piso de esa bahía, con la toma hacia la pared trasera. Su malla mide 89,6 mm de alto, más que los 86 mm ATX y que los 86,2 mm libres bajo la cubierta; en el mid-tower solo se corrige esa altura. El ancho, el fondo y los anclajes de las demás piezas no cambian. La placa mide 244 × 244 mm porque se recortó el borde inferior del PCB; el socket, las DIMM y la PCIe conservan el tamaño del modelo ATX. En la GPU de dos ventiladores, el soporte se desplaza —sin cambiar de tamaño— hasta la columna de ranuras y por debajo del ventilador trasero. El cuerpo de esa tarjeta se acerca 8 mm a la placa para entrar en la PCIe, sin mover el ancla ni el soporte. La GPU de hasta 170 mm usa `gpu-mini-itx-170.glb`. En Micro-ATX el HDD de 3,5 pulgadas entra en una jaula de dos bahías bajo la cubierta, delante de la fuente, y el SSD de 2,5 pulgadas queda sobre esa cubierta. El M.2 sigue anclado a la placa. En Micro-ATX el apoyo es la cara superior de la PCB, en el conector 1 o el 2; la tapa de esa ranura se oculta solo mientras está ocupada. En ATX el apoyo es la misma cara del PCB de `atx-motherboard.glb`, en los conectores 1, 2 o 3, y la tapa se oculta igual. La jaula y los soportes de 2,5" son los del mid-tower. El gabinete Mini-ITX medido no trae bahías de 3,5 ni de 2,5 pulgadas: esos discos no se dibujan y el aviso de bahías lo indica. El M.2 sigue anclado a la placa.

El archivo del gabinete sale del formato del gabinete seleccionado. Si no hay gabinete, se usa el formato de la placa. La malla de la placa y sus anclajes salen del formato de la placa: una Mini-ITX dentro de un gabinete ATX o Micro-ATX se apoya en la bandeja del mid-tower con su tamaño de 170 mm. La GPU de hasta 170 mm usa `gpu-mini-itx-170.glb` por el largo del producto. La fuente SFX se elige cuando el nombre del producto contiene SFX; la de 450 W normal conserva `power-supply-unit.glb`. El cooler de hasta 80 mm, como el de 58 mm, usa `cooler-bajo-58.glb`. El de 150 mm sigue en `cpu-cooler.glb`. Las bahías de 3,5 y 2,5 pulgadas salen de la ficha del gabinete mostrado.

## Sustituir un GLB

1. Reemplazar el archivo en su carpeta y conservar `LICENSE.txt` y `ORIGEN.txt`.
2. No cambiar el nombre que ya está en `ARCHIVOS`, o actualizar solo esa entrada.
3. Medir el nuevo modelo en metros del archivo y corregir su línea de `EJES`, `APOYO` o `PIVOTE`.
4. Si es una placa, volver a medir `REFERENCIA.placa` (socket, contacto, cada DIMM, PCIe y M.2). No reutilizar el centro de la caja.
5. Subir `?v=` del import en `pc-visualizer.js` y el de la plantilla, y la aserción de `core/test_visualizador_pc.py`.

Una variante futura (otro gabinete, otra placa, otra GPU) se agrega como entrada nueva. No hace falta editar el resto de las piezas ni la lógica de `plan`.

## Medir una placa

El GLB actual se apoya con el borde trasero de E/S hacia −Z del archivo y los componentes hacia +Y. Los anclajes de `REFERENCIA.placa` están en ese sistema:

- `socket`: centro del zócalo y altura de la superficie de contacto (`y`).
- `dimm`: un punto por ranura, en el centro de la ranura y a la altura de los contactos.
- `pcie` de la placa ATX: centro de la x16 principal y extremo trasero de esa ranura. Las mallas de las ranuras PCIe, que ya venían separadas, se desplazaron 33,05 mm hacia el borde de E/S para que el bracket de la GPU coincida con la trasera del gabinete sin alargar la tarjeta. Socket, DIMM y conectores conservan su tamaño.
- `m2`: centro de la almohadilla. `pasoZ` separa un segundo módulo porque el modelo solo trae un disipador visible.

`PIVOTE` indica qué punto del componente cae sobre ese ancla. El cooler usa el centro de la base de cobre, no el centro de la torre. La GPU usa el centro de los contactos PCIe, no el centro de la tarjeta.

## Comprobación

Activar `window.hwMarcadores = true` y volver a sincronizar el armado muestra el socket en rojo, las DIMM en verde, el PCIe en azul y el M.2 en amarillo. Esos marcadores no forman parte de la vista normal.
