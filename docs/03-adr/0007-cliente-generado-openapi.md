# 0007 · Cliente del frontend generado desde OpenAPI

- **Estado**: Aceptado
- **Fecha**: 2026-10-03
- **Decisores**: Alberto Mercado

## Contexto

El frontend (TypeScript) y la API (Python) comparten los esquemas de petición y respuesta.
Mantenerlos a mano en los dos lados lleva a que se desincronicen sin que nadie lo note.
FastAPI publica el contrato como OpenAPI de forma automática.

## Decisión

Generamos los tipos y el cliente TypeScript a partir del OpenAPI de la API con
**openapi-typescript** (y `openapi-fetch` para las llamadas). El estado que viene del servidor
se gestiona con **TanStack Query**. Cuando cambia la API, se vuelve a generar el cliente; CI
comprueba que el cliente generado está al día.

## Alternativas consideradas

### Tipos escritos a mano

- ✅ Sin paso de generación.
- ❌ Se desincronizan con la API.

### Generadores completos (p. ej., OpenAPI Generator)

- ✅ Generan servicios enteros.
- ❌ Más código generado y más pesado del necesario.

## Consecuencias

### Positivas

- Los errores de contrato aparecen al compilar el frontend.

### Negativas / riesgos

- Un paso más en el flujo de desarrollo y en CI.

### Acciones derivadas

- [x] Añadir la generación del cliente y su comprobación al job de CI del frontend
  (job **Web**; [web en desarrollo](../05-operacion/web.md#ci)).

## Referencias

- [API](../02-ddt/api.md)
- [openapi-typescript](https://openapi-ts.dev/)
