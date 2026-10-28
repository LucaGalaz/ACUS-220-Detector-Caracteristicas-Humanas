# Fondo de puntos

## Integración activa

La aplicación sirve `app/src/ui/public/index.html`, `style.css` y `app.js`
desde FastAPI. Actualmente no utiliza React, TypeScript, Tailwind ni shadcn,
y no tiene un gestor de paquetes JavaScript o una etapa de compilación.

El fondo activo adapta el mismo SVG del componente: separación de 16 px,
radio de 1 px y máscara radial que difumina los extremos. Cubre la ventana
tanto en el inicio como en el panel. CSS selecciona fondo negro/puntos blancos
o fondo blanco/puntos negros mediante las clases de tema existentes.
La opacidad y la máscara conservan el aspecto suave de la referencia.

El CSS y JavaScript se cargan con una versión en la URL para evitar mezclar
el HTML nuevo con recursos anteriores guardados en caché. La ruta principal
de FastAPI devuelve `Cache-Control: no-cache` para revalidar el HTML.
Las clases de tema también configuran `color-scheme`, y el SVG tiene tamaño
explícito de ventana para no ocupar el tamaño predeterminado de 300 × 150 px.

El SVG es decorativo, no recibe foco ni intercepta clics. Se retiró la carga
del fondo WebGL y de Three.js de la página. Este fondo no requiere imágenes,
iconos, paquetes externos, estado ni proveedores.

## Componentes React preparados

- `app/src/ui/components/ui/dot-pattern.tsx`: componente reutilizable tipado,
  con `useId` para evitar conflictos entre patrones.
- `app/src/ui/components/ui/demo.tsx`: ejemplo independiente de 500 px.
- `app/src/ui/lib/utils.ts`: utilidad `cn` habitual de shadcn.

Estos archivos son fuentes para una futura interfaz React; FastAPI no los
compila ni los ejecuta en la página actual.

No existía una carpeta de componentes. Se creó `components/ui` dentro de
`app/src/ui`, la raíz de la interfaz, para agrupar componentes reutilizables
y conservar los imports `@/components/ui/...` de shadcn. Los estilos activos
siguen en `app/src/ui/public/style.css`.

`width`/`height` controlan la separación del patrón; `x`/`y`, su desplazamiento;
`cx`/`cy`, el centro de cada punto; y `cr`, su radio. `className` permite ajustar
opacidad, máscara y colores. El SVG ocupa el tamaño de su contenedor, que debe
tener posición relativa y dimensiones. No requiere datos de la API.

## Configurar React + TypeScript + Tailwind + shadcn

Para crear una interfaz React separada, desde `app/`:

```powershell
npx shadcn@latest init -t vite
```

Indicar `frontend-react` como nombre del proyecto y seleccionar TypeScript
si el asistente pregunta. La plantilla configura Vite, React, Tailwind y
shadcn. Ver [instalación oficial con Vite](https://ui.shadcn.com/docs/installation/vite).

Después, desde `app/frontend-react/`:

```powershell
npm install
npm install clsx tailwind-merge
New-Item -ItemType Directory -Force src/components/ui, src/lib
Copy-Item ../src/ui/components/ui/dot-pattern.tsx src/components/ui/
Copy-Item ../src/ui/components/ui/demo.tsx src/components/ui/
Copy-Item ../src/ui/lib/utils.ts src/lib/utils.ts
```

Comprobar que `@/*` apunta a `./src/*` en TypeScript y Vite, y que
`components.json` usa `@/components/ui` para `ui` y `@/lib/utils` para `utils`.
La hoja global de esa plantilla es `src/index.css`.

Si se usa una plantilla Vite manual (`npm create vite@latest frontend-react -- --template react-ts`),
instalar Tailwind con `npm install tailwindcss @tailwindcss/vite`, agregar
`tailwindcss()` a los plugins de `vite.config.ts`, importar
`@import "tailwindcss";` en `src/index.css`, configurar el alias anterior y
ejecutar `npx shadcn@latest init`. La plantilla `react-ts` incluye TypeScript.
Ver [configuración oficial de Tailwind con Vite](https://tailwindcss.com/docs/installation/using-vite).

Para que las variantes `dark:` respondan al interruptor existente, usar esta
variante en el CSS global, reemplazando la variante `dark` de la plantilla:

```css
@custom-variant dark (&:where(.dark-theme, .dark-theme *));
```

Para ver el ejemplo, importar y renderizar `DotPatternDemo` en `src/App.tsx`.
Para un fondo de aplicación completo, colocar `DotPattern` detrás del
contenido en un contenedor con `relative min-h-svh bg-white dark:bg-black`,
con la misma máscara radial del ejemplo.

```powershell
npm run build
npm run dev
```

Este procedimiento prepara otro frontend; su futura conexión a FastAPI
requiere servir su compilación y conservar las llamadas a `/api/analyze`.
La aplicación actual ya muestra el patrón sin realizar esa migración.
