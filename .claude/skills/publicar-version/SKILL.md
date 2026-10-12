---
name: publicar-version
description: Publica una versión nueva de pokemon-team-builder (SemVer, CHANGELOG, etiqueta vX.Y.Z y release de GitHub). Úsala cuando el usuario pida publicar, sacar, lanzar o preparar una versión o release, o cuando diga que ya ha ejecutado los comandos de publicación y haya que comprobarla.
---

# Publicar una versión

Sigue el protocolo de [publicar una versión](../../../docs/05-operacion/versiones.md#publicar-una-version)
(`docs/05-operacion/versiones.md`, sección «Publicar una versión»). Lee esa sección completa
antes de empezar: es la única fuente del procedimiento.

Reglas que no se saltan:

- Si el usuario dice que ya ha ejecutado el script o los comandos, ve directamente a la fase 3
  (Comprobar).
- Si el usuario no da el número de versión, propónlo con la numeración y **espera su
  confirmación**.
- **No** ejecutes `scripts/publicar-version.sh`, `gh pr merge`, `git tag`, `git push` de
  etiquetas ni `gh release create`: dale el comando de la fase 2,
  `scripts/publicar-version.sh X.Y.Z <n>`, con la versión y el PR sustituidos. Nunca le des
  cadenas de comandos con `&&`: con el `!` de zsh se rompen.
