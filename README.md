# Atlas Mayab · V1.0 cerrada para revisión privada del profesor

**Corte:** 21:00, 20 de noviembre de 2026. **Estado:** V1.0 técnica local revisable, sin aprobación científica/institucional ni permiso de publicación abierta.

## Abrir el Atlas

1. Descomprimir este ZIP completo y mantener la estructura de carpetas.
2. Abrir `site/index.html`. Se incluye `site/data/atlas-data.js` para consultar el sitio sin depender de `fetch()`.
3. Como alternativa para revisión HTTP local, desde la raíz del ZIP descomprimido ejecutar `python -m http.server 8000` y visitar `http://localhost:8000/site/`.
4. Iniciar con el **Explorador CO (02)**. El **Atlas general (01)** conserva las 249 propuestas y las preguntas que no pertenecen al CO. Las fichas enlazan ambos recorridos por el mismo ID.

## Qué consultar primero

- `docs/03_INFORME_CIERRE_PROFESOR_V1_2026-11-20.pdf` — auditoría 03, controles, reservas, guía y notas para el profesor.
- `docs/CHANGELOG_V1_2026-11-20.md` — bitácora de correcciones V1.0. Las fases 00, 01 y 02 no fueron sobrescritas.
- `docs/README_V1_2026-11-20.md` — manual técnico detallado de la etapa 02.
- `docs/QA_NAVEGADOR_03_V1_2026-11-20.json` — ejecución real de controles DOM en Chromium; no equivale a despliegue HTTP remoto.
- `docs/QA_LOCAL_V1_2026-11-20.json` — pruebas de conteo, lógica y HTTP local desde subruta.
- `docs/MANIFIESTO_V1_2026-11-20.json` — rutas, tamaños y hashes SHA-256.

## Editable, derivados y publicación

- **Fuente editable:** `private/02_ATLAS_MAESTRO_MAYAB_V1.0_2026-11-20.xlsx`.
- **Datos web derivados:** `site/data/atlas.json`, `site/data/atlas-data.js` y los CSV. Se regeneran con `python scripts/build.py`.
- **Legado inmutable:** archivo unificado, fuentes de etapa 01 y control fase 00 en `private/`.
- **NO PUBLICAR AHORA.** Antes de la publicación hay que obtener permisos y revisar derechos, privacidad, citas e identidad académica. Cuando exista autorización, **solo** el contenido de `site/` debe ir a GitHub Pages. Nunca publicar `private/`, el ZIP completo o materiales protegidos.

## Pruebas reproducibles

```bash
python scripts/build.py --check
node scripts/test_logic.js
python scripts/test.py
python scripts/test_browser_embedded.py
python scripts/manifest.py
```

La prueba Chromium incrusta scripts/estilos reales en un documento en memoria porque el entorno puede bloquear `localhost` y `file://` en el navegador. El servidor HTTP local sí se prueba por código 200 y MIME mediante Python. No se comprobó una URL remota, Safari real, lector de pantalla ni un móvil físico.

**Cualquier cambio solicitado tras la revisión del profesor deberá versionarse como V2.0 y mantener esta V1.0 sin sobrescritura.**
