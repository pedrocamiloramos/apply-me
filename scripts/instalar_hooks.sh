#!/usr/bin/env bash
# Copia os hooks de scripts/hooks/ para .git/hooks/ (idempotente).
set -euo pipefail
raiz="$(git rev-parse --show-toplevel)"
for hook in "$raiz"/scripts/hooks/*; do
  destino="$raiz/.git/hooks/$(basename "$hook")"
  cp "$hook" "$destino"
  chmod +x "$destino"
  echo "instalado: $(basename "$hook")"
done
