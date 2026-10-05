# Operación

Instalación, despliegue, ingesta de datos y mantenimiento.

- [Entorno de desarrollo en macOS](entorno-desarrollo-macos.md): preparar un Mac y descargar el proyecto.
- [Ingesta de datos](ingesta.md): construir `reference.sqlite` con `uv run python -m ingest`,
  qué hace, el informe, qué pasa si falla o queda bloqueada y cómo consultar los datos
  cargados.
- [Arrancar la API](api.md): `uv run uvicorn api.main:app`, el directorio de datos, la base de
  datos del usuario y sus migraciones.
- [Web](web.md): la aplicación en un solo proceso (la API sirve la web compilada), la web en
  desarrollo con `npm run dev`, el cliente de la API, las comprobaciones y las pruebas de
  extremo a extremo.
- [Informes de carga](informes-carga/index.md): historial de las cargas bloqueadas y de las
  que las resuelven, registrado en git a mano.

!!! note "Pendiente"
    Una guía de mantenimiento: actualizar la aplicación y los datos y hacer copias de seguridad
    de `user.sqlite`. Mientras tanto, cada paso está en su página: [ingesta](ingesta.md),
    [migraciones](api.md#base-de-datos-del-usuario-usersqlite) y
    [compilar la web](web.md#un-solo-proceso).
