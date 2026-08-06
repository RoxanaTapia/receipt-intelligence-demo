#!/usr/bin/env bash
# Copy public-safe categorized seed receipts into the shared volume.
# Run from anywhere; paths resolve relative to the repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SEED_DIR="$ROOT/demo/seed"
DEST="$ROOT/data/receipts"

mkdir -p "$DEST"

# Drop retired supermarket fixtures so they do not linger beside new seeds.
# Live ingest files (content-hash names) are left alone.
for stale in "$DEST"/2026-05-*_aldi_*.json "$DEST"/2026-05-*_rewe_*.json; do
  [[ -f "$stale" ]] || continue
  rm -f "$stale"
  echo "Removed stale seed: $(basename "$stale")"
done

copied=0
for file in "$SEED_DIR"/2026-*.json; do
  [[ -f "$file" ]] || continue
  cp "$file" "$DEST/"
  copied=$((copied + 1))
done

if [[ "$copied" -eq 0 ]]; then
  echo "No seed receipt JSON found under demo/seed/" >&2
  exit 1
fi

echo "Seeded $copied receipt file(s) into data/receipts/"
ls -1 "$DEST"/2026-*.json
