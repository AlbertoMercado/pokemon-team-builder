#!/usr/bin/env bash
# Publish a prepared version (phase 2 of docs/05-operacion/versiones.md): merge its release PR,
# tag the merge commit and create the GitHub release with the CHANGELOG section as notes.
#
# Usage: scripts/publicar-version.sh X.Y.Z <PR number>
#
# It can be run again at any time: each step first checks whether it is already done, so after
# any failure it resumes where it stopped, and on a published version it only checks it. The
# tag always goes on the PR's merge commit, never on whatever the local branch is, and nothing
# is merged unless the PR is the release branch of that version with its CI passed.
set -euo pipefail

cd "$(dirname "$0")/.."

fail() {
    printf '\nERROR: %s\n' "$1" >&2
    printf 'Corrígelo y vuelve a ejecutar el script: retoma desde donde se paró.\n' >&2
    exit 1
}
step() { printf '\n==> %s\n' "$1"; }
done_() { printf '    ✔ %s\n' "$1"; }

[[ $# -eq 2 ]] || fail "uso: scripts/publicar-version.sh X.Y.Z <número de PR>"
version="$1"
pr="$2"
tag="v$version"
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "versión no válida: $version (se espera X.Y.Z)"
[[ $pr =~ ^[0-9]+$ ]] || fail "número de PR no válido: $pr"
command -v gh >/dev/null || fail "falta la CLI de GitHub (gh)"

step "PR #$pr"
read -r state branch < <(gh pr view "$pr" --json state,headRefName -q '.state + " " + .headRefName')
[[ $branch == "chore/release-$version" ]] ||
    fail "el PR #$pr es de la rama $branch, no de chore/release-$version"
case "$state" in
    MERGED)
        done_ "ya está fusionado"
        ;;
    OPEN)
        # Exit code 0 only if every check passed (1 if one failed, 8 if some are pending).
        gh pr checks "$pr" >/dev/null 2>&1 ||
            fail "la CI del PR #$pr no ha terminado o no ha pasado (gh pr checks $pr)"
        gh pr merge "$pr" --merge --delete-branch
        done_ "fusionado"
        ;;
    *)
        fail "el PR #$pr está $state"
        ;;
esac

merge_commit="$(gh pr view "$pr" --json mergeCommit -q .mergeCommit.oid)"
[[ -n $merge_commit ]] || fail "GitHub no da el commit de la fusión del PR #$pr"
git fetch --quiet --tags origin
git cat-file -e "$merge_commit^{commit}" 2>/dev/null ||
    fail "el commit de la fusión ${merge_commit:0:7} no está en local tras git fetch"
done_ "commit de la fusión: ${merge_commit:0:7}"

step "Versión y notas en el commit de la fusión"
found="$(git show "$merge_commit:pyproject.toml" | sed -n 's/^version = "\(.*\)"$/\1/p')"
[[ $found == "$version" ]] || fail "pyproject.toml dice la versión '$found', no $version"
done_ "pyproject.toml: $version"
# The same section as the documented awk: from the version's heading to the next section or the
# links at the end.
notes="$(git show "$merge_commit:CHANGELOG.md" | awk -v heading="## [$version]" '
    index($0, heading) == 1 { found = 1; next }
    /^## \[|^\[Sin publicar\]:/ { found = 0 }
    found')"
[[ -n ${notes//[[:space:]]/} ]] || fail "el CHANGELOG no tiene la sección [$version] o está vacía"
done_ "CHANGELOG: sección [$version], $(printf '%s\n' "$notes" | wc -l | tr -d ' ') líneas"

step "Etiqueta $tag"
if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    target="$(git rev-parse "$tag^{commit}")"
    [[ $target == "$merge_commit" ]] ||
        fail "la etiqueta $tag ya existe y apunta a ${target:0:7}, no a la fusión ${merge_commit:0:7}"
    done_ "ya existe sobre la fusión"
else
    git tag -a "$tag" -m "Versión $version" "$merge_commit"
    done_ "creada sobre ${merge_commit:0:7}"
fi
remote="$(git ls-remote origin "refs/tags/$tag^{}" | cut -f1)"
if [[ -z $remote ]]; then
    git push --quiet origin "refs/tags/$tag"
    done_ "subida a GitHub"
elif [[ $remote == "$merge_commit" ]]; then
    done_ "ya está en GitHub"
else
    fail "en GitHub, $tag apunta a ${remote:0:7}, no a la fusión ${merge_commit:0:7}"
fi

step "Release $tag"
if gh release view "$tag" >/dev/null 2>&1; then
    done_ "ya existe"
else
    notes_file="$(mktemp)"
    trap 'rm -f "$notes_file"' EXIT
    printf '%s\n' "$notes" >"$notes_file"
    gh release create "$tag" --verify-tag --title "$tag" --notes-file "$notes_file" --latest
    done_ "creada con la sección [$version] del CHANGELOG"
fi
latest="$(gh release view --json tagName -q .tagName)"
[[ $latest == "$tag" ]] || fail "la release más reciente (Latest) es $latest, no $tag"
done_ "es la más reciente (Latest)"

step "main local"
if [[ $(git branch --show-current) == main && -z $(git status --porcelain) ]]; then
    git pull --quiet --ff-only
    done_ "actualizada"
else
    done_ "sin tocar: no estás en main o hay cambios sin guardar (actualízala con git pull)"
fi

printf '\nVersión %s publicada: %s\n' "$version" "$(gh release view "$tag" --json url -q .url)"
printf 'Avisa a Claude para la comprobación final (fase 3).\n'
