#!/bin/bash
# Ambiente do data app Dashboard DATASUS (imagem dadosfera/base-kernel-py, Python 3.9). Só pip.
# O deploy_service.py anexa o sha256 do requirements.txt a este script: mudar dependência força rebuild.
set -e
pip3 install --upgrade pip
pip3 install -r /project-dir/backend/requirements.txt
