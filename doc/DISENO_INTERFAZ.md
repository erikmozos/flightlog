# Flightlog — diseño de interfaz

Este documento describe **qué es** el diseño visual de la aplicación: principios, tokens, estructura de pantallas y cómo se reparte el CSS entre plantillas. Complementa el registro de cambios **`doc/2026-05-07.md`**.

---

## 1. Objetivo del diseño

- **Coherencia** entre pantallas públicas de acceso (login/registro) y zona autenticada (panel, bitácora, formularios, detalle).
- Apariencia **clara y profesional**, tipo producto SaaS de aviación: mucho blanco, navy como color de marca, grises para texto secundario y acentos para estados (planificado, en curso, completado, cancelado).
- **Legibilidad** y jerarquía: títulos fuertes, etiquetas en mayúsculas pequeñas donde ayuda, espaciado generoso.

---

## 2. Tipografía

- **Inter** (Google Fonts) en toda la interfaz que usa `base.html` o `auth_base.html`.
- Pesos habituales: **400** (cuerpo), **500–600** (menús, etiquetas), **700** (títulos y cifras destacadas).

---

## 3. Tokens de color (variables CSS)

En **`templates/base.html`** se definen, con prefijo `--fl-`:

| Token | Uso típico |
|--------|------------|
| `--fl-navy`, `--fl-navy-hover` | Marca, botones primarios, títulos fuertes |
| `--fl-navy-soft` | Fondos suaves de ítems activos en sidebar |
| `--fl-text` | Texto principal |
| `--fl-muted` | Subtítulos, etiquetas, texto secundario |
| `--fl-border` | Bordes de tarjetas y campos |
| `--fl-bg` | Fondo de página gris muy claro |
| `--fl-surface` | Superficies blancas (tarjetas, topbar) |
| `--fl-link`, `--fl-link-hover` | Enlaces |

Las pantallas de **login/registro** repiten una lógica muy similar en **`templates/users/auth_base.html`** con prefijo **`--auth-*`** (mismos tonos navy/grises para mantener continuidad visual).

Los **estados de vuelo** usan verdes, azules, ámbar y rojos **apagados** (badges tipo «píldora»), alineados en lista, dashboard, detalle y formularios.

---

## 4. Patrones de componente

### 4.1 Autenticación (`auth_base.html`)

- Fondo con **gradiente radial** claro (centrado más luminoso que los bordes).
- **Tarjeta** central blanca, sombra suave, radio ~16px.
- Campos en **cápsulas** grises (`auth-input-shell`) con icono SVG a la izquierda (y ojo para contraseña).
- Botón principal **relleno navy**, texto blanco.

### 4.2 Marco de aplicación (`base.html`)

- **Sidebar** fija a la izquierda: logo texto + icono avión, bloque usuario (inicial en círculo), navegación con iconos, pie con admin y cierre de sesión.
- **Topbar**: pestañas que repiten las mismas secciones (Panel, Bitácora, Nuevo vuelo) con subrayado azul en la ruta actual.
- **Main**: padding generoso; cada pantalla aporta su contenido en `{% block content %}`.

En **móvil** (~900px), el sidebar pasa a **flujo vertical** (menú envuelto) según reglas en el propio `base.html`.

### 4.3 Dashboard, lista, formulario y detalle

- **Cabecera de página**: título navy + subtítulo gris; a menudo acciones a la derecha (buscar, nuevo vuelo, imprimir…).
- **Tarjetas** (`border-radius` ~14px, borde ligero, sombra común `--fl-shadow`).
- **Tablas**: cabeceras en mayúsculas pequeñas, filas con hover suave; enlaces a detalle en fechas o textos clave.
- **Formulario de vuelo**: rejilla 2 columnas + campo ancho completo para observaciones; iconos por campo en `ff-shell`.
- **Detalle**: tarjeta «Información general» + tarjeta **Vuelo activo** (fondo navy) solo si está en curso; sidebar con resumen, mapa conceptual y listado de PDFs/enlaces de cartas.

---

## 5. Dónde vive el CSS

- **No** hay un único archivo `static/css/app.css` obligatorio en esta fase del proyecto.
- Los estilos globales del **shell** están en **`<style>` dentro de `base.html`**.
- **Auth**: estilos en **`auth_base.html`**.
- Pantallas concretas añaden bloques **`{% block extra_head %}`** con prefijos de clase acordes:
  - Dashboard: clases `dash-*`
  - Bitácora: `log-*`
  - Crear vuelo: `ff-*`
  - Detalle: `fd-*`

**Ventajas** del enfoque actual: cero configuración extra de estáticos para empezar; todo el contexto visual de una pantalla suele estar en un solo sitio.

**Inconvenientes**: menos reutilización automática entre archivos, caché del navegador menos agresiva que con un `.css` versionado. Un paso natural de evolución sería **extraer** los bloques comunes a `static/css/` y enlazarlos con `{% static %}` sin cambiar clases.

---

## 6. Iconografía

- **SVG en línea** en plantillas (avión de marca, sobre, candado, reloj, impresora, etc.).
- Objetivo: misma línea de trazo (stroke ~2) y tamaños coherentes (~18–22px en campos, algo mayor en héroes).

---

## 7. Accesibilidad y datos que el diseño asume

- Contraste razonable navy/blanco y texto sobre gris claro.
- Estados de vuelo también se comunican con **texto** (`get_status_display`), no solo color.
- Algunas cifras del **sidebar** (combustible, distancia exacta, certificación médica) son **placeholders** hasta existir campos en el modelo.

---

## 8. Resumen en una frase

**Flightlog** usa **Inter**, **navy corporativo** y **tarjetas blancas sobre fondo gris**, con un **shell lateral + barra superior** en la zona autenticada y **pantallas de auth a página completa**; el CSS está **principalmente en plantillas** por bloques (`base`, `auth_base`, `extra_head`) con convenciones de clase por pantalla.
