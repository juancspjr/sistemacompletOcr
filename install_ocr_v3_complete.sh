#!/bin/bash

# Script de Instalación Automática - Sistema OCR v3.0
# Descarga completa desde GitHub y configuración automática

set -e  # Salir si hay algún error

echo "🚀 INSTALACIÓN AUTOMÁTICA - SISTEMA OCR v3.0"
echo "=============================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[PASO]${NC} $1"
}

# Variables
PROJECT_NAME="sistemacompletOcr"
REPO_URL="https://github.com/juancspjr/sistemacompletOcr.git"
INSTALL_DIR="$HOME/ocr_system_v3"
VENV_NAME="ocr_env"

print_step "1. Verificando dependencias del sistema..."

# Verificar Git
if ! command -v git &> /dev/null; then
    print_error "Git no está instalado. Instalando..."
    sudo apt update
    sudo apt install -y git
fi

# Verificar Python3
if ! command -v python3 &> /dev/null; then
    print_error "Python3 no está instalado. Instalando..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    print_warning "pip3 no está instalado. Instalando..."
    sudo apt install -y python3-pip
fi

print_status "Dependencias del sistema verificadas ✓"

print_step "2. Descargando el repositorio completo..."

# Eliminar directorio si existe
if [ -d "$INSTALL_DIR" ]; then
    print_warning "El directorio $INSTALL_DIR ya existe. Eliminando..."
    rm -rf "$INSTALL_DIR"
fi

# Clonar repositorio
print_status "Clonando desde: $REPO_URL"
git clone "$REPO_URL" "$INSTALL_DIR"

if [ $? -eq 0 ]; then
    print_status "Repositorio descargado exitosamente ✓"
else
    print_error "Error descargando el repositorio"
    exit 1
fi

print_step "3. Configurando el entorno virtual..."

cd "$INSTALL_DIR"

# Crear entorno virtual
python3 -m venv "$VENV_NAME"
print_status "Entorno virtual creado: $VENV_NAME ✓"

# Activar entorno virtual
source "$VENV_NAME/bin/activate"
print_status "Entorno virtual activado ✓"

print_step "4. Instalando dependencias Python..."

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias desde requirements.txt
if [ -f "requirements.txt" ]; then
    print_status "Instalando desde requirements.txt..."
    pip install -r requirements.txt
else
    print_warning "requirements.txt no encontrado. Instalando dependencias básicas..."
    pip install opencv-python pytesseract pillow numpy
fi

print_status "Dependencias Python instaladas ✓"

print_step "5. Instalando Tesseract OCR..."

# Instalar Tesseract
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-spa

# Verificar instalación de Tesseract
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version | head -n1)
    print_status "Tesseract instalado: $TESSERACT_VERSION ✓"
else
    print_error "Error instalando Tesseract"
    exit 1
fi

print_step "6. Configurando directorios del proyecto..."

# Crear directorios necesarios
mkdir -p input output temp logs

print_status "Directorios creados ✓"

print_step "7. Verificando la instalación..."

# Verificar estructura del proyecto
print_status "Verificando estructura del proyecto..."

REQUIRED_FILES=(
    "src/config.py"
    "src/main.py"
    "src/image_processor.py"
    "src/field_extractor.py"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status "✓ $file"
    else
        print_error "✗ $file (FALTANTE)"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    print_status "Todos los archivos principales están presentes ✓"
else
    print_error "Faltan ${#MISSING_FILES[@]} archivos importantes"
    print_warning "Archivos faltantes: ${MISSING_FILES[*]}"
fi

print_step "8. Creando imagen de prueba..."

# Crear imagen de prueba simple
python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Crear directorio input si no existe
os.makedirs('input', exist_ok=True)

# Crear imagen de prueba
img = Image.new('RGB', (800, 600), 'white')
draw = ImageDraw.Draw(img)

# Simular un comprobante
draw.rectangle([50, 50, 750, 550], outline='black', width=2)
draw.text((100, 100), 'COMPROBANTE DE PAGO', fill='black')
draw.text((100, 150), 'Monto: Bs. 150,50', fill='black')
draw.text((100, 200), 'Fecha: 28/12/2024', fill='black')
draw.text((100, 250), 'Operación: 1234567890', fill='black')
draw.text((100, 300), 'Banco: Banco de Venezuela', fill='black')

img.save('input/test_comprobante.png')
print('Imagen de prueba creada: input/test_comprobante.png')
"

print_step "9. Prueba rápida del sistema..."

# Probar importaciones básicas
python3 -c "
try:
    import cv2
    import pytesseract
    import numpy as np
    from PIL import Image
    print('✓ Todas las librerías se importaron correctamente')
except ImportError as e:
    print(f'✗ Error importando librerías: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Prueba de importaciones exitosa ✓"
else
    print_error "Error en las importaciones"
    exit 1
fi

print_step "10. Creando scripts de acceso rápido..."

# Crear script de activación
cat > activate_ocr.sh << 'EOF'
#!/bin/bash
# Script para activar el entorno OCR

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🔧 Activando entorno OCR v3.0..."
source ocr_env/bin/activate

echo "✅ Entorno activado. Comandos disponibles:"
echo "   • python3 src/main.py input/imagen.png    - Procesar imagen"
echo "   • deactivate                              - Desactivar entorno"
echo ""
echo "📁 Directorio actual: $(pwd)"
echo "🐍 Python: $(which python3)"

# Mantener la sesión activa
exec bash
EOF

chmod +x activate_ocr.sh

# Crear script de prueba rápida
cat > test_system.sh << 'EOF'
#!/bin/bash
# Script de prueba rápida del sistema

echo "🧪 PRUEBA RÁPIDA DEL SISTEMA OCR v3.0"
echo "====================================="

# Activar entorno
source ocr_env/bin/activate

# Verificar que existe imagen de prueba
if [ ! -f "input/test_comprobante.png" ]; then
    echo "❌ No se encuentra la imagen de prueba"
    exit 1
fi

echo "📸 Procesando imagen de prueba..."
python3 src/main.py input/test_comprobante.png

echo ""
echo "✅ Prueba completada. Revisa los resultados en el directorio temp/"
EOF

chmod +x test_system.sh

print_status "Scripts de acceso creados ✓"

echo ""
echo "🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo "========================================"
echo ""
echo "📍 Ubicación del proyecto: $INSTALL_DIR"
echo "🐍 Entorno virtual: $VENV_NAME"
echo ""
echo "🚀 COMANDOS PARA EMPEZAR:"
echo ""
echo "1. Ir al directorio del proyecto:"
echo "   cd $INSTALL_DIR"
echo ""
echo "2. Activar el entorno (OPCIÓN A - Manual):"
echo "   source $VENV_NAME/bin/activate"
echo ""
echo "2. Activar el entorno (OPCIÓN B - Script automático):"
echo "   ./activate_ocr.sh"
echo ""
echo "3. Procesar una imagen:"
echo "   python3 src/main.py input/imagen.png"
echo ""
echo "4. Prueba rápida del sistema:"
echo "   ./test_system.sh"
echo ""
echo "📚 ARCHIVOS IMPORTANTES:"
echo "   • README.md                    - Documentación principal"
echo "   • GUIA_INSTALACION_COMPLETA.md - Guía detallada"
echo "   • src/main.py                  - Script principal"
echo "   • input/                       - Coloca aquí tus imágenes"
echo "   • temp/                        - Resultados de procesamiento"
echo ""
echo "🆕 NUEVA FUNCIONALIDAD v3.0:"
echo "   • Inversión inteligente de colores para fondos oscuros"
echo "   • Detección automática de fondos negros"
echo "   • Conversión automática: letras blancas → letras negras"
echo "   • Optimizado para comprobantes de fondo oscuro"
echo ""
echo "💡 Para desactivar el entorno: deactivate"
echo ""
print_status "¡Sistema listo para usar! 🎯"
