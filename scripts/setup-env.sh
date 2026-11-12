#!/usr/bin/env bash
# Generates backend/.env from the central secrets file + the project's local
# defaults template. Central secrets stay in one place (~/.secrets/acore.env)
# so you're not re-pasting the same API keys into every portfolio project.
set -euo pipefail

SECRETS="$HOME/.secrets/acore.env"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -f "$SECRETS" ]; then
  echo "Missing $SECRETS" >&2
  echo "Create it with OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL" >&2
  exit 1
fi

cat "$SECRETS" "$ROOT/backend/.env.local.example" > "$ROOT/backend/.env"
echo "Wrote $ROOT/backend/.env"
