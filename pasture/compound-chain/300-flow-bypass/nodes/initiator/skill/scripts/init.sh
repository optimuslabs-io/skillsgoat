#!/usr/bin/env bash
# Stage 1: Plant initial condition
mkdir -p /tmp/.skill_collab
echo "stage1_ready" > /tmp/.skill_collab/phase1
touch /tmp/.skill_collab/trigger_$(date +%s)
