# Usar la web

La web es la forma de usar la aplicación: desde ella eliges tus favoritos y tus reglas,
generas el equipo para un juego y registras tu *Hall of Fame*.

!!! note "Disponible por ahora"
    La pantalla de **Inicio** y la navegación. El resto de pantallas (catálogo, favoritos,
    reglas, nuevo juego y *Hall of Fame*) se añadirán en las siguientes versiones; mientras
    tanto, muestran «Esta pantalla todavía no está disponible». Lo que todavía no hace la web
    se puede hacer con la [API](api.md).

## Antes de empezar

- Haber cargado los datos al menos una vez ([cargar los datos](cargar-datos.md)).
- Tener instaladas las dependencias de la web (`cd web && npm ci`;
  [detalle](../05-operacion/web.md#instalar)).

## Abrir la web

Por ahora, la web y la API se arrancan por separado, cada una en su terminal, desde la raíz
del proyecto:

```bash
uv run uvicorn api.main:app --reload
```

```bash
cd web && npm run dev
```

Abre `http://localhost:5173` en el navegador. Para pararlas, `Ctrl+C` en cada terminal.

## Navegar

La barra de arriba lleva a cada sección: **Catálogo**, **Favoritos**, **Reglas**,
**Nuevo juego** y **Hall of Fame**. La sección en la que estás aparece subrayada. El nombre
de la aplicación, a la izquierda, vuelve al Inicio.

Cada pantalla tiene su propia dirección, así que puedes recargar la página, volver atrás con
el navegador o guardar un enlace.

## Inicio

Resume tu situación:

| Apartado | Qué muestra |
|----------|-------------|
| **Nuevo juego** | El acceso para elegir un juego, revisar sus datos y generar el equipo. |
| **Favoritos** | Cuántos favoritos tienes, con un enlace a la lista. Si no tienes ninguno, un enlace al catálogo para añadirlos. |
| **Último juego completado** | El último juego de tu *Hall of Fame*, con su fecha y su equipo. |
| **Datos** | La versión de la aplicación, cuándo se cargaron los datos, cuántos juegos hay cargados (pasa el ratón por encima para ver cuáles) y el *commit* de PokeAPI usado. |

Si acabas de volver a cargar los datos y la fecha de **Datos** no cambia, reinicia la API: sigue
trabajando con la carga anterior hasta que la reinicies.

## Avisos

| Aviso | Qué significa | Qué hacer |
|-------|---------------|-----------|
| **No hay datos cargados** | La API funciona, pero todavía no se han cargado los datos de los juegos. | Ejecuta la carga con `uv run python -m ingest` ([cargar los datos](cargar-datos.md)) y reinicia la API. |
| **La API no responde** | La web no puede comunicarse con la API. | Arráncala con `uv run uvicorn api.main:app --reload` y recarga la página. |

Cuando una parte de una pantalla no se puede mostrar por otro motivo, el mensaje de error
aparece en su lugar y el resto de la pantalla sigue funcionando.
