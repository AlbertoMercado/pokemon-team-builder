# Operación

Instalación, despliegue, ingesta de datos y mantenimiento.

- [Entorno de desarrollo en macOS](entorno-desarrollo-macos.md): preparar un Mac y descargar el proyecto.
- [Ingesta de datos](ingesta.md): construir `reference.sqlite` con `uv run python -m ingest`,
  qué hace, el informe, qué pasa si falla o queda bloqueada y cómo consultar los datos
  cargados.
- [Arrancar la API](api.md): `uv run uvicorn api.main:app`, el directorio de datos, la base de
  datos del usuario y sus migraciones.
- [Informes de carga](informes-carga/index.md): historial de las cargas bloqueadas y de las
  que las resuelven, registrado en git a mano.

!!! note "Pendiente"
    Despliegue y mantenimiento están en construcción.
