# web/

**Qué es**: la interfaz de la aplicación: una aplicación de una sola página con React, Vite,
TypeScript (strict) y Tailwind ([ADR-0001](../docs/03-adr/0001-stack-tecnologico.md)).
Implementada la fase 1 del [plan](../docs/02-ddt/plan-web.md#fases): proyecto, cliente de la
API, rutas, navegación, avisos de API no disponible e **Inicio**.

**Por qué existe**: es la forma de usar la aplicación para el usuario; muestra lo que calcula
la [API](../docs/02-ddt/api.md) y no implementa reglas de negocio.

**Qué hace**: llama a la API con un cliente tipado generado desde su OpenAPI
([ADR-0007](../docs/03-adr/0007-cliente-generado-openapi.md)) y guarda el estado del servidor
con TanStack Query.

**Contenido**:

| Ruta | Qué hace |
|------|----------|
| `src/main.tsx`, `src/App.tsx` | Arranque, `QueryClient`, router y rutas. Las pantallas de fases posteriores responden con `PendingPage`. |
| `src/api/schema.d.ts` | Contrato generado con `npm run api:generate`. **No se edita a mano.** |
| `src/api/client.ts` | Cliente de `openapi-fetch`, `ApiError` (respuesta de error con su `detail`), `NetworkError` (la API no responde) y `unwrap`. |
| `src/api/queryClient.ts` | `QueryClient`: solo reintenta los fallos de conexión. |
| `src/api/queries/` | Una consulta o mutación por recurso, con sus claves en `keys.ts`. |
| `src/api/types.ts` | Nombres cortos de los esquemas del contrato. |
| `src/components/` | `Layout` (navegación), `ApiStatusBanner` (aviso de `503` o sin API) y `ErrorMessage`. |
| `src/pages/` | Una por pantalla. |
| `src/lib/` | Funciones puras: fechas en español y comandos que la web indica. |
| `src/test/` | Configuración de Vitest y la API simulada con MSW. |

Los tests están junto a lo que prueban (`*.test.ts(x)`).

Cómo se arranca y se comprueba: [Operación](../docs/05-operacion/web.md). Cómo se usa:
[manual de usuario](../docs/04-manual-usuario/web.md).

**Restricciones**: no decide qué equipos son válidos ni los ordena; los tipos de la API salen
siempre de `schema.d.ts`.

Más detalle en [Estructura del código](../docs/02-ddt/estructura-codigo.md).
