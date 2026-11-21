# Registro de versión

## 2026-11-20 · V1.0, entrega fase 02

- Se creó el sitio de dos exploradores: CO protagonista, atlas general y catálogo histórico separado.
- Se construyó Excel maestro editable (20 hojas V1.1 importadas + 9 auxiliares), y exportador Python estándar verificable.
- Se preservaron 249/365/1,157/5,270/2,730/36/747 y 30 conceptos, 126 enlaces CO nuevos y 6 heredados.
- Se implementó motor JS compartido entre sitio y pruebas de filtros, fichas, búsqueda, paginación, estados vacíos y barras de cobertura.
- Se adoptó la corrección V1.1 de páginas 31 para los conceptos CO-00027 y CO-00028, dejando el legado sin alteración.
- Se agregaron marcas de revisión provisional, licencia, derechos, trazabilidad y condiciones de publicación.
- Se registró bloqueo de Chromium y falta de pruebas remotas reales, sin atribuir aprobación a estas verificaciones.

**Congelar este corte para fase 03:** la revisión posterior generará una nueva entrega con su propio hash, sin sobrescribir silenciosamente V1.0.

---

## Fase 03 · Cierre corregido V1.0 para el profesor · 2026-11-20

La entrada de esta sección corresponde al **cierre final local**, distinto de las anotaciones heredadas de la fase 02. Ningún archivo original de `private/` fue modificado.

1. **Navegación entre exploradores:** se añadieron dos acciones a las fichas que localizan el mismo ID normalizado/original en el Atlas general y, si existen vínculos, en el explorador CO. El botón CO se oculta cuando el registro carece de relaciones. No se introducen nuevos registros o correspondencias.
2. **Transparencia científica:** se retiró el título excesivamente concluyente «Vínculos fundamentados». Se muestra el procedimiento de cada relación, separando curaduría específica, cribado documental y cotejo de pregunta-indicador. Se añadió reserva explícita sobre los 126 enlaces, de los cuales 68 son parciales.
3. **Exactitud metodológica:** se aclaró que el rol X/Y/moderación debe establecerse por pregunta y que el puente pregunta-variable todavía no está validado. Las 116 preguntas CAU continúan como candidatas, sin efectos demostrados.
4. **Robustez de interfaz:** el sitio muestra un mensaje comprensible cuando falta la base de datos o el motor JS, en vez de detener la interfaz antes de mostrar el error.
5. **Accesibilidad visual:** se elevaron los contrastes en etiquetas, acciones y botones pequeños, sin eliminar la paleta original naranja/café. Los botones dinámicos con atributo `hidden` permanecen realmente ocultos. Se ajustó el tamaño táctil en acciones de ficha móvil.
6. **Pruebas reales ampliadas:** se creó `scripts/test_browser_embedded.py`, ejecutado en Chromium con DOM/CSS/JS originales inyectados en memoria. Se comprobaron filtros, búsquedas, fichas, cruces, teclado, impresión PDF y seis anchos de pantalla. Resultados documentados en `docs/QA_NAVEGADOR_03_V1_2026-11-20.json`.
7. **Cierre y trazabilidad:** informe final en PDF, capturas originales del navegador, manifiesto SHA-256 regenerado y ZIP final reempaquetado. Se conserva el CSV/JSON derivado original, validado contra el Excel maestro.

**Reservas abiertas a V2:** revisión académica individual y ratificación docente, permisos de difusión pública, prueba en navegadores/dispositivos físicos, lector de pantalla, carga real en GitHub Pages, validez de las relaciones semiautomatizadas, normalización municipal y puente pregunta-variable.
