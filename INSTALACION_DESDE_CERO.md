# 🚀 GUÍA DE INSTALACIÓN DESDE CERO - OCR v2.0.0

## 📋 Tabla de Contenidos
1. [Limpieza Completa del Sistema](#limpieza-completa)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Instalación Automática](#instalación-automática)
4. [Verificación del Sistema](#verificación)
5. [Pruebas Funcionales](#pruebas)
6. [Solución de Problemas](#problemas)

---

## 🧹 1. Limpieza Completa del Sistema {#limpieza-completa}

### Eliminar Instalaciones Previas

\`\`\`bash
# 1. Detener todos los servicios relacionados
sudo systemctl stop ocr-pagos 2>/dev/null || true
sudo systemctl disable ocr-pagos 2>/dev/null || true

# 2. Eliminar directorios de instalación
sudo rm -rf /opt/ocr-pagos
sudo rm -rf /opt/ocr-backups
rm -rf ~/ocr-*
rm -rf ~/sistemacompletOcr

# 3. Limpiar servicios systemd
sudo rm -f /etc/systemd/system/ocr-pagos.service
sudo systemctl daemon-reload

# 4. Limpiar procesos Python relacionados
pkill -f "python.*main" 2>/dev/null || true
pkill -f "python.*ocr" 2>/dev/null || true

# 5. Limpiar archivos temporales
sudo rm -rf /tmp/ocr_*
sudo rm -rf /tmp/tesseract_*

echo "✅ Limpieza completa terminada"
\`\`\`

### Verificar Limpieza

\`\`\`bash
# Verificar que no queden procesos
ps aux | grep -i ocr
ps aux | grep -i tesseract

# Verificar que no queden directorios
ls -la /opt/ | grep ocr
ls -la ~/ | grep ocr

# Verificar servicios
systemctl list-units | grep ocr
\`\`\`

---

## 🔧 2. Preparación del Entorno {#preparación-del-entorno}

### Actualizar Sistema

\`\`\`bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libopencv-dev \
    python3-opencv \
    build-essential \
    pkg-config
\`\`\`

### Verificar Tesseract

\`\`\`bash
# Verificar instalación de Tesseract
tesseract --version
tesseract --list-langs | grep spa

# Si no está español, instalarlo
sudo apt install tesseract-ocr-spa -y
\`\`\`

### Crear Usuario del Sistema (Opcional)

\`\`\`bash
# Crear usuario dedicado para OCR
sudo useradd -r -s /bin/bash -d /opt/ocr-pagos -m ocr-service
sudo usermod -a -G sudo ocr-service
\`\`\`

---

## 🚀 3. Instalación Automática {#instalación-automática}

### Opción A: Instalación en Directorio Personal (Recomendada)

\`\`\`bash
# 1. Crear directorio limpio
mkdir -p ~/ocr-sistema-v2
cd ~/ocr-sistema-v2

# 2. Descargar script de instalación
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/install_clean.sh -o install_clean.sh

# 3. Ejecutar instalación
chmod +x install_clean.sh
./install_clean.sh
\`\`\`

### Opción B: Instalación del Sistema (/opt)

\`\`\`bash
# 1. Crear directorio del sistema
sudo mkdir -p /opt/ocr-pagos
sudo chown $USER:$USER /opt/ocr-pagos
cd /opt/ocr-pagos

# 2. Descargar e instalar
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/install_system.sh -o install_system.sh
chmod +x install_system.sh
sudo ./install_system.sh
\`\`\`

---

## ✅ 4. Verificación del Sistema {#verificación}

### Verificación Básica

\`\`\`bash
# Ir al directorio de instalación
cd ~/ocr-sistema-v2  # o /opt/ocr-pagos

# Activar entorno virtual
source venv/bin/activate

# Verificar estructura
ls -la
echo "Estructura correcta si ves: src/, data/, templates/, scripts/, venv/"

# Verificar archivos críticos
python3 -c "
import sys
sys.path.append('src')

# Verificar importaciones
try:
    import config
    print('✅ config.py - OK')
except Exception as e:
    print(f'❌ config.py - ERROR: {e}')

try:
    import main_v2
    print('✅ main_v2.py - OK')
except Exception as e:
    print(f'❌ main_v2.py - ERROR: {e}')

try:
    from image_processor_optimized import diagnose_and_process_image
    print('✅ image_processor_optimized.py - OK')
except Exception as e:
    print(f'❌ image_processor_optimized.py - ERROR: {e}')

try:
    from template_manager_v2 import identify_template_or_zoi_v2
    print('✅ template_manager_v2.py - OK')
except Exception as e:
    print(f'❌ template_manager_v2.py - ERROR: {e}')

try:
    from data_extractor_v2 import extract_data_v2
    print('✅ data_extractor_v2.py - OK')
except Exception as e:
    print(f'❌ data_extractor_v2.py - ERROR: {e}')

print('\\n🎉 Verificación de importaciones completada')
"
\`\`\`

---

## 🧪 5. Pruebas Funcionales {#pruebas}

### Prueba Básica del Sistema

\`\`\`bash
# Crear imagen de prueba simple
python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Crear directorio input si no existe
os.makedirs('input', exist_ok=True)

# Crear imagen de prueba
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)

# Simular texto de comprobante
text_lines = [
    'COMPROBANTE DE PAGO MÓVIL',
    'Banco: Banco de Venezuela',
    'Fecha: 28/12/2024',
    'Hora: 14:30:25',
    'Monto: Bs. 150.000,00',
    'Referencia: 123456789',
    'C.I.: 12.345.678',
    'Teléfono: 0414-1234567'
]

y_position = 50
for line in text_lines:
    draw.text((50, y_position), line, fill='black')
    y_position += 60

img.save('input/test_comprobante.png')
print('✅ Imagen de prueba creada: input/test_comprobante.png')
"

# Ejecutar prueba
python3 src/main_v2.py input/test_comprobante.png
\`\`\`

### Verificar Resultados

\`\`\`bash
# Verificar que se crearon archivos de resultado
ls -la temp/
ls -la output/ 2>/dev/null || echo "Directorio output no creado"

# Verificar logs
tail -n 20 logs/system.log
\`\`\`

---

## 🔧 6. Solución de Problemas {#problemas}

### Problemas Comunes

#### Error: "module 'config' has no attribute 'LOG_FILE'"

\`\`\`bash
# Verificar config.py
python3 -c "
import sys
sys.path.append('src')
import config
print('LOG_FILE_PATH:', getattr(config, 'LOG_FILE_PATH', 'NO DEFINIDO'))
print('LOG_FILE:', getattr(config, 'LOG_FILE', 'NO DEFINIDO'))
"

# Si falla, reinstalar
rm -rf src/config.py
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/src/config.py -o src/config.py
\`\`\`

#### Error de Tesseract

\`\`\`bash
# Verificar Tesseract
which tesseract
tesseract --version

# Reinstalar si es necesario
sudo apt remove tesseract-ocr tesseract-ocr-spa -y
sudo apt install tesseract-ocr tesseract-ocr-spa -y
\`\`\`

#### Error de Dependencias Python

\`\`\`bash
# Recrear entorno virtual
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

### Logs de Diagnóstico

\`\`\`bash
# Activar modo debug
export OCR_DEBUG=1

# Ejecutar con logs detallados
python3 src/main_v2.py input/test_comprobante.png 2>&1 | tee debug.log

# Revisar logs
cat logs/system.log
cat debug.log
\`\`\`

---

## 🎯 Comandos de Uso Final

Una vez instalado correctamente:

\`\`\`bash
# Activar entorno (siempre necesario)
source venv/bin/activate

# Procesar una imagen
python3 src/main_v2.py input/mi_comprobante.png

# Ver resultados
ls temp/mi_comprobante_*/
cat temp/mi_comprobante_*/extraction_result_v2.json

# Ver logs
tail -f logs/system.log
\`\`\`

---

## 📞 Soporte

Si sigues teniendo problemas:

1. **Verificar logs**: `cat logs/system.log`
2. **Modo debug**: `export OCR_DEBUG=1`
3. **Reinstalación limpia**: Repetir desde el paso 1

**¡El sistema debería funcionar perfectamente siguiendo esta guía!**
\`\`\`

```shellscript file="scripts/install_clean.sh"
#!/bin/bash

# Script de Instalación Limpia OCR v2.0.0
# Instalación completa desde cero con verificaciones exhaustivas

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Variables de configuración
REPO_URL="https://github.com/juancspjr/sistemacompletOcr.git"
PROJECT_DIR="$(pwd)"
TEMP_DIR="/tmp/ocr_clean_install_$$"
PYTHON_MIN_VERSION="3.8"

# Funciones de utilidad
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    if [ "$OCR_DEBUG" = "1" ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Función para mostrar banner
show_banner() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "           INSTALACIÓN LIMPIA OCR v2.0.0"
    echo "=================================================================="
    echo -e "${NC}"
    echo "🧹 Instalación completamente nueva desde cero"
    echo "🔧 Verificaciones exhaustivas de integridad"
    echo "📦 Repositorio: https://github.com/juancspjr/sistemacompletOcr.git"
    echo "📁 Directorio: $PROJECT_DIR"
    echo "⚡ Sistema optimizado v2.0 con extracción flexible"
    echo ""
}

# Verificar versión de Python
check_python_version() {
    log_step "Verificando versión de Python..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado"
        log_info "Instalar con: sudo apt-get install python3 python3-pip python3-venv"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "Versión de Python detectada: $PYTHON_VERSION"
    
    # Verificar versión mínima
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Versión de Python compatible ✓"
    else
        log_error "Se requiere Python 3.8 o superior"
        exit 1
    fi
}

# Verificar dependencias del sistema
check_system_dependencies() {
    log_step "Verificando dependencias del sistema..."
    
    # Lista de comandos requeridos
    required_commands=("git" "curl" "tesseract")
    missing_commands=()
    
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            log_success "✓ $cmd disponible"
        else
            log_warning "✗ $cmd no encontrado"
            missing_commands+=("$cmd")
        fi
    done
    
    # Verificar Tesseract específicamente
    if command -v tesseract &> /dev/null; then
        TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
        log_info "Tesseract: $TESSERACT_VERSION"
        
        # Verificar idioma español
        if tesseract --list-langs 2>/dev/null | grep -q "spa"; then
            log_success "✓ Tesseract con soporte para español"
        else
            log_warning "✗ Tesseract sin soporte para español"
            log_info "Instalar con: sudo apt-get install tesseract-ocr-spa"
        fi
    fi
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        log_error "Dependencias faltantes: ${missing_commands[*]}"
        log_info "Instalar con: sudo apt-get install ${missing_commands[*]}"
        
        read -p "¿Intentar instalar automáticamente? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y "${missing_commands[@]}" tesseract-ocr-spa
        else
            exit 1
        fi
    fi
    
    log_success "Dependencias del sistema verificadas ✓"
}

# Limpiar instalaciones previas
clean_previous_installations() {
    log_step "Limpiando instalaciones previas..."
    
    # Limpiar directorio actual
    if [ -d "src" ] || [ -d "venv" ] || [ -f "requirements.txt" ]; then
        log_warning "Detectada instalación previa en directorio actual"
        read -p "¿Eliminar archivos existentes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf src data templates scripts venv logs temp output input
            rm -f requirements.txt README.md Dockerfile docker-compose.yml
            rm -f *.py *.log *.json
            log_success "Directorio limpiado ✓"
        else
            log_error "No se puede continuar con archivos existentes"
            exit 1
        fi
    fi
    
    # Limpiar procesos Python relacionados
    if pgrep -f "python.*main" > /dev/null 2>&1; then
        log_info "Deteniendo procesos Python del OCR..."
        pkill -f "python.*main" 2>/dev/null || true
        sleep 2
    fi
    
    # Limpiar archivos temporales
    rm -rf /tmp/ocr_* 2>/dev/null || true
    
    log_success "Limpieza completada ✓"
}

# Descargar código desde GitHub
download_source_code() {
    log_step "Descargando código fuente desde GitHub..."
    
    # Limpiar directorio temporal
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Verificar conectividad
    if ! ping -c 1 github.com &> /dev/null; then
        log_error "No hay conectividad con GitHub"
        exit 1
    fi
    
    # Clonar repositorio
    log_info "Clonando repositorio: $REPO_URL"
    if git clone "$REPO_URL" "$TEMP_DIR"; then
        log_success "Repositorio clonado exitosamente ✓"
    else
        log_error "Error al clonar repositorio"
        exit 1
    fi
    
    # Verificar contenido crítico
    critical_files=(
        "src/main_v2.py"
        "src/config.py"
        "src/image_processor_optimized.py"
        "src/template_manager_v2.py"
        "src/data_extractor_v2.py"
        "requirements.txt"
    )
    
    log_info "Verificando archivos críticos..."
    for file in "${critical_files[@]}"; do
        if [ -f "$TEMP_DIR/$file" ]; then
            log_success "✓ $file"
        else
            log_error "✗ $file (FALTANTE)"
            exit 1
        fi
    done
    
    log_success "Código fuente descargado y verificado ✓"
}

# Crear estructura de directorios
create_directory_structure() {
    log_step "Creando estructura de directorios..."
    
    # Directorios principales
    directories=(
        "src"
        "data"
        "templates"
        "scripts"
        "input"
        "output"
        "temp"
        "logs"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_debug "Creado directorio: $dir"
    done
    
    # Crear subdirectorios de data
    mkdir -p data/{processed_receipts,feedback_loop,processed_receipts/images_archive,feedback_loop/processed_feedback_archive}
    
    log_success "Estructura de directorios creada ✓"
}

# Copiar archivos del repositorio
copy_source_files() {
    log_step "Copiando archivos del código fuente..."
    
    cd "$PROJECT_DIR"
    
    # Copiar archivos principales
    log_info "Copiando código fuente..."
    cp -r "$TEMP_DIR/src"/* src/ 2>/dev/null || true
    
    log_info "Copiando scripts..."
    cp -r "$TEMP_DIR/scripts"/* scripts/ 2>/dev/null || true
    
    log_info "Copiando plantillas..."
    cp -r "$TEMP_DIR/templates"/* templates/ 2>/dev/null || true
    
    # Copiar archivos de configuración
    [ -f "$TEMP_DIR/requirements.txt" ] && cp "$TEMP_DIR/requirements.txt" .
    [ -f "$TEMP_DIR/README.md" ] && cp "$TEMP_DIR/README.md" .
    [ -f "$TEMP_DIR/Dockerfile" ] && cp "$TEMP_DIR/Dockerfile" .
    [ -f "$TEMP_DIR/docker-compose.yml" ] && cp "$TEMP_DIR/docker-compose.yml" .
    
    # Copiar datos del modelo
    if [ -f "$TEMP_DIR/data/probabilistic_model.json" ]; then
        cp "$TEMP_DIR/data/probabilistic_model.json" data/
        log_info "Modelo probabilístico copiado"
    fi
    
    # Hacer ejecutables los scripts
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x src/main*.py 2>/dev/null || true
    
    log_success "Archivos copiados correctamente ✓"
}

# Configurar entorno Python
setup_python_environment() {
    log_step "Configurando entorno Python..."
    
    cd "$PROJECT_DIR"
    
    # Crear entorno virtual
    log_info "Creando entorno virtual..."
    python3 -m venv venv
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Verificar activación
    if [ "$VIRTUAL_ENV" != "" ]; then
        log_success "Entorno virtual activado: $VIRTUAL_ENV"
    else
        log_error "Error activando entorno virtual"
        exit 1
    fi
    
    # Actualizar pip
    log_info "Actualizando pip..."
    pip install --upgrade pip
    
    # Verificar requirements.txt
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt no encontrado"
        exit 1
    fi
    
    # Instalar dependencias
    log_info "Instalando dependencias Python..."
    pip install -r requirements.txt
    
    # Verificar instalación de dependencias críticas
    log_info "Verificando dependencias críticas..."
    python3 -c "
import sys
errors = []

try:
    import cv2
    print('✓ OpenCV disponible')
except ImportError as e:
    errors.append(f'OpenCV: {e}')

try:
    import pytesseract
    print('✓ PyTesseract disponible')
except ImportError as e:
    errors.append(f'PyTesseract: {e}')

try:
    import numpy as np
    print('✓ NumPy disponible')
except ImportError as e:
    errors.append(f'NumPy: {e}')

try:
    import yaml
    print('✓ PyYAML disponible')
except ImportError as e:
    errors.append(f'PyYAML: {e}')

try:
    from PIL import Image
    print('✓ Pillow disponible')
except ImportError as e:
    errors.append(f'Pillow: {e}')

if errors:
    print('\\nERRORES:')
    for error in errors:
        print(f'✗ {error}')
    sys.exit(1)
else:
    print('\\n🎉 Todas las dependencias están correctamente instaladas')
"
    
    log_success "Entorno Python configurado correctamente ✓"
}

# Verificar integridad del código
verify_code_integrity() {
    log_step "Verificando integridad del código..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Verificar que todos los módulos se pueden importar
    log_info "Verificando importaciones de módulos..."
    
    python3 -c "
import sys
sys.path.append('src')

modules_to_test = [
    'config',
    'main_v2',
    'image_processor_optimized',
    'template_manager_v2',
    'data_extractor_v2',
    'ocr_engine',
    'document_classifier',
    'learning_manager'
]

errors = []

for module_name in modules_to_test:
    try:
        module = __import__(module_name)
        print(f'✓ {module_name} - Importación exitosa')
        
        # Verificaciones específicas
        if module_name == 'config':
            required_attrs = ['LOG_FILE_PATH', 'TEMP_DIR', 'BASE_DIR', 'TESSERACT_LANG']
            for attr in required_attrs:
                if hasattr(module, attr):
                    print(f'  ✓ {attr} definido')
                else:
                    errors.append(f'{module_name}: Atributo {attr} no definido')
                    
        elif module_name == 'main_v2':
            if hasattr(module, 'process_image_v2'):
                print(f'  ✓ Función principal process_image_v2 disponible')
            else:
                errors.append(f'{module_name}: Función process_image_v2 no encontrada')
                
    except Exception as e:
        errors.append(f'{module_name}: {str(e)}')
        print(f'✗ {module_name} - ERROR: {e}')

if errors:
    print('\\n❌ ERRORES DE INTEGRIDAD:')
    for error in errors:
        print(f'  • {error}')
    sys.exit(1)
else:
    print('\\n✅ Verificación de integridad completada exitosamente')
"
    
    log_success "Integridad del código verificada ✓"
}

# Crear imagen de prueba
create_test_image() {
    log_step "Creando imagen de prueba..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    python3 -c "
from PIL import Image, ImageDraw, ImageFont
import os

# Crear imagen de prueba realista
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)

# Simular comprobante de pago móvil
text_lines = [
    'COMPROBANTE DE PAGO MÓVIL',
    '',
    'Banco Emisor: Banco de Venezuela',
    'Banco Receptor: Banesco',
    '',
    'Fecha: 28/12/2024',
    'Hora: 14:30:25',
    '',
    'Datos del Pagador:',
    'C.I.: V-12.345.678',
    'Teléfono: 0414-1234567',
    '',
    'Datos del Beneficiario:',
    'C.I.: V-87.654.321',
    'Teléfono: 0424-7654321',
    '',
    'Monto: Bs. 150.000,00',
    'Referencia: 123456789012',
    '',
    'Estado: EXITOSO'
]

y_position = 30
for line in text_lines:
    if line:  # Solo dibujar líneas no vacías
        draw.text((50, y_position), line, fill='black')
    y_position += 25

# Guardar imagen
img.save('input/test_comprobante.png')
print('✅ Imagen de prueba creada: input/test_comprobante.png')
"
    
    log_success "Imagen de prueba creada ✓"
}

# Ejecutar prueba funcional
run_functional_test() {
    log_step "Ejecutando prueba funcional del sistema..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    log_info "Procesando imagen de prueba..."
    
    # Ejecutar procesamiento con captura de salida
    if python3 src/main_v2.py input/test_comprobante.png > test_output.log 2>&1; then
        log_success "✓ Procesamiento completado sin errores"
        
        # Verificar que se crearon archivos de resultado
        if ls temp/test_comprobante_*/extraction_result_v2.json 1> /dev/null 2>&1; then
            log_success "✓ Archivo de resultados creado"
            
            # Mostrar resumen de resultados
            log_info "Resumen de resultados:"
            python3 -c "
import json
import glob

result_files = glob.glob('temp/test_comprobante_*/extraction_result_v2.json')
if result_files:
    with open(result_files[0], 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print(f'  Estado: {result.get(\"final_status\", \"unknown\")}')
    print(f'  Método: {result.get(\"extraction_method\", \"unknown\")}')
    print(f'  Campos extraídos: {len(result.get(\"campos_extraidos\", {}))}')
    print(f'  Confianza: {result.get(\"overall_confidence\", 0):.1f}%')
else:
    print('  No se encontraron archivos de resultado')
"
        else
            log_warning "⚠ No se crearon archivos de resultado"
        fi
        
    else
        log_error "✗ Error durante el procesamiento"
        log_info "Salida del error:"
        cat test_output.log
        return 1
    fi
    
    log_success "Prueba funcional completada ✓"
}

# Limpiar archivos temporales
cleanup_installation() {
    log_step "Limpiando archivos temporales de instalación..."
    
    # Limpiar directorio temporal
    rm -rf "$TEMP_DIR" 2>/dev/null || true
    
    # Limpiar archivos de prueba
    rm -f test_output.log 2>/dev/null || true
    
    log_success "Limpieza completada ✓"
}

# Mostrar resumen final
show_final_summary() {
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "                    INSTALACIÓN COMPLETADA"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🎉 SISTEMA OCR v2.0.0 INSTALADO EXITOSAMENTE${NC}"
    echo ""
    echo -e "${BLUE}📁 DIRECTORIO DE INSTALACIÓN: $PROJECT_DIR${NC}"
    echo ""
    echo -e "${BLUE}🚀 COMANDOS PRINCIPALES:${NC}"
    echo ""
    echo -e "${CYAN}   1. Activar entorno (SIEMPRE NECESARIO):${NC}"
    echo "      source venv/bin/activate"
    echo ""
    echo -e "${CYAN}   2. Procesar una imagen:${NC}"
    echo "      python3 src/main_v2.py input/mi_imagen.png"
    echo ""
    echo -e "${CYAN}   3. Ver resultados:${NC}"
    echo "      ls temp/mi_imagen_*/"
    echo "      cat temp/mi_imagen_*/extraction_result_v2.json"
    echo ""
    echo -e "${CYAN}   4. Ver logs del sistema:${NC}"
    echo "      tail -f logs/system.log"
    echo ""
    echo -e "${BLUE}📂 ESTRUCTURA INSTALADA:${NC}"
    echo "   ├── src/           # Código fuente v2.0"
    echo "   ├── data/          # Modelos y datos"
    echo "   ├── templates/     # Plantillas de extracción"
    echo "   ├── scripts/       # Scripts de administración"
    echo "   ├── input/         # Imágenes de entrada"
    echo "   ├── output/        # Resultados procesados"
    echo "   ├── temp/          # Archivos temporales"
    echo "   ├── logs/          # Logs del sistema"
    echo "   ├── venv/          # Entorno virtual Python"
    echo "   └── requirements.txt"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
    echo "   • Siempre activar el entorno virtual antes de usar el sistema"
    echo "   • Los resultados se guardan en temp/ con timestamp único"
    echo "   • Los logs están en logs/system.log"
    echo ""
    echo -e "${GREEN}✅ ¡Sistema listo para usar!${NC}"
    echo ""
    echo -e "${BLUE}📖 PRÓXIMOS PASOS:${NC}"
    echo "   1. Copiar tus imágenes a input/"
    echo "   2. Activar entorno: source venv/bin/activate"
    echo "   3. Procesar: python3 src/main_v2.py input/tu_imagen.png"
    echo ""
    echo -e "${PURPLE}==================================================================${NC}"
}

# Función principal
main() {
    show_banner
    
    # Confirmar instalación
    echo -e "${YELLOW}Esta instalación creará un sistema OCR v2.0.0 completamente nuevo${NC}"
    echo "📁 Directorio: $PROJECT_DIR"
    echo "🧹 Se eliminarán archivos existentes si los hay"
    echo ""
    read -p "¿Continuar con la instalación limpia? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Instalación cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar instalación paso a paso
    log_info "Iniciando instalación limpia OCR v2.0.0..."
    
    check_python_version
    check_system_dependencies
    clean_previous_installations
    download_source_code
    create_directory_structure
    copy_source_files
    setup_python_environment
    verify_code_integrity
    create_test_image
    
    if run_functional_test; then
        cleanup_installation
        show_final_summary
        log_success "🎉 ¡Instalación completada exitosamente!"
        exit 0
    else
        log_error "La prueba funcional falló. Revisar instalación."
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Instalación interrumpida"; cleanup_installation; exit 1' INT TERM

# Ejecutar instalación
main "$@"
