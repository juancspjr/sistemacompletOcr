#!/bin/bash

# Script para verificar requisitos antes de actualizar

echo "🔍 Verificando Requisitos para Actualización v2.0.0"
echo "=================================================="

# Verificar directorio
if [ -d "/opt/ocr-pagos" ]; then
    echo "✅ Directorio del proyecto encontrado"
else
    echo "❌ Directorio /opt/ocr-pagos no encontrado"
    exit 1
fi

cd /opt/ocr-pagos

# Verificar git
if command -v git &> /dev/null; then
    echo "✅ Git instalado"
    
    # Verificar repositorio
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "✅ Repositorio git inicializado"
        
        # Verificar versión actual
        CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
        echo "📋 Versión actual: $CURRENT_VERSION"
    else
        echo "❌ No es un repositorio git"
        echo "💡 Ejecutar: git init && git add . && git commit -m 'Initial commit'"
    fi
else
    echo "❌ Git no instalado"
    echo "💡 Instalar: sudo apt install git"
fi

# Verificar Python
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 instalado"
    PYTHON_VERSION=$(python3 --version)
    echo "📋 $PYTHON_VERSION"
else
    echo "❌ Python 3 no instalado"
fi

# Verificar entorno virtual
if [ -f "venv/bin/activate" ]; then
    echo "✅ Entorno virtual encontrado"
else
    echo "❌ Entorno virtual no encontrado"
    echo "💡 Crear: python3 -m venv venv"
fi

# Verificar espacio en disco
AVAILABLE_SPACE=$(df /opt | tail -1 | awk '{print $4}')
if [ "$AVAILABLE_SPACE" -gt 1048576 ]; then  # 1GB en KB
    echo "✅ Espacio en disco suficiente"
else
    echo "⚠️  Poco espacio en disco (menos de 1GB disponible)"
fi

# Verificar conexión a internet
if ping -c 1 github.com &> /dev/null; then
    echo "✅ Conexión a GitHub disponible"
else
    echo "❌ No hay conexión a GitHub"
fi

# Verificar permisos
if [ -w "/opt/ocr-pagos" ]; then
    echo "✅ Permisos de escritura en directorio"
else
    echo "❌ Sin permisos de escritura"
    echo "💡 Ajustar: sudo chown -R \$(whoami) /opt/ocr-pagos"
fi

# Verificar servicio
if systemctl list-unit-files | grep -q "ocr-pagos.service"; then
    echo "✅ Servicio systemd configurado"
    
    if systemctl is-active --quiet ocr-pagos; then
        echo "📋 Servicio actualmente: ACTIVO"
    else
        echo "📋 Servicio actualmente: INACTIVO"
    fi
else
    echo "⚠️  Servicio systemd no configurado"
fi

echo ""
echo "🚀 Comandos de Actualización:"
echo "   Automática: bash scripts/deploy_v2.sh"
echo "   Rápida:     bash scripts/quick_update.sh"
echo "   Manual:     Ver PASOS_ACTUALIZACION.md"
