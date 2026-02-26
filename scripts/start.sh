#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

for attempt in 1 2; do
	if docker compose up --build -d; then
		exit 0
	fi

	if [ "$attempt" -eq 2 ]; then
		exit 1
	fi

	sleep 5
done
