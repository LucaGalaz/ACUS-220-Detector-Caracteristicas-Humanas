# Fondo de puntos

El fondo está definido por el SVG `vh-dot-pattern` de
`app/src/ui/public/index.html`. Sus estilos están en `style.css`.

Cada celda mide 16 × 16 píxeles y contiene un punto de radio 1. El SVG ocupa
la ventana completa, detrás de la interfaz. No recibe clics ni interfiere
con los controles.

Los temas usan las variables `--vh-bg-color` y `--vh-dot-color`:

| Tema | Fondo | Puntos |
| --- | --- | --- |
| Claro | Blanco | Negros |
| Oscuro | Negro | Blancos |

La máscara radial reduce la visibilidad de los puntos hacia los bordes.
`vh-haze` suaviza el fondo detrás de los textos centrales.

El cambio de tema lo controla `app.js`, mediante las clases `light-theme` y
`dark-theme` del elemento `html`. No hay librerías de fondos ni animaciones
WebGL cargadas por la página.
