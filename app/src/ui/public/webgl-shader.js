document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("webgl-canvas");
  if (!canvas) return;

  const scene = new THREE.Scene();
  const renderer = new THREE.WebGLRenderer({ canvas });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setClearColor(new THREE.Color(0x000000));

  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, -1);

  const isLight = document.documentElement.classList.contains("light-theme");
  
  const uniforms = {
    resolution: { value: [window.innerWidth, window.innerHeight] },
    time: { value: 0.0 },
    xScale: { value: 1.0 },
    yScale: { value: 0.5 },
    distortion: { value: 0.05 },
    uTheme: { value: isLight ? 1.0 : 0.0 }
  };

  const vertexShader = `
    attribute vec3 position;
    void main() {
      gl_Position = vec4(position, 1.0);
    }
  `;

  const fragmentShader = `
    precision highp float;
    uniform vec2 resolution;
    uniform float time;
    uniform float xScale;
    uniform float yScale;
    uniform float distortion;
    uniform float uTheme;

    void main() {
      vec2 p = (gl_FragCoord.xy * 2.0 - resolution) / min(resolution.x, resolution.y);
      
      float d = length(p) * distortion;
      
      float rx = p.x * (1.0 + d);
      float gx = p.x;
      float bx = p.x * (1.0 - d);

      float r = 0.05 / abs(p.y + sin((rx + time) * xScale) * yScale);
      float g = 0.05 / abs(p.y + sin((gx + time) * xScale) * yScale);
      float b = 0.05 / abs(p.y + sin((bx + time) * xScale) * yScale);
      
      vec3 color = vec3(r, g, b);
      vec3 finalColor;
      
      if (uTheme > 0.5) {
         // Light theme: Fondo gris para mayor contraste (#c0c0c0)
         vec3 bg = vec3(0.75, 0.75, 0.75);
         
         // Para que brille igual que en el modo oscuro sin perder su color original,
         // extraemos el color puro (hue) de las ondas
         // y lo superponemos al fondo claro.
         float maxColor = max(r, max(g, b));
         vec3 hue = color / max(maxColor, 0.001);
         finalColor = mix(bg, hue, clamp(maxColor, 0.0, 1.0));
      } else {
         // Dark theme: Fondo casi negro con adición de color
         vec3 bg = vec3(0.012, 0.020, 0.008); 
         finalColor = bg + color;
      }
      
      gl_FragColor = vec4(finalColor, 1.0);
    }
  `;

  const position = [
    -1.0, -1.0, 0.0,
     1.0, -1.0, 0.0,
    -1.0,  1.0, 0.0,
     1.0, -1.0, 0.0,
    -1.0,  1.0, 0.0,
     1.0,  1.0, 0.0,
  ];

  const positions = new THREE.BufferAttribute(new Float32Array(position), 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", positions);

  const material = new THREE.RawShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: uniforms,
    side: THREE.DoubleSide,
  });

  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  let animationId;
  const animate = () => {
    uniforms.time.value += 0.01;
    renderer.render(scene, camera);
    animationId = requestAnimationFrame(animate);
  };

  const handleResize = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    renderer.setSize(width, height, false);
    uniforms.resolution.value = [width, height];
  };

  handleResize();
  animate();
  window.addEventListener("resize", handleResize);

  // Watch for theme changes on html element
  const observer = new MutationObserver(() => {
    const currentlyLight = document.documentElement.classList.contains("light-theme");
    uniforms.uTheme.value = currentlyLight ? 1.0 : 0.0;
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
});
