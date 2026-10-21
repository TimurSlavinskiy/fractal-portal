# Mathematical and numerical notes — Fractal Portal v2

Fractal Portal v2 is a **mathematical artwork explorer**, not a scientific simulation of light or physical material. Every rendered pixel is computed from equations in either a WebGL2 fragment shader or a JavaScript Canvas 2D fallback.

## 1. Quadratic Julia dynamics

Given a complex constant $c=a+bi$, each pixel corresponds to a different initial complex point $z_0=x+iy$. The iteration is

$$z_{n+1}=z_n^2+c.$$

Write $z_n=u_n+iv_n$. The same recurrence using real numbers is

$$u_{n+1}=u_n^2-v_n^2+a,\qquad v_{n+1}=2u_nv_n+b.$$

Points whose orbits escape (in our finite iteration budget) are colored according to how and when they escape. Points that remain bounded *within the tested iterations* are drawn dark: this is an approximation to the filled Julia set, not proof that those points never escape.

## 2. Escape-time smoothing

When $|z_n|$ exceeds the chosen escape radius (16), a smooth iteration measure is estimated using

$$\mu\approx n+2-\log_2\!\left(\log|z_n|\right).$$

Here $n$ is the zero-based loop index. Smooth iteration values help remove discrete bands from the coloring, but color remains an artistic choice.

## 3. Complex derivative and distance estimation

For the Julia map $f_c(z)=z^2+c$, sensitivity to the *initial point* follows

$$D_0=1,\qquad D_{n+1}=2z_nD_n.$$

An exterior-distance heuristic is then computed from the escaped orbit,

$$d(z_0)\approx \frac{|z_n|\ln|z_n|}{|D_n|}.$$

The renderer uses the estimated pixel distance to amplify narrow intricate boundaries, combine multiple glow scales, and blend colors. This is a numerical visualization heuristic, not an exact signed distance to every boundary pixel.

## 4. Camera model and interaction

Viewport coordinates are mapped to the complex plane in equal world-space units along x and y. Dragging changes the center $(x_c,y_c)$, while zoom changes the pixel scale. The mouse-wheel zoom attempts to preserve the complex coordinate under the pointer.

## 5. Color and glow

Cosine-based functions of the smoothed escape count and final orbit angle produce smooth artistic palettes (Aurora, Ember, Coral, Frost). The screenshot, export and animation all come from a deterministic mathematical renderer, not a downloaded illustration or an image-generation service.

## 6. Accuracy and limitations

- **WebGL2 GPU shader**: operates primarily on 32-bit floating point values, so very deep zooms can lose fine structure and precision. The UI deliberately caps zoom at 32×.
- **Canvas 2D fallback**: computes the same recurrence using JavaScript double-precision numbers but caps its output resolution for responsiveness.
- **Finite iterations**: being dark only means the orbit has not escaped within the configured iteration budget.
- **Independent implementations**: the browser shader and the Python gallery renderer differ in color processing and rendering resolution, and do not promise identical pixels.
- **Automation**: source tests and JavaScript syntax checks do not establish behavior on every browser or GPU. Real browser tests are additionally useful.

For further mathematical study, investigate periodic orbits, connected Julia sets, parameter-plane Mandelbrot sets, automatic differentiation, numerical precision, adaptive iteration limits, and antialiasing.
