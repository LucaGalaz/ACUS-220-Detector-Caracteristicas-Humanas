# Interfaz

La interfaz está en `app/src/ui/public/`. FastAPI sirve los archivos sin una
etapa de compilación.

| Archivo | Contenido |
| --- | --- |
| `index.html` | Pantallas, controles, diálogo de subida y fondo de puntos |
| `style.css` | Temas, distribución, tarjetas y estados visuales |
| `app.js` | Navegación, grabación, análisis y exportación |
| `file-upload.js` | Selección de archivos, arrastre y vista previa |
| `audio-text-feedback.js` | Lectura del nivel del micrófono |

## Inicio y navegación

La portada muestra «Bienvenido a», el título Voihunt y «Descubre lo que la voz
cuenta». CONTINUAR abre la zona de trabajo. El nombre y el logo del encabezado
vuelven al inicio.

Al salir se cancela una grabación en curso y se libera el micrófono. Una
grabación que ya estaba pendiente de revisión se conserva durante la navegación
interna, junto con los últimos resultados. No se guarda al cerrar o recargar.

## Temas

El tema se guarda en `localStorage`. El cambio usa un revelado circular desde
el botón durante 900 ms. Si el navegador no admite View Transitions, se usa
una transición de colores de 450 ms. Con movimiento reducido, el cambio es
directo.

El fondo de puntos, los textos, las tarjetas y los controles comparten las
variables de color. El halo de los textos centrales se define con `vh-haze`.

## Grabación

Al pulsar el micrófono aparece «Te escuchamos…». La ayuda de permisos solo se
muestra cuando falta autorización. Si el permiso está bloqueado, se indica
que hay que revisarlo en el navegador.

Durante la captura, el medidor de 24 segmentos muestra el nivel real del audio,
en una escala de −72 a 0 dBFS. Lee el bloque actual unas 30 veces por segundo,
sin secuencias animadas. No reproduce el sonido por los altavoces.

Stop muestra un indicador de carga mientras se completa el archivo y después
abre la revisión. Se puede escuchar, descartar o analizar la grabación. El audio
solo se envía al servidor al pulsar Analizar audio.

## Subida y errores

El botón de subida abre un diálogo centrado con el fondo desenfocado. Admite
un archivo de audio, seleccionado desde el equipo o arrastrado a la zona de
subida. Incluye reproducción previa, eliminación y análisis.

Los archivos tienen un límite de 25 MB y de 1 a 120 segundos. Los errores se
muestran junto al archivo o a la grabación, que se conserva para reintentar.
Cancelar, Escape o un clic fuera del diálogo cierran la ventana. Las vistas
previas liberan sus URL temporales al cambiar de archivo o cerrar.

## Resultados

Las tarjetas aparecen juntas cuando termina el análisis y ya contienen datos.
Se ocultan durante otra grabación, revisión o análisis. En escritorio forman
una cuadrícula de dos columnas; en móvil se muestran en una columna desplazable.

Exportar JSON está arriba a la derecha. El nombre del archivo tiene el formato
`Voihunt_AAAA-MM-DD_HH-mm-ss.json`, con la fecha y hora local de la descarga.
El formato y los límites del reporte están en [Análisis de voz](analisis-voz.md).
