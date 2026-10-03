#!/usr/bin/env bash
set -e

echo "=== Configurando permissão X11 para a GUI do RViz2 no Docker ==="
xhost +local:root 2>/dev/null || true

echo "=== Subindo o contêiner Docker para G1 Teleop (Fase 1) ==="
docker compose up --build
