#!/bin/bash

# Script de Actualización Automática del Sistema OCR
# Versión: 1.0.0

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables de configuración
PROJECT_DIR="/opt/ocr-pagos"
BACKUP_DIR="/opt/ocr-backups"
SERVICE_NAME="ocr-pagos"
REPO_URL="https://github.com/tu-usuario/sistema-ocr-pagos.git"

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

check_prerequisites() {
    log_info "Verificando prerrequisitos..."
    
    # Verificar que estamos en el directorio correcto
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Directorio del proyecto no encontrado: $PROJECT_DIR"
        exit 1
    fi
    
    # Verificar que git está instalado
    if ! command -v git &> /dev/null; then
        log_error "Git no está instalado"
        exit 1
    fi
    
    # Verificar conexión a internet
    if ! ping -c 1 github.com &> /dev/null; then
        log_error "No hay conexión a internet"
        exit 1
    fi
    
    log_success "Prerrequisitos verificados ✓"
}

create_backup() {
    log_info "Creando backup del sistema actual..."
    
    # Crear directorio de backup
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup del código
    cp -r "$PROJECT_DIR" "$BACKUP_PATH/code"
    
    # Backup de datos críticos
    if [ -d "$PROJECT_DIR/data" ]; then
        cp -r "$PROJECT_DIR/data" "$BACKUP_PATH/"
    fi
    
    # Backup de configuración
    if [ -f "$PROJECT_DIR/src/config.py" ]; then
        cp "$PROJECT_DIR/src/config.py" "$BACKUP_PATH/config_backup.py"
    fi
    
    # Crear archivo de información del backup
    cat > "$BACKUP_PATH/backup_info.txt" << EOF
Backup creado: $(date)
Versión anterior: $(cd $PROJECT_DIR && git describe --tags --always 2>/dev/null || echo "unknown")
Directorio original: $PROJECT_DIR
Razón: Actualización automática del sistema
EOF
    
    log_success "Backup creado en: $BACKUP_PATH"
    echo "$BACKUP_PATH" > /tmp/last_backup_path
}

stop_services() {
    log_info "Deteniendo servicios..."
    
    # Detener servicio systemd si existe
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        sudo systemctl stop "$SERVICE_NAME"
        log_success "Servicio $SERVICE_NAME detenido"
    else
        log_info "Servicio $SERVICE_NAME no está ejecutándose"
    fi
    
    # Matar procesos Python relacionados (precaución)
    pkill -f "python.*main.py" 2>/dev/null || true
    sleep 2
}

start_services() {
    log_info "Iniciando servicios..."
    
    # Iniciar servicio systemd si existe
    if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        sudo systemctl start "$SERVICE_NAME"
        sleep 3
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_success "Servicio $SERVICE_NAME iniciado correctamente"
        else
            log_error "Error al iniciar servicio $SERVICE_NAME"
            return 1
        fi
    else
        log_info "Servicio systemd no configurado"
    fi
}

fetch_latest_version() {
    log_info "Obteniendo información de la última versión..."
    
    cd "$PROJECT_DIR"
    
    # Obtener información del repositorio remoto
    git fetch origin --tags
    
    # Obtener la última versión
    LATEST_TAG=$(git describe --tags --abbrev=0 origin/main 2>/dev/null || echo "")
    CURRENT_TAG=$(git describe --tags --always 2>/dev/null || echo "unknown")
    
    log_info "Versión actual: $CURRENT_TAG"
    log_info "Última versión disponible: ${LATEST_TAG:-"No hay tags disponibles"}"
    
    echo "$LATEST_TAG" > /tmp/latest_version
    echo "$CURRENT_TAG" > /tmp/current_version
}

update_code() {
    log_info "Actualizando código..."
    
    cd "$PROJECT_DIR"
    
    # Guardar cambios locales si los hay
    if ! git diff --quiet; then
        log_warning "Hay cambios locales no guardados. Creando stash..."
        git stash push -m "Auto-stash before update $(date)"
    fi
    
    # Actualizar código
    LATEST_TAG=$(cat /tmp/latest_version)
    
    if [ -n "$LATEST_TAG" ]; then
        log_info "Actualizando a versión: $LATEST_TAG"
        git checkout main
        git pull origin main
        git checkout "$LATEST_TAG"
    else
        log_info "Actualizando a la última versión de main"
        git checkout main
        git pull origin main
    fi
    
    log_success "Código actualizado correctamente"
}

update_dependencies() {
    log_info "Actualizando dependencias..."
    
    cd "$PROJECT_DIR"
    
    # Activar entorno virtual
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        
        # Actualizar pip
        pip install --upgrade pip
        
        # Instalar/actualizar dependencias
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt --upgrade
            log_success "Dependencias actualizadas"
        else
            log_warning "requirements.txt no encontrado"
        fi
    else
        log_error "Entorno virtual no encontrado"
        return 1
    fi
}

migrate_configuration() {
    log_info "Migrando configuración..."
    
    BACKUP_PATH=$(cat /tmp/last_backup_path)
    
    # Comparar archivos de configuración
    if [ -f "$BACKUP_PATH/config_backup.py" ] && [ -f "$PROJECT_DIR/src/config.py" ]; then
        # Verificar si hay diferencias significativas
        if ! diff -q "$BACKUP_PATH/config_backup.py" "$PROJECT_DIR/src/config.py" > /dev/null; then
            log_warning "Se detectaron cambios en la configuración"
            log_info "Backup de configuración anterior: $BACKUP_PATH/config_backup.py"
            log_info "Nueva configuración: $PROJECT_DIR/src/config.py"
            log_warning "REVISAR MANUALMENTE las diferencias de configuración"
        else
            log_success "Configuración sin cambios"
        fi
    fi
    
    # Preservar datos críticos
    if [ -d "$BACKUP_PATH/data" ]; then
        log_info "Preservando datos del sistema..."
        
        # Copiar modelo probabilístico si existe
        if [ -f "$BACKUP_PATH/data/probabilistic_model.json" ]; then
            cp "$BACKUP_PATH/data/probabilistic_model.json" "$PROJECT_DIR/data/"
            log_success "Modelo probabilístico preservado"
        fi
        
        # Copiar feedback si existe
        if [ -d "$BACKUP_PATH/data/feedback_loop" ]; then
            cp -r "$BACKUP_PATH/data/feedback_loop"/* "$PROJECT_DIR/data/feedback_loop/" 2>/dev/null || true
            log_success "Datos de feedback preservados"
        fi
        
        # Copiar plantillas personalizadas
        if [ -d "$BACKUP_PATH/data/templates" ]; then
            cp -r "$BACKUP_PATH/data/templates"/* "$PROJECT_DIR/templates/" 2>/dev/null || true
            log_success "Plantillas personalizadas preservadas"
        fi
    fi
}

verify_update() {
    log_info "Verificando actualización..."
    
    cd "$PROJECT_DIR"
    
    # Verificar que el código se actualizó
    NEW_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
    log_info "Nueva versión instalada: $NEW_VERSION"
    
    # Ejecutar test de verificación
    if [ -f "test_installation.py" ]; then
        source venv/bin/activate
        if python3 test_installation.py; then
            log_success "Verificación de instalación exitosa"
        else
            log_error "La verificación de instalación falló"
            return 1
        fi
    else
        log_warning "Script de verificación no encontrado"
    fi
    
    # Verificar que los servicios están funcionando
    sleep 5
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        log_success "Servicio funcionando correctamente"
    else
        log_warning "Servicio no está activo (puede ser normal si no está configurado)"
    fi
}

rollback() {
    log_error "Iniciando rollback..."
    
    BACKUP_PATH=$(cat /tmp/last_backup_path)
    
    if [ -d "$BACKUP_PATH" ]; then
        # Detener servicios
        stop_services
        
        # Restaurar código
        rm -rf "$PROJECT_DIR"
        cp -r "$BACKUP_PATH/code" "$PROJECT_DIR"
        
        # Restaurar permisos
        sudo chown -R $USER:ocr-service "$PROJECT_DIR" 2>/dev/null || true
        
        # Reiniciar servicios
        start_services
        
        log_success "Rollback completado. Sistema restaurado desde: $BACKUP_PATH"
    else
        log_error "No se encontró backup para rollback"
        exit 1
    fi
}

show_update_summary() {
    CURRENT_VERSION=$(cat /tmp/current_version)
    NEW_VERSION=$(cd "$PROJECT_DIR" && git describe --tags --always 2>/dev/null || echo "unknown")
    
    echo
    echo "=================================="
    echo "  RESUMEN DE ACTUALIZACIÓN"
    echo "=================================="
    echo
    echo "📦 Versión anterior: $CURRENT_VERSION"
    echo "🚀 Versión nueva: $NEW_VERSION"
    echo "📁 Directorio: $PROJECT_DIR"
    echo "💾 Backup: $(cat /tmp/last_backup_path)"
    echo
    echo "🔧 VERIFICACIONES POST-ACTUALIZACIÓN:"
    echo "   ✓ Código actualizado"
    echo "   ✓ Dependencias actualizadas"
    echo "   ✓ Configuración migrada"
    echo "   ✓ Datos preservados"
    echo "   ✓ Servicios reiniciados"
    echo
    echo "📋 PRÓXIMOS PASOS:"
    echo "   1. Verificar logs: tail -f $PROJECT_DIR/logs/system.log"
    echo "   2. Probar procesamiento: python3 $PROJECT_DIR/src/main.py [imagen] [id]"
    echo "   3. Revisar configuración si hay warnings"
    echo
    echo "🆘 EN CASO DE PROBLEMAS:"
    echo "   Rollback: bash $0 --rollback"
    echo
}

# Función principal
main() {
    echo "=================================="
    echo "  ACTUALIZADOR SISTEMA OCR"
    echo "=================================="
    echo
    
    # Manejar argumentos
    if [ "$1" = "--rollback" ]; then
        rollback
        exit 0
    fi
    
    # Verificar si se ejecuta como root
    if [[ $EUID -eq 0 ]]; then
        log_error "No ejecutar como root. Usar: bash update_system.sh"
        exit 1
    fi
    
    # Proceso de actualización
    check_prerequisites
    create_backup
    fetch_latest_version
    
    # Verificar si hay actualizaciones disponibles
    CURRENT_VERSION=$(cat /tmp/current_version)
    LATEST_VERSION=$(cat /tmp/latest_version)
    
    if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ] && [ -n "$LATEST_VERSION" ]; then
        log_info "El sistema ya está en la última versión: $CURRENT_VERSION"
        read -p "¿Forzar actualización de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Actualización cancelada"
            exit 0
        fi
    fi
    
    # Confirmar actualización
    echo
    log_warning "Se va a actualizar el sistema:"
    log_info "  De: $CURRENT_VERSION"
    log_info "  A:  ${LATEST_VERSION:-"última versión"}"
    echo
    read -p "¿Continuar con la actualización? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Actualización cancelada"
        exit 0
    fi
    
    # Ejecutar actualización
    stop_services
    
    if update_code && update_dependencies && migrate_configuration; then
        start_services
        
        if verify_update; then
            show_update_summary
            log_success "¡Actualización completada exitosamente!"
        else
            log_error "La verificación falló. Iniciando rollback..."
            rollback
            exit 1
        fi
    else
        log_error "Error durante la actualización. Iniciando rollback..."
        rollback
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Actualización interrumpida"; rollback; exit 1' INT TERM

# Ejecutar actualización
main "$@"
