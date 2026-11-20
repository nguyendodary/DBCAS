#!/usr/bin/env bash
# Collect only synthetic smoke-stack diagnostics while its containers still exist.
set -eu

output_dir=${1:?Usage: collect_seed_diagnostics.sh OUTPUT_DIR [COMPOSE_OPTIONS...]}
shift
compose=(docker compose "$@")
mkdir -p "$output_dir"

capture() {
  local file=$1
  shift
  "$@" > "$output_dir/$file" 2>&1 ||
    printf '\nDiagnostic command exited %s.\n' "$?" >> "$output_dir/$file"
}

capture compose-ps.log "${compose[@]}" ps --all init db

for service in init db; do
  container=$("${compose[@]}" ps --all --quiet "$service" 2>"$output_dir/$service-lookup.log") || container=
  if [[ -z "$container" ]]; then
    printf 'No container ID available for %s. See the lookup log.\n' "$service" >> "$output_dir/$service-lookup.log"
    continue
  fi
  if [[ "$service" == init ]]; then
    capture init-state.json docker inspect --format '{{json .State}}' "$container"
  else
    capture db-health.json docker inspect --format '{{json .State.Health}}' "$container"
  fi
done

for service in init db; do
  capture "$service.log" "${compose[@]}" logs --no-color --timestamps "$service"
done
