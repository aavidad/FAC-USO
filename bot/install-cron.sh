#!/usr/bin/env bash
# Instala o retira solo la entrada cron de FAC-USO del usuario actual.
set -euo pipefail
umask 077

usage() { printf 'Uso: %s [--local | --remove]\n' "$0" >&2; exit 2; }
[[ $# -le 1 ]] || usage
mode=install
if [[ $# -eq 1 ]]; then
  case $1 in
    --local) mode=local ;;
    --remove) mode=remove ;;
    *) usage ;;
  esac
fi
command -v crontab >/dev/null || { printf 'Falta crontab.\n' >&2; exit 1; }

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
runtime="$root/.runtime"
if [[ $mode != remove ]]; then
  env_file="$runtime/cron.env"
  if [[ ! -f $env_file || -L $env_file || $(stat -c '%a:%u' -- "$env_file") != "600:$(id -u)" ]]; then
    printf 'Prepara .runtime/cron.env con propietario actual y modo 600.\n' >&2
    exit 1
  fi
fi

current=$(mktemp)
updated=$(mktemp)
errors=$(mktemp)
trap 'rm -f -- "$current" "$updated" "$errors"' EXIT
if ! LC_ALL=C crontab -l >"$current" 2>"$errors"; then
  if [[ -s $current || $(<"$errors") != *'no crontab'* ]]; then
    printf 'No se pudo leer el crontab actual.\n' >&2
    exit 1
  fi
fi
while IFS= read -r line || [[ -n $line ]]; do
  [[ $line =~ [[:space:]]#[[:space:]]FACUSO_HOURLY$ ]] || printf '%s\n' "$line" >>"$updated"
done <"$current"
if [[ $mode != remove ]]; then
  runner="$root/bot/run-hourly.sh"
  [[ $runner != *%* && $runner != *$'\n'* ]] || { printf 'Ruta incompatible con cron.\n' >&2; exit 1; }
  printf -v runner_escaped '%q' "$runner"
  printf '0 * * * * /bin/bash %s' "$runner_escaped" >>"$updated"
  [[ $mode != local ]] || printf ' --local' >>"$updated"
  printf ' # FACUSO_HOURLY\n' >>"$updated"
fi
if ! cmp -s -- "$current" "$updated"; then
  crontab "$updated"
fi
printf 'Cron FAC-USO: %s.\n' "$mode"
