#!/bin/bash
# Ambiente do data app Dashboard DATASUS (imagem dadosfera/base-kernel-py, Python 3.9). Só pip.
set -e
pip3 install --upgrade pip
pip3 install -r /project-dir/backend/requirements.txt
# A imagem traz um pyOpenSSL antigo que ainda satisfaz o snowflake-connector, mas quebra com o cryptography
# novo (module 'lib' has no attribute 'X509_V_FLAG_NOTIFY_POLICY'). Força a versão compatível.
pip3 install --upgrade "pyOpenSSL>=24,<26"
