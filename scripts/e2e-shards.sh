#!/usr/bin/env bash
# Authoritative spec -> CI shard assignment. Single source of truth used by
# both the e2e shard step and the fail-safe coverage check in CI.
#
# Buckets (each spec must land in exactly one):
#   localization -> e2e-1
#   rest         -> e2e-2 / e2e-3 (further split by Playwright --shard)
#   qa           -> qa-1 / qa-2 / qa-3 (playwright.practice.config.js)
#   smoke        -> smoke-1 / smoke-2 / smoke-3 (playwright.local.config.js)
#   manual       -> real-provider.spec.js (playwright.real.config.js; live key)
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

all_specs() {
  find frontend/e2e -maxdepth 1 -name '*.spec.js' -printf '%f\n' | sort -u
}
config_specs() {
  grep -oE "'[A-Za-z0-9_-]+\.spec\.js'" "$1" | tr -d "'" | sort -u
}
qa_specs() { config_specs frontend/playwright.practice.config.js; }
smoke_specs() { config_specs frontend/playwright.local.config.js; }
manual_specs() { config_specs frontend/playwright.real.config.js; }
localization_spec() { echo 'localization.spec.js'; }
e2e_rest() {
  comm -23 <(all_specs) <({ localization_spec; qa_specs; smoke_specs; manual_specs; } | sort -u)
}
with_prefix() { sed 's#^#e2e/#'; }

case "${1:-}" in
  localization) localization_spec | with_prefix ;;
  rest) e2e_rest | with_prefix ;;
  check)
    assigned="$({ localization_spec; e2e_rest; qa_specs; smoke_specs; manual_specs; } | sort)"
    dup="$(printf '%s\n' "$assigned" | uniq -d)"
    missing="$(comm -23 <(all_specs) <(printf '%s\n' "$assigned" | sort -u))"
    if [ -n "$dup" ] || [ -n "$missing" ]; then
      echo "spec assignment invalid: duplicated=[$dup] unassigned=[$missing]" >&2
      exit 1
    fi
    echo "all $(all_specs | wc -l) e2e specs assigned exactly once"
    printf 'localization=%s rest=%s qa=%s smoke=%s manual=%s\n' \
      "$(localization_spec | wc -l)" "$(e2e_rest | wc -l)" \
      "$(qa_specs | wc -l)" "$(smoke_specs | wc -l)" "$(manual_specs | wc -l)"
    ;;
  *)
    echo "usage: $0 {check|localization|rest}" >&2
    exit 2
    ;;
esac
