#!/bin/sh
# Build packcheck against a kode-sdk checkout: ./build.sh /path/to/kode-sdk
# Needs a C compiler, zlib (libz-dev) and cJSON (fetched here once).
set -e
SDK=${1:?usage: build.sh /path/to/kode-sdk}
cd "$(dirname "$0")"
[ -f cJSON.c ] || { curl -fsSLO https://raw.githubusercontent.com/DaveGamble/cJSON/v1.7.18/cJSON.c; curl -fsSLO https://raw.githubusercontent.com/DaveGamble/cJSON/v1.7.18/cJSON.h; }
P="$SDK/components/kui/pack"
cc -O1 -I stub -I . -I "$P/include" -I "$SDK/components/kode/include" main.c crc.c cJSON.c "$P/src/kui_pack.c" -lz -o packcheck
echo "built ./packcheck"
