#!/bin/bash

# Script de Instalación Automatizada - Sistema OCR de Pagos Móviles
# Versión: 1.0.0
# Compatible con: Ubuntu Server LTS 20.04/22.04

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
PROJECT_DIR="/opt/ocr-pagos"
PYTHON_VERSION="3.10"
SERVICE_USER="ocr-service"

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

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Este script no debe ejecutarse como root"
        log_info "Ejecuta: bash install.sh"
        exit 1
    fi
}

check_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        log_error "Este script está diseñado para Ubuntu Server LTS"
        exit 1
    fi
    
    local version=$(lsb_release -rs)
    log_info "Detectado Ubuntu $version"
    
    if [[ ! "$version" =~ ^(20\.04|22\.04) ]]; then
        log_warning "Versión de Ubuntu no probada. Recomendado: 20.04 o 22.04"
        read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_resources() {
    log_info "Verificando recursos del sistema..."
    
    # Verificar RAM (mínimo 2GB)
    local ram_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$ram_gb" -lt 2 ]; then
        log_warning "RAM detectada: ${ram_gb}GB. Recomendado: 4GB+"
    else
        log_success "RAM: ${ram_gb}GB ✓"
    fi
    
    # Verificar espacio en disco (mínimo 5GB)
    local disk_gb=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$disk_gb" -lt 5 ]; then
        log_error "Espacio insuficiente: ${disk_gb}GB. Mínimo: 5GB"
        exit 1
    else
        log_success "Espacio disponible: ${disk_gb}GB ✓"
    fi
    
    # Verificar CPU cores
    local cores=$(nproc)
    log_info "CPU cores: $cores"
}

update_system() {
    log_info "Actualizando sistema..."
    
    sudo apt update -qq
    sudo apt upgrade -y -qq
    
    log_info "Instalando herramientas básicas..."
    sudo apt install -y -qq \
        curl \
        wget \
        git \
        build-essential \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "Sistema actualizado ✓"
}

install_python() {
    log_info "Verificando instalación de Python..."
    
    # Verificar si Python 3.10+ ya está instalado
    if command -v python3 &> /dev/null; then
        local current_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ $(echo "$current_version >= 3.9" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
            log_success "Python $current_version ya instalado ✓"
            return
        fi
    fi
    
    log_info "Instalando Python $PYTHON_VERSION..."
    
    # Instalar Python 3.10
    sudo apt install -y -qq \
        python3.10 \
        python3.10-venv \
        python3.10-dev \
        python3-pip
    
    # Crear enlace simbólico si es necesario
    if ! command -v python3 &> /dev/null || [[ $(python3 --version | cut -d'.' -f2) -lt 10 ]]; then
        sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    fi
    
    log_success "Python $(python3 --version) instalado ✓"
}

install_tesseract() {
    log_info "Instalando Tesseract OCR..."
    
    # Verificar si ya está instalado
    if command -v tesseract &> /dev/null; then
        local version=$(tesseract --version | head -1)
        log_success "Tesseract ya instalado: $version ✓"
        
        # Verificar idiomas
        if tesseract --list-langs | grep -q "spa"; then
            log_success "Idioma español disponible ✓"
            return
        fi
    fi
    
    # Instalar Tesseract y paquetes de idioma
    sudo apt install -y -qq \
        tesseract-ocr \
        tesseract-ocr-spa \
        tesseract-ocr-eng \
        tesseract-ocr-script-latn
    
    # Verificar instalación
    if ! command -v tesseract &> /dev/null; then
        log_error "Falló la instalación de Tesseract"
        exit 1
    fi
    
    local version=$(tesseract --version | head -1)
    log_success "Tesseract instalado: $version ✓"
    
    # Verificar idiomas disponibles
    local langs=$(tesseract --list-langs 2>/dev/null | grep -E "(spa|eng)" | tr '\n' ' ')
    log_success "Idiomas disponibles: $langs✓"
}

install_system_dependencies() {
    log_info "Instalando dependencias del sistema..."
    
    # Librerías para OpenCV y procesamiento de imágenes
    sudo apt install -y -qq \
        libopencv-dev \
        python3-opencv \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
        libgomp1 \
        libgtk-3-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev
    
    # Librerías para Pillow
    sudo apt install -y -qq \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libwebp-dev \
        zlib1g-dev
    
    log_success "Dependencias del sistema instaladas ✓"
}

setup_project_directory() {
    log_info "Configurando directorio del proyecto..."
    
    # Crear directorio si no existe
    if [ ! -d "$PROJECT_DIR" ]; then
        sudo mkdir -p "$PROJECT_DIR"
        sudo chown $USER:$USER "$PROJECT_DIR"
        log_success "Directorio creado: $PROJECT_DIR ✓"
    else
        log_info "Directorio ya existe: $PROJECT_DIR"
    fi
    
    cd "$PROJECT_DIR"
    
    # Verificar si ya hay archivos del proyecto
    if [ -f "src/main.py" ]; then
        log_success "Proyecto ya existe en el directorio ✓"
    else
        log_info "Copiando archivos del proyecto..."
        # Aquí se copiarían los archivos del proyecto
        # Por ahora, crear estructura básica
        mkdir -p src templates data input temp logs
        log_success "Estructura de directorios creada ✓"
    fi
}

create_virtual_environment() {
    log_info "Creando entorno virtual de Python..."
    
    cd "$PROJECT_DIR"
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_success "Entorno virtual creado ✓"
    else
        log_info "Entorno virtual ya existe"
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip setuptools wheel -q
    
    log_success "Entorno virtual configurado ✓"
}

install_python_dependencies() {
    log_info "Instalando dependencias de Python..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Verificar si requirements.txt existe
    if [ ! -f "requirements.txt" ]; then
        log_warning "requirements.txt no encontrado, creando versión básica..."
        cat > requirements.txt << 'EOF'
pytesseract==0.3.10
opencv-python==4.8.1.78
Pillow==10.0.1
numpy==1.24.3
pandas==2.0.3
PyYAML==6.0.1
pathlib2==2.3.7
python-dateutil==2.8.2
colorlog==6.7.0
EOF
    fi
    
    # Instalar dependencias
    pip install -r requirements.txt -q
    
    # Verificar instalaciones críticas
    log_info "Verificando instalaciones críticas..."
    
    python3 -c "import cv2; print('OpenCV:', cv2.__version__)" 2>/dev/null && log_success "OpenCV ✓" || log_error "OpenCV ✗"
    python3 -c "import pytesseract; print('PyTesseract: OK')" 2>/dev/null && log_success "PyTesseract ✓" || log_error "PyTesseract ✗"
    python3 -c "import PIL; print('Pillow:', PIL.__version__)" 2>/dev/null && log_success "Pillow ✓" || log_error "Pillow ✗"
    python3 -c "import pandas; print('Pandas:', pandas.__version__)" 2>/dev/null && log_success "Pandas ✓" || log_error "Pandas ✗"
    
    log_success "Dependencias de Python instaladas ✓"
}

setup_permissions() {
    log_info "Configurando permisos..."
    
    cd "$PROJECT_DIR"
    
    # Crear directorios necesarios
    mkdir -p input temp logs data/processed_receipts data/feedback_loop templates
    mkdir -p data/processed_receipts/images_archive data/feedback_loop/processed_feedback_archive
    
    # Establecer permisos
    if [ -d "src" ]; then
        chmod 755 src/*.py 2>/dev/null || true
        chmod +x src/main.py 2>/dev/null || true
        chmod +x src/update_probabilistic_model.py 2>/dev/null || true
    fi
    
    # Crear archivos .gitkeep para directorios vacíos
    for dir in input temp logs templates; do
        touch "$dir/.gitkeep"
    done
    
    log_success "Permisos configurados ✓"
}

create_service_user() {
    log_info "Configurando usuario de servicio..."
    
    # Verificar si el usuario ya existe
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "Usuario $SERVICE_USER ya existe"
    else
        sudo useradd -r -s /bin/false -d "$PROJECT_DIR" "$SERVICE_USER"
        log_success "Usuario $SERVICE_USER creado ✓"
    fi
    
    # Configurar permisos para el usuario de servicio
    sudo chown -R $USER:$SERVICE_USER "$PROJECT_DIR"
    sudo chmod -R g+rw "$PROJECT_DIR"
    
    log_success "Usuario de servicio configurado ✓"
}

setup_systemd_service() {
    log_info "Configurando servicio systemd..."
    
    # Crear archivo de servicio
    sudo tee /etc/systemd/system/ocr-pagos.service > /dev/null << EOF
[Unit]
Description=Sistema OCR de Pagos Móviles
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR/src
ExecStart=$PROJECT_DIR/venv/bin/python3 src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Recargar systemd
    sudo systemctl daemon-reload
    
    log_success "Servicio systemd configurado ✓"
    log_info "Para habilitar: sudo systemctl enable ocr-pagos.service"
    log_info "Para iniciar: sudo systemctl start ocr-pagos.service"
}

setup_log_rotation() {
    log_info "Configurando rotación de logs..."
    
    sudo tee /etc/logrotate.d/ocr-pagos > /dev/null << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload ocr-pagos 2>/dev/null || true
    endscript
}
EOF
    
    log_success "Rotación de logs configurada ✓"
}

create_test_script() {
    log_info "Creando script de verificación..."
    
    cat > "$PROJECT_DIR/test_installation.py" << 'EOF'
#!/usr/bin/env python3
"""Script de verificación de instalación"""

import sys
import os
import subprocess
from pathlib import Path

def test_imports():
    """Verificar importaciones críticas"""
    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except ImportError as e:
        print(f"✗ OpenCV: {e}")
        return False
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract {version}")
    except Exception as e:
        print(f"✗ Tesseract: {e}")
        return False
    
    try:
        import pandas as pd
        print(f"✓ Pandas {pd.__version__}")
    except ImportError as e:
        print(f"✗ Pandas: {e}")
        return False
    
    try:
        import yaml
        print("✓ PyYAML")
    except ImportError as e:
        print(f"✗ PyYAML: {e}")
        return False
    
    try:
        from PIL import Image
        print(f"✓ Pillow {Image.__version__}")
    except ImportError as e:
        print(f"✗ Pillow: {e}")
        return False
    
    return True

def test_directories():
    """Verificar estructura de directorios"""
    required_dirs = [
        'src', 'templates', 'data', 'input', 
        'temp', 'logs', 'data/processed_receipts',
        'data/feedback_loop'
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"✓ Directorio {dir_name}")
        else:
            print(f"✗ Directorio {dir_name} NO existe")
            all_exist = False
    
    return all_exist

def test_tesseract_languages():
    """Verificar idiomas de Tesseract"""
    try:
        result = subprocess.run(['tesseract', '--list-langs'], 
                              capture_output=True, text=True)
        langs = result.stdout.strip().split('\n')[1:]  # Skip first line
        
        required_langs = ['spa', 'eng']
        missing_langs = []
        
        for lang in required_langs:
            if lang in langs:
                print(f"✓ Idioma {lang}")
            else:
                print(f"✗ Idioma {lang} NO disponible")
                missing_langs.append(lang)
        
        return len(missing_langs) == 0
        
    except Exception as e:
        print(f"✗ Error verificando idiomas: {e}")
        return False

def main():
    print("=== Verificación de Instalación OCR System ===\n")
    
    tests = [
        ("Importaciones Python", test_imports),
        ("Estructura de directorios", test_directories),
        ("Idiomas Tesseract", test_tesseract_languages)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if not test_func():
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 ¡Instalación verificada correctamente!")
        print("\nPróximos pasos:")
        print("1. Añadir plantillas en templates/")
        print("2. Configurar integración con N8N")
        print("3. Procesar primera imagen de prueba")
        return 0
    else:
        print("❌ Algunos componentes requieren atención")
        print("Revisa los errores anteriores y ejecuta install.sh nuevamente")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    chmod +x "$PROJECT_DIR/test_installation.py"
    log_success "Script de verificación creado ✓"
}

run_verification() {
    log_info "Ejecutando verificación final..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    if python3 test_installation.py; then
        log_success "¡Instalación completada exitosamente! 🎉"
        return 0
    else
        log_error "La verificación encontró problemas"
        return 1
    fi
}

show_summary() {
    echo
    echo "=================================="
    echo "  RESUMEN DE INSTALACIÓN"
    echo "=================================="
    echo
    echo "📁 Directorio del proyecto: $PROJECT_DIR"
    echo "🐍 Python: $(python3 --version)"
    echo "👁  Tesseract: $(tesseract --version | head -1)"
    echo "👤 Usuario de servicio: $SERVICE_USER"
    echo
    echo "🔧 COMANDOS ÚTILES:"
    echo "   Activar entorno: source $PROJECT_DIR/venv/bin/activate"
    echo "   Verificar sistema: cd $PROJECT_DIR && python3 test_installation.py"
    echo "   Ver logs: tail -f $PROJECT_DIR/logs/system.log"
    echo "   Iniciar servicio: sudo systemctl start ocr-pagos"
    echo
    echo "📚 PRÓXIMOS PASOS:"
    echo "   1. Revisar configuración en src/config.py"
    echo "   2. Añadir plantillas en templates/"
    echo "   3. Procesar imagen de prueba"
    echo "   4. Configurar integración con N8N"
    echo
    echo "📖 Documentación completa en:"
    echo "   - INSTALLATION_GUIDE.md"
    echo "   - USER_GUIDE.md"
    echo "   - README.md"
    echo
}

# Función principal
main() {
    echo "=================================="
    echo "  INSTALADOR OCR PAGOS MÓVILES"
    echo "=================================="
    echo
    
    # Verificaciones previas
    check_root
    check_ubuntu
    check_resources
    
    echo
    log_info "Iniciando instalación..."
    echo
    
    # Proceso de instalación
    update_system
    install_python
    install_tesseract
    install_system_dependencies
    setup_project_directory
    create_virtual_environment
    install_python_dependencies
    setup_permissions
    create_service_user
    setup_systemd_service
    setup_log_rotation
    create_test_script
    
    echo
    log_info "Ejecutando verificación final..."
    
    if run_verification; then
        show_summary
        log_success "¡Instalación completada exitosamente!"
        exit 0
    else
        log_error "La instalación encontró problemas. Revisa los logs anteriores."
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Instalación interrumpida"; exit 1' INT TERM

# Ejecutar instalación
main "$@"
