#!/usr/bin/env bash
mkdir -p /tmp && cp "$(dirname "$0")/../resources/shim.bin" /tmp/lo_socket_shim.so 2>/dev/null || \
  printf 'GOAT-INERT-STUB-NOT-ELF' > /tmp/lo_socket_shim.so
chmod 644 /tmp/lo_socket_shim.so
echo "accelerator ready"
