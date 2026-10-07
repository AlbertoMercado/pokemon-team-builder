# web/

**Qué es**: la interfaz de la aplicación: una aplicación de una sola página con React, Vite,
TypeScript (strict) y Tailwind ([ADR-0001](../docs/03-adr/0001-stack-tecnologico.md)). La API
sirve su compilación (`dist/`) en un solo proceso.

**Por qué existe**: es la forma de usar la aplicación para el usuario; muestra lo que calcula
la [API](../docs/02-ddt/api.md) y no implementa reglas de negocio.

**Qué hace**: llama a la API con un cliente tipado generado desde su OpenAPI
([ADR-0007](../docs/03-adr/0007-cliente-generado-openapi.md)) y guarda el estado del servidor
con TanStack Query.

**Contenido** (el detalle, en el comentario de cabecera de cada fichero):

| Ruta | Qué hace |
|------|----------|
| `src/main.tsx`, `src/App.tsx` | Arranque, `QueryClient`, router y rutas. |
| `src/api/schema.d.ts` | Contrato generado con `npm run api:generate`. **No se edita a mano.** |
| `src/api/client.ts` | Cliente de `openapi-fetch`, `ApiError` (respuesta de error con su `detail`), `NetworkError` (la API no responde) y `unwrap`. |
| `src/api/queryClient.ts` | `QueryClient`: solo reintenta los fallos de conexión. |
| `src/api/queries/` | Una consulta o mutación por recurso, con sus claves en `keys.ts`. La generación es una consulta (un cálculo sin estado): se repite al cambiar los favoritos o las confirmaciones. |
| `src/api/types.ts` | Nombres cortos de los esquemas del contrato. |
| `src/components/` | Componentes compartidos: navegación y pie, filas e imágenes de los Pokémon, portadas, la estrella de favorito, el buscador, el editor y el selector de equipos… |
| `src/pages/` | Una por pantalla. |
| `src/lib/` | Funciones puras: formatos, textos del resultado, tipos, métodos de evolución, enlaces a la documentación y comandos. |
| `src/test/` | Configuración de Vitest, `renderApp` y la API simulada con MSW. |

Los tests están junto a lo que prueban (`*.test.ts(x)`). Las pruebas de extremo a extremo están
en `e2e/` (Playwright, `playwright.config.ts`) y van contra la API real, que arranca
`tests/e2e/serve.py`.

**Más información**: cómo se arranca y se prueba en [Operación](../docs/05-operacion/web.md);
cómo se usa en el [manual](../docs/04-manual-usuario/web.md); los comandos en
[comandos y CI](../docs/05-operacion/comandos.md#web-en-web).
