#!/bin/sh
set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
default_sdk="$project_root/third_party/niobium-client"
sdk=${NIOBIUM_CLIENT_ROOT:-$default_sdk}

if [ "$sdk" = "$default_sdk" ]; then
  /usr/bin/git -C "$project_root" submodule update --init -- third_party/niobium-client
fi

if [ ! -f "$sdk/dsl_fhe/xcomp/nbc.py" ]; then
  echo "Niobium client SDK not found at: $sdk" >&2
  echo "Initialize submodules or set NIOBIUM_CLIENT_ROOT to a compatible checkout." >&2
  exit 1
fi

if [ "$sdk" = "$default_sdk" ]; then
  /usr/bin/git -C "$sdk" submodule update --init -- vendor/niobium-fhetch
  /usr/bin/git -C "$sdk/vendor/niobium-fhetch" submodule update --init --recursive
fi

if [ ! -f "$sdk/vendor/lib/openfhe/include/openfhe/pke/openfhe.h" ]; then
  make -C "$sdk" release
fi

if [ "$#" -eq 0 ]; then
  set -- test
fi

exec make -C "$project_root" NIOBIUM_CLIENT_ROOT="$sdk" "$@"
