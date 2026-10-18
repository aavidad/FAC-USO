#!/usr/bin/env bash
# Una pasada horaria: BOP de Almería y después los ocho bot provinciales.
set -u -o pipefail
umask 077

usage() { printf 'Uso: %s [--local | --production]\n' "$0" >&2; exit 2; }
[[ $# -le 1 ]] || usage
local_mode=false
production_mode=false
if [[ $# -eq 1 ]]; then
  case $1 in
    --local) local_mode=true ;;
    --production) production_mode=true ;;
    *) usage ;;
  esac
fi

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P) || exit 1
runtime="$root/.runtime"
env_file="$runtime/cron.env"
if [[ ! -d $runtime || -L $runtime || ! -f $env_file || -L $env_file ]]; then
  printf 'Falta .runtime/cron.env o no es un archivo regular.\n' >&2
  exit 1
fi
if [[ $(stat -c '%a:%u' -- "$env_file") != "600:$(id -u)" ]]; then
  printf '.runtime/cron.env debe pertenecer al usuario y tener modo 600.\n' >&2
  exit 1
fi
for tool in docker timeout flock tail stat date; do
  command -v "$tool" >/dev/null || { printf 'Falta %s.\n' "$tool" >&2; exit 1; }
done

mkdir -p -- "$runtime/hourly-logs" "$runtime/hourly-state" || exit 1
chmod 700 -- "$runtime/hourly-logs" "$runtime/hourly-state" || exit 1
exec {lock_fd}>"$runtime/hourly.lock" || exit 1
if ! flock -n "$lock_fd"; then
  printf 'Ya hay una pasada horaria en curso.\n' >&2
  exit 0
fi

bot_compose=(docker compose --env-file "$env_file" -f "$root/bot/compose.yaml")
if $local_mode; then
  bot_compose+=(-f "$root/bot/compose.local.yaml")
fi
browser_compose=(docker compose --env-file "$env_file" -f "$root/bot/compose.almeria-browser.yaml")
if $production_mode; then
  bot_compose+=(-p facuso-bots)
  browser_compose+=(-f "$root/docker/production/collector.yaml")
fi

rotate_log() {
  local log=$1
  if [[ -f $log && $(stat -c %s -- "$log") -ge 524288 ]]; then
    [[ ! -f $log.2 ]] || mv -f -- "$log.2" "$log.3"
    [[ ! -f $log.1 ]] || mv -f -- "$log.1" "$log.2"
    mv -f -- "$log" "$log.1"
  fi
}

write_state() {
  local name=$1 started=$2 finished=$3 status=$4 code=$5
  local target="$runtime/hourly-state/$name" temp="$runtime/hourly-state/.$name.$$"
  printf 'started_at=%s\nfinished_at=%s\nstatus=%s\nexit_code=%s\n' \
    "$started" "$finished" "$status" "$code" > "$temp"
  mv -f -- "$temp" "$target"
}

run_job() {
  local name=$1 seconds=$2 compose_name=$3 service=$4
  local started finished code status log output container
  started=$(date -u +%FT%TZ)
  log="$runtime/hourly-logs/$name.log"
  output="$runtime/hourly-logs/.$name.$$.out"
  container="facuso-hourly-${name}-$$"
  if [[ $compose_name == browser ]]; then
    if timeout --signal=TERM --kill-after=10s "${seconds}s" \
      "${browser_compose[@]}" --profile bots run --rm -T --no-deps \
      --name "$container" "$service" --once >"$output" 2>&1; then
      code=0
    else
      code=$?
    fi
  else
    if timeout --signal=TERM --kill-after=10s "${seconds}s" \
      "${bot_compose[@]}" --profile bots run --rm -T --no-deps \
      --name "$container" "$service" >"$output" 2>&1; then
      code=0
    else
      code=$?
    fi
  fi
  if (( code != 0 )); then
    timeout --signal=TERM --kill-after=5s 30s docker rm -f "$container" >/dev/null 2>&1 || :
  fi
  finished=$(date -u +%FT%TZ)
  rotate_log "$log"
  {
    printf '[%s] inicio=%s fin=%s salida=%s\n' "$name" "$started" "$finished" "$code"
    tail -c 131072 -- "$output"
    printf '\n'
  } >>"$log"
  rm -f -- "$output"
  status=ok
  (( code == 0 )) || status=error
  write_state "$name" "$started" "$finished" "$status" "$code"
  return "$code"
}

failed=0
run_job almeria_browser 600 browser almeria_browser || failed=1
for province in almeria cadiz cordoba granada huelva jaen malaga sevilla; do
  run_job "$province" 350 bot "$province" || failed=1
done
exit "$failed"
