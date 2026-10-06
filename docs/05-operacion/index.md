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
- [Puesta en producción](puesta-en-produccion.md): tener la aplicación siempre disponible con
  coste 0 (opciones evaluadas, recomendación, instalación en una VM gratuita con acceso por
  Tailscale, copias de seguridad, actualización y supervisión).
- [Versiones](versiones.md): cómo se numeran (SemVer desde la 1.0.0), cómo se publica una
  versión y cómo actualizar sin perder `user.sqlite`.
- [Dependencias](dependencias.md): revisar qué dependencias están desactualizadas,
  actualizarlas (Python, web, hooks de pre-commit y acciones de la CI) y los casos especiales.
- [Informes de carga](informes-carga/index.md): historial de las cargas bloqueadas y de las
  que las resuelven, registrado en git a mano.

!!! note "Pendiente"
    Elegir la opción de despliegue ([ADR-0009](../03-adr/0009-despliegue-vm-gratuita-tailscale.md),
    *Propuesto*) y probar la [puesta en producción](puesta-en-produccion.md).
