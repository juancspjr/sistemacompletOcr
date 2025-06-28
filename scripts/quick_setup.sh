#!/bin/bash

# Script de Configuración Rápida OCR v2.0.0
# Descarga y configura el sistema desde GitHub

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Variables de configuración
REPO_URL="https://github.com/juancspjr/sistemacompletOcr.git"
PROJECT_DIR="$(pwd)"
TEMP_DIR="/tmp/ocr_update_$$"

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

# Función para mostrar banner
show_banner() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "           CONFIGURACIÓN RÁPIDA OCR v2.0.0"
    echo "=================================================================="
    echo -e "${NC}"
    echo "🚀 Descarga desde GitHub y configuración automática"
    echo "📦 Repositorio: https://github.com/juancspjr/sistemacompletOcr.git"
    echo "⚡ Configuración local segura"
    echo ""
}

# Verificar prerrequisitos básicos
check_basic_requirements() {
    log_step "Verificando prerrequisitos básicos..."
    
    # Verificar git
    if ! command -v git &> /dev/null; then
        log_error "Git no está instalado"
        log_info "Instalar con: sudo apt-get install git"
        exit 1
    fi
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado"
        log_info "Instalar con: sudo apt-get install python3 python3-pip python3-venv"
        exit 1
    fi
    
    # Verificar conexión a internet
    if ! ping -c 1 github.com &> /dev/null; then
        log_error "No hay conexión a internet o GitHub no es accesible"
        exit 1
    fi
    
    log_success "Prerrequisitos básicos verificados ✓"
}

# Crear backup del directorio actual
create_local_backup() {
    log_step "Creando backup del directorio actual..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="backup_local_$TIMESTAMP"
    
    # Crear backup solo si hay archivos importantes
    if [ -f "src/main.py" ] || [ -f "src/config.py" ] || [ -d "data" ]; then
        log_info "Detectados archivos existentes, creando backup..."
        mkdir -p "$BACKUP_DIR"
        
        # Backup de archivos críticos
        [ -d "src" ] && cp -r src "$BACKUP_DIR/"
        [ -d "data" ] && cp -r data "$BACKUP_DIR/"
        [ -d "templates" ] && cp -r templates "$BACKUP_DIR/"
        [ -f "requirements.txt" ] && cp requirements.txt "$BACKUP_DIR/"
        
        log_success "Backup local creado en: $BACKUP_DIR"
        echo "$PROJECT_DIR/$BACKUP_DIR" > /tmp/ocr_local_backup
    else
        log_info "No se detectaron archivos existentes, omitiendo backup"
    fi
}

# Descargar código desde GitHub
download_from_github() {
    log_step "Descargando código desde GitHub..."
    
    # Limpiar directorio temporal
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Clonar repositorio
    log_info "Clonando repositorio: $REPO_URL"
    if git clone "$REPO_URL" "$TEMP_DIR"; then
        log_success "Repositorio clonado exitosamente ✓"
    else
        log_error "Error al clonar repositorio"
        exit 1
    fi
    
    # Verificar contenido descargado
    if [ ! -f "$TEMP_DIR/src/main_v2.py" ]; then
        log_error "El repositorio no contiene los archivos v2.0 esperados"
        log_info "Verificar que el repositorio esté actualizado"
        exit 1
    fi
    
    log_success "Código v2.0 descargado correctamente ✓"
}

# Sincronizar archivos locales
sync_local_files() {
    log_step "Sincronizando archivos locales..."
    
    cd "$PROJECT_DIR"
    
    # Crear directorios necesarios
    mkdir -p {src,data,templates,scripts,input,output,temp,logs}
    
    # Copiar archivos principales
    log_info "Copiando archivos del sistema v2.0..."
    cp -r "$TEMP_DIR/src"/* src/ 2>/dev/null || true
    cp -r "$TEMP_DIR/scripts"/* scripts/ 2>/dev/null || true
    cp -r "$TEMP_DIR/templates"/* templates/ 2>/dev/null || true
    
    # Copiar archivos de configuración
    [ -f "$TEMP_DIR/requirements.txt" ] && cp "$TEMP_DIR/requirements.txt" .
    [ -f "$TEMP_DIR/README.md" ] && cp "$TEMP_DIR/README.md" .
    [ -f "$TEMP_DIR/Dockerfile" ] && cp "$TEMP_DIR/Dockerfile" .
    [ -f "$TEMP_DIR/docker-compose.yml" ] && cp "$TEMP_DIR/docker-compose.yml" .
    
    # Copiar datos del modelo si no existen localmente
    if [ ! -f "data/probabilistic_model.json" ] && [ -f "$TEMP_DIR/data/probabilistic_model.json" ]; then
        cp "$TEMP_DIR/data/probabilistic_model.json" data/
        log_info "Modelo probabilístico copiado"
    fi
    
    # Hacer ejecutables los scripts
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x src/main*.py 2>/dev/null || true
    
    log_success "Archivos sincronizados correctamente ✓"
}

# Restaurar datos locales importantes
restore_local_data() {
    log_step "Restaurando datos locales importantes..."
    
    if [ -f "/tmp/ocr_local_backup" ]; then
        BACKUP_PATH=$(cat /tmp/ocr_local_backup)
        
        if [ -d "$BACKUP_PATH" ]; then
            log_info "Restaurando datos desde: $BACKUP_PATH"
            
            # Restaurar datos críticos
            if [ -f "$BACKUP_PATH/data/probabilistic_model.json" ]; then
                cp "$BACKUP_PATH/data/probabilistic_model.json" data/
                log_info "Modelo probabilístico local restaurado"
            fi
            
            # Restaurar configuración personalizada
            if [ -f "$BACKUP_PATH/src/config.py" ] && [ -f "src/config.py" ]; then
                # Crear archivo de comparación
                if ! diff -q "$BACKUP_PATH/src/config.py" "src/config.py" > /dev/null 2>&1; then
                    cp "$BACKUP_PATH/src/config.py" "config_local_backup.py"
                    log_warning "Configuración local diferente guardada en: config_local_backup.py"
                fi
            fi
            
            # Restaurar plantillas personalizadas
            if [ -d "$BACKUP_PATH/templates" ]; then
                cp -r "$BACKUP_PATH/templates"/* templates/ 2>/dev/null || true
                log_info "Plantillas personalizadas restauradas"
            fi
            
            log_success "Datos locales restaurados ✓"
        fi
    else
        log_info "No hay datos locales para restaurar"
    fi
}

# Configurar entorno Python
setup_python_environment() {
    log_step "Configurando entorno Python..."
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        log_info "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    log_info "Actualizando pip..."
    pip install --upgrade pip
    
    # Instalar dependencias
    if [ -f "requirements.txt" ]; then
        log_info "Instalando dependencias..."
        pip install -r requirements.txt
        log_success "Dependencias instaladas ✓"
    else
        log_warning "requirements.txt no encontrado, instalando dependencias básicas..."
        pip install opencv-python pytesseract pillow numpy pyyaml
    fi
    
    # Verificar instalación
    python3 -c "
import cv2
import pytesseract
import yaml
import numpy as np
from PIL import Image
print('✓ Todas las dependencias están disponibles')
" || {
        log_error "Error en dependencias"
        exit 1
    }
    
    log_success "Entorno Python configurado ✓"
}

# Verificar instalación
verify_installation() {
    log_step "Verificando instalación..."
    
    # Verificar archivos críticos
    critical_files=(
        "src/main_v2.py"
        "src/image_processor_optimized.py"
        "src/template_manager_v2.py"
        "src/data_extractor_v2.py"
        "scripts/deploy_v2.sh"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_error "✗ $file (FALTANTE)"
            return 1
        fi
    done
    
    # Verificar que el sistema v2.0 funciona
    log_info "Verificando sistema v2.0..."
    if python3 -c "
import sys
sys.path.append('src')
try:
    import main_v2
    print('✓ Sistema v2.0 funcional')
except Exception as e:
    print(f'✗ Error: {e}')
    sys.exit(1)
"; then
        log_success "✓ Sistema v2.0 verificado"
    else
        log_error "✗ Error en sistema v2.0"
        return 1
    fi
    
    log_success "Instalación verificada correctamente ✓"
}

# Limpiar archivos temporales
cleanup() {
    log_step "Limpiando archivos temporales..."
    
    # Limpiar directorio temporal
    rm -rf "$TEMP_DIR" 2>/dev/null || true
    
    # Limpiar archivos temporales
    rm -f /tmp/ocr_local_backup 2>/dev/null || true
    
    log_success "Limpieza completada ✓"
}

# Mostrar resumen final
show_final_summary() {
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "                    CONFIGURACIÓN COMPLETADA"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🎉 SISTEMA OCR v2.0.0 CONFIGURADO EXITOSAMENTE${NC}"
    echo ""
    echo -e "${BLUE}📁 DIRECTORIO ACTUAL: $PROJECT_DIR${NC}"
    echo ""
    echo -e "${BLUE}🚀 COMANDOS PRINCIPALES:${NC}"
    echo "   📋 Procesar imagen:"
    echo "      python3 src/main_v2.py input/imagen.png"
    echo ""
    echo "   🧪 Ejecutar pruebas:"
    echo "      bash scripts/test_v2_system.sh"
    echo ""
    echo "   🔄 Actualización completa (si tienes /opt/ocr-pagos):"
    echo "      bash scripts/deploy_v2.sh"
    echo ""
    echo -e "${BLUE}📂 ESTRUCTURA CREADA:${NC}"
    echo "   ├── src/           # Código fuente v2.0"
    echo "   ├── scripts/       # Scripts de administración"
    echo "   ├── templates/     # Plantillas de extracción"
    echo "   ├── data/          # Modelos y datos"
    echo "   ├── input/         # Imágenes de entrada"
    echo "   ├── output/        # Resultados procesados"
    echo "   ├── venv/          # Entorno virtual Python"
    echo "   └── requirements.txt"
    echo ""
    echo -e "${YELLOW}⚠️  PRÓXIMOS PASOS:${NC}"
    echo "   1. Probar con una imagen:"
    echo "      cp tu_imagen.png input/"
    echo "      python3 src/main_v2.py input/tu_imagen.png"
    echo ""
    echo "   2. Si tienes instalación en /opt/ocr-pagos:"
    echo "      sudo bash scripts/deploy_v2.sh"
    echo ""
    echo -e "${GREEN}✅ ¡Sistema listo para usar!${NC}"
    echo -e "${PURPLE}==================================================================${NC}"
}

# Función principal
main() {
    show_banner
    
    # Confirmar configuración
    echo -e "${YELLOW}Este script descargará y configurará OCR v2.0.0 desde GitHub${NC}"
    echo "📦 Repositorio: $REPO_URL"
    echo "📁 Directorio: $PROJECT_DIR"
    echo ""
    read -p "¿Continuar con la configuración? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Configuración cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar configuración
    check_basic_requirements
    create_local_backup
    download_from_github
    sync_local_files
    restore_local_data
    setup_python_environment
    
    if verify_installation; then
        cleanup
        show_final_summary
        log_success "🎉 ¡Configuración completada exitosamente!"
        exit 0
    else
        log_error "Error en la verificación. Revisar instalación."
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Configuración interrumpida"; cleanup; exit 1' INT TERM

# Ejecutar configuración
main "$@"
