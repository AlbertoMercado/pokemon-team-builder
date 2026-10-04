# Páginas de WikiDex para los tests

**Qué es**: páginas reales de WikiDex en el formato de la caché de la ingesta (un JSON por
página, con su título, su revisión y su wikitexto). Las de entrenadores están recortadas a su
sección de Rojo Fuego y Verde Hoja.

**Por qué existe**: los tests de la ingesta nunca usan la red. Con wikitexto real, los tests
comprueban el procesado de las plantillas `{{Equipo}}` con la estructura que tienen de verdad,
incluidos los casos difíciles.

| Página | Revisión | Caso |
|--------|----------|------|
| Brock | 3562807 | Un solo equipo, sin rótulos. |
| Giovanni | 3530484 | Tres combates en la misma sección, cada uno con su rótulo (`; En Silph S.A.`); en la carga solo se usa el de líder de gimnasio (CA-39). |
| Azul (personaje) | 3557514 | Varios combates con rótulo; el de Campeón con tres variantes según el inicial dentro de `<tabber>`. |
| Bruno | 2451940 | Página de desambiguación, completa. |

**Licencia y atribución**: el contenido procede de [WikiDex](https://www.wikidex.net), con
licencia [CC BY-NC-SA 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/deed.es). Los
autores son los editores de cada página, que figuran en su historial
(`https://www.wikidex.net/index.php?title=<página>&action=history`). Se usa sin ánimo de lucro
y recortado al mínimo necesario para los tests.

**Cómo se regenera**:

1. Ejecutar una carga real para tener las páginas en la caché:
   `uv run python -m ingest --data-dir /tmp/datos`.
2. Si falta la página de desambiguación de Bruno en la caché, descargarla (no la usa la carga).
3. Generar el extracto:
   `PYTHONPATH=. uv run python tests/ingest/fixtures/wikidex/extract_wikidex.py /tmp/datos/cache/wikidex`.
