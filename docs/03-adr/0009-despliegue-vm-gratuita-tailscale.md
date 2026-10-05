# 0009 · Despliegue en una máquina virtual gratuita con acceso privado por Tailscale

- **Estado**: Propuesto
- **Fecha**: 2026-10-05
- **Decisores**: Alberto Mercado

## Contexto

Hasta ahora la aplicación se arranca en el ordenador del usuario
([un solo proceso](../05-operacion/web.md#un-solo-proceso)). Se quiere usar sin arrancarla en
local, desde cualquier dispositivo, con estas restricciones:

- **Coste 0**: es una aplicación personal y sin ánimo de lucro.
- **Disco persistente**: `user.sqlite` guarda los favoritos, las reglas, las confirmaciones y el
  *Hall of Fame*, y no se puede regenerar ([ADR-0003](0003-dos-bases-de-datos-sqlite.md)). Un
  disco que se borra al reiniciar o al desplegar pierde esos datos.
- **Sin autenticación**: la aplicación es de un solo usuario y no tiene cuentas
  ([alcance](../01-ddf/index.md#alcance)). Publicada en Internet, cualquiera podría cambiar los
  datos.
- **Un solo proceso**: `uvicorn` sirve la API y la web compilada; necesita poca memoria y CPU, y
  unos pocos MB de disco.

Los planes gratuitos se revisaron el 2026-10-05; las condiciones y referencias están en la
[puesta en producción](../05-operacion/puesta-en-produccion.md#opciones-evaluadas).

## Decisión

Desplegamos la aplicación en una **máquina virtual *Always Free* de Oracle Cloud** (una
instancia Ampere A1 en la región de casa más cercana, como Madrid), con el disco de arranque
gratuito para el código y los datos, y la ejecutamos como un servicio de `systemd`.

El acceso es **privado por [Tailscale](https://tailscale.com/)** (plan *Personal*, gratuito): la
aplicación escucha solo en `127.0.0.1` y `tailscale serve` la publica con HTTPS dentro de la red
privada del usuario. No se abre ningún puerto a Internet y no hace falta autenticación ni
dominio.

Para evitar que Oracle reclame la instancia por estar inactiva, la cuenta se pasa a *Pay As You
Go* sin salir de los recursos gratuitos, con un presupuesto y una alerta de gasto.

## Alternativas consideradas

### Google Cloud: máquina virtual e2-micro *Always Free*

- ✅ Sin política de reclamación por inactividad; 30 GB de disco persistente.
- ❌ Solo en regiones de EE. UU. (más latencia), 1 GB de memoria y 1 GB de salida de datos al
  mes en el plan gratuito.
- ❌ También exige una cuenta de facturación con tarjeta.
- Es la **alternativa** si Oracle no tiene capacidad o se descarta.

### Un equipo propio encendido (Raspberry Pi, un ordenador antiguo)

- ✅ Sin cuentas en la nube ni tarjeta; los datos se quedan en casa. Mismo acceso por Tailscale.
- ❌ Solo es coste 0 si ya se tiene el equipo; consume electricidad y depende de la conexión de
  casa.

### Plataformas gratuitas de aplicaciones (Render, Fly.io, Koyeb, Hugging Face Spaces)

- ✅ Despliegue sencillo desde el repositorio.
- ❌ Ninguna ofrece hoy disco persistente gratis: el sistema de ficheros se pierde al reiniciar o
  dormir, y con él `user.sqlite`. Fly.io y Koyeb ya no tienen plan gratuito para cuentas
  nuevas.

### Servicios sin servidor (Cloud Run, Vercel, Cloudflare Workers)

- ❌ Sistema de ficheros efímero: obligarían a sustituir SQLite por otra base de datos o a
  sincronizarla con un almacenamiento externo, contra
  [ADR-0003](0003-dos-bases-de-datos-sqlite.md).

### Publicar en Internet con Cloudflare Tunnel y Cloudflare Access

- ✅ Acceso desde cualquier navegador, sin instalar nada, con inicio de sesión de Access (gratis
  hasta 50 usuarios).
- ❌ Exige un dominio gestionado por Cloudflare, que tiene un coste anual. Se puede añadir más
  adelante sin cambiar el resto.

## Consecuencias

### Positivas

- Coste 0 y la aplicación siempre disponible desde los dispositivos del usuario.
- Sin cambios en el código: la misma aplicación de un solo proceso.
- Nada expuesto a Internet: la falta de autenticación no es un riesgo.

### Negativas / riesgos

- Oracle exige tarjeta para el registro y, con *Pay As You Go*, un error de configuración podría
  generar gastos: hay que usar solo recursos *Always Free* y tener la alerta de presupuesto.
- La capacidad de Ampere A1 en las regiones más usadas puede estar agotada; la región de casa no
  se puede cambiar después.
- Los límites gratuitos pueden cambiar (Oracle redujo los de A1 en 2026); hay que revisarlos de
  vez en cuando.
- Cada dispositivo necesita la aplicación de Tailscale.
- El mantenimiento (actualizaciones del sistema, copias de seguridad) es responsabilidad del
  usuario.

### Acciones derivadas

- [ ] Elegir la opción y aceptar o cambiar este ADR.
- [ ] Seguir la [puesta en producción](../05-operacion/puesta-en-produccion.md) y probarla.
- [ ] Automatizar la copia de seguridad diaria de `user.sqlite`.

## Referencias

- [Puesta en producción](../05-operacion/puesta-en-produccion.md)
- [Oracle Cloud: recursos *Always Free*](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [Tailscale: `tailscale serve`](https://tailscale.com/kb/1242/tailscale-serve)
