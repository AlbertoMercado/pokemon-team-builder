# scripts/

**Qué es**: scripts de terminal para usar la aplicación en el propio ordenador y para publicar
sus versiones.

**Por qué existe**: reúne en un comando los pasos que hay que repetir al instalar o actualizar,
para no olvidar ninguno ([versiones](../docs/05-operacion/versiones.md#actualizar-a-una-version-nueva)).

**Contenido** (el detalle, en el comentario de cabecera de cada script):

| Ruta | Qué es |
|------|--------|
| `start.sh` | Copia `user.sqlite`, instala las dependencias, carga los datos, compila la web y arranca la aplicación. |
| `publicar-version.sh` | Fusiona el PR de una versión, la etiqueta y crea su *release*; se puede repetir ([publicar una versión](../docs/05-operacion/versiones.md#2-publicar-usuario)). |

**Más información**: cómo se usa en el [manual de la web](../docs/04-manual-usuario/web.md#abrir-la-web);
el resto de comandos, en [comandos y CI](../docs/05-operacion/comandos.md).
