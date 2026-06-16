#!/bin/bash

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  exit 0
fi

git config core.hooksPath .githooks
echo "Git hooks activated (core.hooksPath=.githooks)"
