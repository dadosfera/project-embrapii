#!/usr/bin/env bash
# Túnel para o Postgres da UFMG: localhost:5433 -> 150.164.2.13:5432 via bastion.
# Requer SSH_USER, SSH_HOST e SSH_PASSWORD no Dashboard/.env. Uso: scripts/tunnel.sh (Ctrl+C encerra).
set -euo pipefail
cd "$(dirname "$0")/.."

env_var() {
  local key="$1"
  { grep -E "^${key}=" .env || true; } | tail -n1 | cut -d'=' -f2- | sed -e 's/\r$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

SSH_HOST="$(env_var SSH_HOST)"
SSH_USER="$(env_var SSH_USER)"
SSH_PASSWORD="$(env_var SSH_PASSWORD)"

: "${SSH_HOST:?missing in .env}"
: "${SSH_USER:?missing in .env}"
: "${SSH_PASSWORD:?missing in .env}"

export SSH_HOST SSH_USER
export SSHPW="$SSH_PASSWORD"
unset SSH_PASSWORD

exec expect -c '
  set timeout 30
  log_user 0
  set pw $env(SSHPW)
  unset env(SSHPW)
  spawn ssh -N -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -L 5433:150.164.2.13:5432 $env(SSH_USER)@$env(SSH_HOST)
  expect {
    -re "(?i)password:" { send -- "$pw\r" }
    timeout { puts "NO PASSWORD PROMPT"; exit 3 }
    eof { puts "SSH EXITED: $expect_out(buffer)"; catch wait r; exit [lindex $r 3] }
  }
  log_user 1
  expect {
    -re "(?i)denied|password:" { puts "AUTH FAILED"; exit 2 }
    timeout { puts "TUNNEL UP on :5433" }
    eof { puts "SSH EXITED"; catch wait r; exit [lindex $r 3] }
  }
  set timeout -1
  expect eof
  catch wait r
  exit [lindex $r 3]'
