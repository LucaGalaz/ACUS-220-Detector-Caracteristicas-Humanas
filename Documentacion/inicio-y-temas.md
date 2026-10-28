# Inicio y cambio de tema

La página activa continúa en `app/src/ui/public/`: `index.html` contiene la
descripción y los controles, `style.css` su aspecto y `app.js` el comportamiento.
El componente React y sus ejemplos se prepararon en
`app/src/ui/components/ui/`, junto al fondo de puntos. Esa carpeta agrupa las
piezas reutilizables y mantiene los imports habituales de shadcn.

El inicio muestra «Bienvenido a», el nombre Voihunt y la frase
«Descubre lo que la voz cuenta». El título conserva sus letras normales y
un resplandor suave con `text-shadow`, adaptado al tema. Se retiraron el canvas
y las líneas de color animadas.
Detrás de la descripción y de «Bienvenido a» se comparte la clase `vh-haze`:
una capa radial con bordes difuminados, máscara elíptica y desenfoque,
sin un fondo rectangular sólido.

## Funcionamiento activo

- Botón de tema con iconos Sun/Moon de Lucide adaptados a SVG, entrada con
  escala y giro de 330 ms, y foco visible para navegación con teclado.
- Revelado circular de 900 ms, con cambio gradual de luminosidad, desde el centro del botón hasta la esquina más
  lejana, usando [View Transitions](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using).
  El CSS desactiva el fundido predeterminado para mantener el efecto circular.
- La selección se guarda en `localStorage`; si no está disponible, el cambio
  sigue funcionando. Los clics repetidos durante el revelado se ignoran.
- Sin soporte de View Transitions, los colores cambian con una transición
  CSS de 450 ms. Con movimiento reducido, el tema cambia directamente.
  Los textos, los puntos y el fondo cambian juntos.
- Barra compacta gris translúcida según el tema, con dos botones centrados:
  micrófono y subir archivo. Los botones son sólidos y sus iconos contrastan
  con el fondo. Comparten el mismo hover de escala y los iconos tienen trazos
  redondeados de 2 px. No hay línea, onda ni canvas en la barra.
- Botón CONTINUAR inspirado en [Button de HeroUI](https://heroui.com/en/docs/react/components/button):
  fondo gris suave, esquinas de 14 px, altura de 44 px, feedback de pulsación
  y efecto de onda. Conserva el acceso mediante teclado.
- El logo y el nombre del encabezado vuelven al inicio sin borrar los resultados.
  Si hay una grabación en curso, se detiene y descarta al salir; también se libera
  cualquier micrófono cuyo permiso se complete después de abandonar el panel.
  Una grabación que ya estaba pendiente de revisión se conserva al volver al inicio.
- El encabezado compartido ya no tiene enlace About.
- Las tarjetas del modo claro tienen bordes negros al 16 % para separarlas del fondo.

## Aparición de resultados

La zona de trabajo y las tarjetas son contenedores separados. Al entrar por
primera vez solo se muestran «Todo empieza con la voz» y la barra de audio;
no aparecen tarjetas vacías ni mensajes «Esperando audio».

Las cinco tarjetas se rellenan antes de hacerse visibles. Solo se revelan si
la respuesta del análisis contiene todos los textos esperados, con una animación
simultánea de aparición y escala de 420 ms. Con movimiento reducido aparecen
directamente. Durante la grabación, la revisión y el procesamiento se ocultan
los resultados, incluyendo los de un análisis anterior, para evitar superposiciones.
Si se descarta una nueva grabación, se pueden volver a ver los últimos resultados
válidos. En móvil, las tarjetas se organizan en una columna con desplazamiento.

## Revisión de grabaciones

El botón de micrófono muestra un icono de Stop mientras captura audio.
Antes de iniciar se [consulta el permiso del micrófono](https://developer.mozilla.org/en-US/docs/Web/API/Permissions/query).
Si está concedido, se mantiene la indicación inicial hasta empezar la captura,
y entonces aparece «Te escuchamos…», sin mostrar la solicitud de permisos.
La primera solicitud de autorización utiliza únicamente el diálogo nativo del
navegador; no se muestra una ayuda temporal dentro de la página.
Si está bloqueado, se muestra una indicación persistente y se permite reintentar
o subir un archivo. Cuando el navegador no admite consultar ese permiso,
se conserva el flujo nativo sin inventar un estado de autorización.

Durante la captura, `audio-text-feedback.js` conecta el mismo flujo del micrófono
a un analizador de Web Audio, sin conectarlo a los altavoces. El volumen real
controla la escala y el resplandor de «Te escuchamos…»; las muestras de la señal
mueven cada letra verticalmente. La animación se amortigua hasta quedar quieta
en silencio. Con movimiento reducido solo cambia el resplandor. Al detener,
salir o fallar la grabación se desconectan los nodos, se cierra su AudioContext
y se cancela el bucle de animación.

Al detener la grabación se libera el micrófono. El audio queda
en memoria y aparece un panel centrado en la zona de trabajo con reproducción, duración,
Descartar y Analizar audio. Detener o reproducir no realiza solicitudes a la API.
Se pasa directamente al panel de revisión, sin mensajes de preparación o análisis.
El panel participa en el diseño normal, sin posición fija ni tarjetas detrás.

Solo Analizar audio convierte la grabación a WAV y la envía a `/api/analyze`.
Si falla la conversión o el servidor, se conserva la misma grabación para
escucharla o reintentar. Al completar el análisis o descartarla, se liberan
el audio y su URL temporal. Descartar habilita una nueva grabación.
Durante la revisión se deshabilitan grabación y subida para evitar reemplazos
accidentales. La grabación pendiente sobrevive a la navegación interna al inicio,
pero no se guarda al recargar o cerrar la página.

El reporte conserva su contenido JSON y se descarga con el nombre
`Voihunt_AAAA-MM-DD_HH-mm-ss.json`, usando la fecha y hora local del navegador
en el momento de descargarlo.

## Ventana de subida

`file-upload.js` adapta la tarjeta suministrada a archivos de audio. El icono de
subida abre un `dialog` centrado con fondo desenfocado de 10 px. El selector
del sistema se abre después de pulsar la zona de subida. Se puede arrastrar
un audio, elegirlo mediante teclado, preescucharlo, quitarlo o analizarlo.
La tarjeta conserva el grupo de iconos de la referencia, con borde neutro:
no hay destello azul, subtítulo ni botón de cierre con X.

Se acepta un solo audio, comprobando MIME o extensión para archivos sin MIME.
Se rechazan archivos vacíos y tipos no admitidos. La selección no envía el audio
hasta pulsar Analizar audio. La conversión WAV y `/api/analyze` conservan el flujo
existente. Si la conversión falla, la ventana vuelve a abrirse con el error.
Escape, Cancelar y un clic fuera cierran la ventana. El foco permanece
dentro del diálogo y vuelve al botón de subida al cerrarlo; las vistas previas
liberan sus URL temporales al reemplazarlas o cerrar.

La versión activa usa las APIs del navegador, sin añadir React al servidor.
No necesita paquetes npm, imágenes de stock ni proveedores nuevos.

## Fuentes React

- `animated-theme-toggler.tsx` y `animated-theme-toggler.css`: adaptación del
  componente suministrado, con Framer Motion, Lucide y las clases existentes
  `dark-theme`/`light-theme`.
- `animated-theme-toggler-demo.tsx`: demostración separada del ejemplo del fondo.
- `button.tsx` y `button-example.tsx`: botón nativo reutilizable con el aspecto
  predeterminado de shadcn solicitado anteriormente. Para sus variantes,
  se puede generar su Button mediante el CLI.
- `file-upload.tsx`: componente React original del texto adjunto.
- `file-upload-demo.tsx`: ejemplo configurado para un solo audio y sin BorderBeam.
- `heroui-button-example.tsx`: botón CONTINUAR usando `@heroui/react`.

Estos archivos no son ejecutados por la página HTML actual. Para usarlos en
React, seguir primero la [configuración de Vite, TypeScript, Tailwind y shadcn](fondo-puntos.md#configurar-react--typescript--tailwind--shadcn).
Después, desde la raíz del frontend React:

```powershell
npm install lucide-react framer-motion clsx tailwind-merge
Copy-Item ../src/ui/components/ui/animated-theme-toggler* src/components/ui/
Copy-Item ../src/ui/components/ui/button*.tsx src/components/ui/
```

Mantener `@/*` apuntando a `src/*`, `cn` en `src/lib/utils.ts` y la variante
Tailwind `dark` vinculada a `.dark-theme`, como explica la guía anterior.
El componente importa su CSS de transición automáticamente. No requiere
props salvo `className`, ni un proveedor de temas. Para instalar el Button
completo de shadcn en lugar del ejemplo mínimo: `npx shadcn@latest add button`.

Para probar los nuevos ejemplos en ese frontend React, instalar sus dependencias
y copiar las fuentes adicionales a `src/components/ui`:

```powershell
npm install border-beam @hugeicons/react @hugeicons/core-free-icons
npm install @heroui/react @heroui/styles
Copy-Item ../src/ui/components/ui/file-upload*.tsx src/components/ui/
Copy-Item ../src/ui/components/ui/heroui-button-example.tsx src/components/ui/
```

[HeroUI v3](https://heroui.com/en/docs/react/getting-started/quick-start) requiere
React 19 y Tailwind 4. Importar `@heroui/styles` después de `tailwindcss` en el
CSS global. Estos pasos son para una futura
interfaz React; la página activa ejecuta las adaptaciones nativas sin paquetes npm.
