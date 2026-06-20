#!/usr/bin/env sh
set -xe
cd ~/stroboparty2
. venv/bin/activate
./hz-player.py "${@}"

