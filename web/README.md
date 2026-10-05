# web/

**Qué es**: la interfaz de la aplicación: una aplicación de una sola página con React, Vite,
TypeScript (strict) y Tailwind ([ADR-0001](../docs/03-adr/0001-stack-tecnologico.md)).
Completa: las 8 fases del [plan](../docs/02-ddt/plan-web.md#fases). La API sirve su compilación
(`npm run build` → `dist/`) en un solo proceso. Pantallas: **Inicio**,
**Catálogo**, **Ficha**, **Favoritos**, **Reglas**, **Nuevo juego**, **Revisión de datos**,
**Resultado** con el **selector del equipo**, y ***Hall of Fame***.

**Por qué existe**: es la forma de usar la aplicación para el usuario; muestra lo que calcula
la [API](../docs/02-ddt/api.md) y no implementa reglas de negocio.

**Qué hace**: llama a la API con un cliente tipado generado desde su OpenAPI
([ADR-0007](../docs/03-adr/0007-cliente-generado-openapi.md)) y guarda el estado del servidor
con TanStack Query.

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `src/main.tsx`, `src/App.tsx` | Arranque, `QueryClient`, router y rutas. |
| `src/api/schema.d.ts` | Contrato generado con `npm run api:generate`. **No se edita a mano.** |
| `src/api/client.ts` | Cliente de `openapi-fetch`, `ApiError` (respuesta de error con su `detail`), `NetworkError` (la API no responde) y `unwrap`. |
| `src/api/queryClient.ts` | `QueryClient`: solo reintenta los fallos de conexión. |
| `src/api/queries/` | Una consulta o mutación por recurso, con sus claves en `keys.ts`. La generación es una consulta (un cálculo sin estado): se repite al cambiar los favoritos o las confirmaciones. |
| `src/api/types.ts` | Nombres cortos de los esquemas del contrato. |
| `src/components/` | `Layout` (navegación), `ApiStatusBanner` (aviso de `503` o sin API), `ErrorMessage`, `TypeBadge`, `PokemonName`, `FavoriteButton` (la estrella, que invalida el catálogo, los favoritos y las revisiones), `FavoriteHint` (qué es un favorito, RN-09) `PokemonPicker` (buscador para elegir un Pokémon), `TeamEditor` (editar un equipo en orden, de hasta 6, con el buscador) y `TeamSelector` (elegir un equipo del resultado, comprobarlo y registrarlo en el *Hall of Fame*). |
| `src/pages/` | Una por pantalla. |
| `src/lib/` | Funciones puras: `format.ts` (fechas, números de la Pokédex y *commits*), `generation.ts` (textos del resultado: motivos, descartes y reglas de presencia), `docs.ts` (enlaces a la documentación en GitHub), `types.ts` (nombres y colores de los 18 tipos), `evolution.ts` (métodos de evolución en texto) y `commands.ts` (comandos que la web indica). |
| `src/test/` | Configuración de Vitest, `renderApp` y la API simulada con MSW, que guarda los favoritos, las reglas (`rules.ts`, el catálogo real), las confirmaciones de la revisión y el *Hall of Fame* como estado y genera un resultado completo o incompleto según los favoritos. |

Los tests están junto a lo que prueban (`*.test.ts(x)`). Las pruebas de extremo a extremo están
en `e2e/` (Playwright, `playwright.config.ts`) y van contra la API real, que arranca
`tests/e2e/serve.py`.

Cómo se arranca y se comprueba: [Operación](../docs/05-operacion/web.md). Cómo se usa:
[manual de usuario](../docs/04-manual-usuario/web.md).

**Restricciones**: no decide qué equipos son válidos ni los ordena; los tipos de la API salen
siempre de `schema.d.ts`.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
