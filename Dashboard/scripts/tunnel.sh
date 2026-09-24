#!/usr/bin/env bash
# Túnel para o Postgres da UFMG: localhost:5433 -> 150.164.2.13:5432 via bastion.
# Requer SSH_USER, SSH_HOST e SSH_PASSWORD no Dashboard/.env. Uso: scripts/tunnel.sh (Ctrl+C encerra).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
export SSHPW="$SSH_PASSWORD"
exec expect -c '
  set timeout 30
  log_user 0
  spawn ssh -N -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes \
    -L 5433:150.164.2.13:5432 $env(SSH_USER)@$env(SSH_HOST)
  expect -re "(?i)password:" { send "$env(SSHPW)\r" }
  expect { -re "(?i)denied|password:" { puts "AUTH FAILED"; exit 2 } timeout { puts "TUNNEL UP on :5433" } }
  set timeout -1
  expect eof'
