#!/usr/bin/env bash
# Prints the name of a working Python command (python3, python or py), or nothing.
for candidate in python3 python py; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import sys" >/dev/null 2>&1; then
    echo "$candidate"; exit 0
  fi
done
exit 0
