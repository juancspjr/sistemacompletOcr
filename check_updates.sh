#!/bin/bash

# Script para verificar si hay nuevas versiones disponibles

PROJECT_DIR="/opt/ocr-pagos"
REPO_URL="https://github.com/tu-usuario/sistema-ocr-pagos.git"

cd "$PROJECT_DIR"

# Obtener versión actual
CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")

# Verificar versión remota
git fetch origin --tags &>/dev/null

LATEST_VERSION=$(git describe --tags --abbrev=0 origin/main 2>/dev/null || echo "")

echo "Versión actual: $CURRENT_VERSION"
echo "Última versión: ${LATEST_VERSION:-"No disponible"}"

if [ -n "$LATEST_VERSION" ] && [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    echo "🚀 Nueva versión disponible: $LATEST_VERSION"
    echo "Para actualizar: bash /opt/ocr-pagos/update_system.sh"
else
    echo "✅ Sistema actualizado"
fi
