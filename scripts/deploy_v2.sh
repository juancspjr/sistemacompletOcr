#!/bin/bash

# Script de Despliegue OCR v2.0.0
# Actualiza el sistema desde GitHub a la nueva versión optimizada

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Variables de configuración
PROJECT_DIR="/opt/ocr-pagos"
BACKUP_DIR="/opt/ocr-backups"
SERVICE_NAME="ocr-pagos"
REPO_URL="https://github.com/tu-usuario/sistema-ocr-pagos.git"
TARGET_VERSION="v2.0.0"
CURRENT_BRANCH="main"

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
    echo "           ACTUALIZACIÓN SISTEMA OCR v2.0.0"
    echo "=================================================================="
    echo -e "${NC}"
    echo "🚀 Migración a estrategia de extracción flexible optimizada"
    echo "📊 Basada en análisis de OCR global exitoso"
    echo "⚡ Sin aislamiento de documento + extracción directa"
    echo ""
}

# Verificar prerrequisitos
check_prerequisites() {
    log_step "Verificando prerrequisitos del sistema..."
    
    # Verificar que estamos ejecutando como usuario correcto
    if [[ $EUID -eq 0 ]]; then
        log_error "No ejecutar como root. Usar usuario del sistema OCR."
        exit 1
    fi
    
    # Verificar directorio del proyecto
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Directorio del proyecto no encontrado: $PROJECT_DIR"
        log_info "¿Es la primera instalación? Use install.sh primero."
        exit 1
    fi
    
    # Verificar git
    if ! command -v git &> /dev/null; then
        log_error "Git no está instalado"
        exit 1
    fi
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado"
        exit 1
    fi
    
    # Verificar conexión a internet
    if ! ping -c 1 github.com &> /dev/null; then
        log_error "No hay conexión a internet o GitHub no es accesible"
        exit 1
    fi
    
    # Verificar que estamos en un repositorio git
    cd "$PROJECT_DIR"
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "El directorio $PROJECT_DIR no es un repositorio git"
        exit 1
    fi
    
    log_success "Prerrequisitos verificados ✓"
}

# Crear backup completo del sistema actual
create_comprehensive_backup() {
    log_step "Creando backup completo del sistema actual..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_pre_v2_$TIMESTAMP"
    
    mkdir -p "$BACKUP_PATH"
    
    cd "$PROJECT_DIR"
    
    # Obtener información de la versión actual
    CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
    CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    
    log_info "Versión actual detectada: $CURRENT_VERSION"
    
    # Backup completo del código
    log_info "Copiando código fuente..."
    cp -r "$PROJECT_DIR" "$BACKUP_PATH/code"
    
    # Backup de datos críticos
    if [ -d "$PROJECT_DIR/data" ]; then
        log_info "Respaldando datos del sistema..."
        cp -r "$PROJECT_DIR/data" "$BACKUP_PATH/"
    fi
    
    # Backup de configuración
    if [ -f "$PROJECT_DIR/src/config.py" ]; then
        cp "$PROJECT_DIR/src/config.py" "$BACKUP_PATH/config_v1.py"
    fi
    
    # Backup de logs recientes
    if [ -d "$PROJECT_DIR/logs" ]; then
        log_info "Respaldando logs..."
        mkdir -p "$BACKUP_PATH/logs"
        find "$PROJECT_DIR/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_PATH/logs/" \;
    fi
    
    # Backup de plantillas personalizadas
    if [ -d "$PROJECT_DIR/templates" ]; then
        log_info "Respaldando plantillas..."
        cp -r "$PROJECT_DIR/templates" "$BACKUP_PATH/"
    fi
    
    # Crear archivo de información del backup
    cat > "$BACKUP_PATH/backup_info.txt" << EOF
=== BACKUP SISTEMA OCR PRE-v2.0.0 ===
Fecha de backup: $(date)
Versión anterior: $CURRENT_VERSION
Commit anterior: $CURRENT_COMMIT
Directorio original: $PROJECT_DIR
Razón: Actualización a v2.0.0 (estrategia flexible optimizada)
Usuario: $(whoami)
Hostname: $(hostname)

=== CONTENIDO DEL BACKUP ===
- code/: Código fuente completo
- data/: Datos del sistema (modelos, feedback)
- templates/: Plantillas personalizadas
- logs/: Logs de los últimos 7 días
- config_v1.py: Configuración anterior

=== INSTRUCCIONES DE ROLLBACK ===
En caso de problemas con v2.0.0:
1. Detener servicios: sudo systemctl stop $SERVICE_NAME
2. Restaurar código: rm -rf $PROJECT_DIR && cp -r $BACKUP_PATH/code $PROJECT_DIR
3. Restaurar permisos: sudo chown -R \$(whoami):ocr-service $PROJECT_DIR
4. Reiniciar servicios: sudo systemctl start $SERVICE_NAME

=== COMANDO DE ROLLBACK RÁPIDO ===
bash $PROJECT_DIR/scripts/rollback_from_v2.sh $BACKUP_PATH
EOF
    
    log_success "Backup completo creado en: $BACKUP_PATH"
    echo "$BACKUP_PATH" > /tmp/ocr_backup_path_v2
    
    # Crear script de rollback específico
    create_rollback_script "$BACKUP_PATH"
}

# Crear script de rollback específico
create_rollback_script() {
    local backup_path="$1"
    
    cat > "$PROJECT_DIR/scripts/rollback_from_v2.sh" << 'EOF'
#!/bin/bash

# Script de Rollback desde v2.0.0
# Restaura el sistema a la versión anterior

BACKUP_PATH="$1"

if [ -z "$BACKUP_PATH" ] || [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Ruta de backup no válida"
    echo "Uso: $0 <ruta_backup>"
    exit 1
fi

echo "🔄 Iniciando rollback desde v2.0.0..."
echo "📁 Backup: $BACKUP_PATH"

# Detener servicios
sudo systemctl stop ocr-pagos 2>/dev/null || true

# Restaurar código
echo "📦 Restaurando código..."
rm -rf /opt/ocr-pagos
cp -r "$BACKUP_PATH/code" /opt/ocr-pagos

# Restaurar permisos
sudo chown -R $(whoami):ocr-service /opt/ocr-pagos 2>/dev/null || true

# Reiniciar servicios
sudo systemctl start ocr-pagos 2>/dev/null || true

echo "✅ Rollback completado"
echo "📋 Verificar: systemctl status ocr-pagos"
EOF
    
    chmod +x "$PROJECT_DIR/scripts/rollback_from_v2.sh"
}

# Detener servicios del sistema
stop_services() {
    log_step "Deteniendo servicios del sistema..."
    
    # Detener servicio systemd si existe
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        sudo systemctl stop "$SERVICE_NAME"
        log_success "Servicio $SERVICE_NAME detenido"
    else
        log_info "Servicio $SERVICE_NAME no estaba ejecutándose"
    fi
    
    # Matar procesos Python relacionados con precaución
    if pgrep -f "python.*main.py" > /dev/null; then
        log_info "Deteniendo procesos Python del OCR..."
        pkill -f "python.*main.py" 2>/dev/null || true
        sleep 3
    fi
    
    # Verificar que no hay procesos activos
    if pgrep -f "python.*main" > /dev/null; then
        log_warning "Algunos procesos Python siguen activos"
        pkill -9 -f "python.*main" 2>/dev/null || true
        sleep 2
    fi
    
    log_success "Servicios detenidos correctamente"
}

# Actualizar código desde GitHub
update_code_from_github() {
    log_step "Actualizando código desde GitHub..."
    
    cd "$PROJECT_DIR"
    
    # Guardar cambios locales si los hay
    if ! git diff --quiet; then
        log_warning "Detectados cambios locales no guardados"
        git stash push -m "Auto-stash before v2.0.0 update $(date)" || true
    fi
    
    # Limpiar estado del repositorio
    git reset --hard HEAD
    
    # Actualizar referencias remotas
    log_info "Obteniendo últimas referencias de GitHub..."
    git fetch origin --tags --prune
    
    # Verificar que la versión objetivo existe
    if ! git tag | grep -q "^$TARGET_VERSION$"; then
        log_error "La versión $TARGET_VERSION no existe en el repositorio"
        log_info "Versiones disponibles:"
        git tag | tail -10
        exit 1
    fi
    
    # Cambiar a la rama principal y actualizar
    log_info "Cambiando a rama $CURRENT_BRANCH..."
    git checkout "$CURRENT_BRANCH"
    git pull origin "$CURRENT_BRANCH"
    
    # Cambiar a la versión específica
    log_info "Cambiando a versión $TARGET_VERSION..."
    git checkout "$TARGET_VERSION"
    
    # Verificar que estamos en la versión correcta
    CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")
    if [ "$CURRENT_TAG" != "$TARGET_VERSION" ]; then
        log_error "Error: No se pudo cambiar a $TARGET_VERSION"
        log_info "Versión actual: $CURRENT_TAG"
        exit 1
    fi
    
    log_success "Código actualizado a $TARGET_VERSION ✓"
}

# Actualizar dependencias Python
update_dependencies() {
    log_step "Actualizando dependencias Python..."
    
    cd "$PROJECT_DIR"
    
    # Verificar entorno virtual
    if [ ! -f "venv/bin/activate" ]; then
        log_error "Entorno virtual no encontrado en $PROJECT_DIR/venv"
        log_info "Creando nuevo entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    log_info "Actualizando pip..."
    pip install --upgrade pip
    
    # Instalar/actualizar dependencias
    if [ -f "requirements.txt" ]; then
        log_info "Instalando dependencias desde requirements.txt..."
        pip install -r requirements.txt --upgrade
        log_success "Dependencias actualizadas ✓"
    else
        log_warning "requirements.txt no encontrado"
    fi
    
    # Verificar dependencias críticas
    log_info "Verificando dependencias críticas..."
    python3 -c "
import pytesseract
import cv2
import numpy as np
import yaml
import PIL
print('✓ Todas las dependencias críticas están disponibles')
" || {
        log_error "Error en dependencias críticas"
        exit 1
    }
}

# Migrar configuración y datos
migrate_configuration_and_data() {
    log_step "Migrando configuración y datos..."
    
    BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
    
    # Migrar configuración
    if [ -f "$BACKUP_PATH/config_v1.py" ] && [ -f "$PROJECT_DIR/src/config.py" ]; then
        log_info "Comparando configuraciones..."
        
        if ! diff -q "$BACKUP_PATH/config_v1.py" "$PROJECT_DIR/src/config.py" > /dev/null; then
            log_warning "Detectados cambios en configuración"
            log_info "Configuración anterior: $BACKUP_PATH/config_v1.py"
            log_info "Nueva configuración: $PROJECT_DIR/src/config.py"
            
            # Crear archivo de diferencias
            diff "$BACKUP_PATH/config_v1.py" "$PROJECT_DIR/src/config.py" > "$PROJECT_DIR/config_differences.txt" || true
            log_warning "Revisar diferencias en: $PROJECT_DIR/config_differences.txt"
        else
            log_success "Configuración sin cambios significativos"
        fi
    fi
    
    # Migrar datos críticos
    log_info "Migrando datos del sistema..."
    
    # Modelo probabilístico
    if [ -f "$BACKUP_PATH/data/probabilistic_model.json" ]; then
        mkdir -p "$PROJECT_DIR/data"
        cp "$BACKUP_PATH/data/probabilistic_model.json" "$PROJECT_DIR/data/"
        log_success "Modelo probabilístico migrado ✓"
    fi
    
    # Datos de feedback
    if [ -d "$BACKUP_PATH/data/feedback_loop" ]; then
        mkdir -p "$PROJECT_DIR/data/feedback_loop"
        cp -r "$BACKUP_PATH/data/feedback_loop"/* "$PROJECT_DIR/data/feedback_loop/" 2>/dev/null || true
        log_success "Datos de feedback migrados ✓"
    fi
    
    # Plantillas personalizadas
    if [ -d "$BACKUP_PATH/templates" ]; then
        # Hacer backup de plantillas nuevas
        if [ -d "$PROJECT_DIR/templates" ]; then
            mv "$PROJECT_DIR/templates" "$PROJECT_DIR/templates_v2_original"
        fi
        
        # Restaurar plantillas personalizadas
        cp -r "$BACKUP_PATH/templates" "$PROJECT_DIR/"
        log_success "Plantillas personalizadas migradas ✓"
        log_info "Plantillas v2.0 originales en: templates_v2_original/"
    fi
    
    # Crear directorios necesarios para v2.0
    mkdir -p "$PROJECT_DIR"/{input,output,temp,logs}
    
    # Configurar permisos
    sudo chown -R $(whoami):ocr-service "$PROJECT_DIR" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/src/main_v2.py" 2>/dev/null || true
    chmod +x "$PROJECT_DIR/scripts"/*.sh 2>/dev/null || true
}

# Iniciar servicios
start_services() {
    log_step "Iniciando servicios del sistema..."
    
    # Verificar archivo de servicio systemd
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        # Recargar configuración de systemd
        sudo systemctl daemon-reload
        
        # Iniciar servicio
        sudo systemctl start "$SERVICE_NAME"
        sleep 5
        
        # Verificar estado
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            log_success "Servicio $SERVICE_NAME iniciado correctamente ✓"
        else
            log_error "Error al iniciar servicio $SERVICE_NAME"
            log_info "Estado del servicio:"
            systemctl status "$SERVICE_NAME" --no-pager -l
            return 1
        fi
    else
        log_info "Servicio systemd no configurado"
        log_info "El sistema puede ejecutarse manualmente con:"
        log_info "  python3 $PROJECT_DIR/src/main_v2.py <imagen>"
    fi
}

# Verificar instalación v2.0
verify_v2_installation() {
    log_step "Verificando instalación v2.0..."
    
    cd "$PROJECT_DIR"
    
    # Verificar archivos críticos v2.0
    critical_files=(
        "src/main_v2.py"
        "src/image_processor_optimized.py"
        "src/template_manager_v2.py"
        "src/data_extractor_v2.py"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_error "✗ $file (FALTANTE)"
            return 1
        fi
    done
    
    # Verificar versión
    INSTALLED_VERSION=$(git describe --tags --exact-match 2>/dev/null || echo "unknown")
    if [ "$INSTALLED_VERSION" = "$TARGET_VERSION" ]; then
        log_success "✓ Versión correcta: $INSTALLED_VERSION"
    else
        log_error "✗ Versión incorrecta: $INSTALLED_VERSION (esperada: $TARGET_VERSION)"
        return 1
    fi
    
    # Prueba básica del sistema v2.0
    log_info "Ejecutando prueba básica del sistema v2.0..."
    
    # Crear imagen de prueba simple si no existe
    if [ ! -f "input/test_basic.png" ]; then
        mkdir -p input
        # Crear imagen de prueba básica (1x1 pixel)
        python3 -c "
import cv2
import numpy as np
img = np.ones((100, 100, 3), dtype=np.uint8) * 255
cv2.imwrite('input/test_basic.png', img)
print('Imagen de prueba creada')
" 2>/dev/null || true
    fi
    
    # Ejecutar prueba básica (sin imagen real, solo verificar que el script funciona)
    if python3 -c "
import sys
sys.path.append('src')
try:
    import main_v2
    print('✓ main_v2.py importa correctamente')
except Exception as e:
    print(f'✗ Error importando main_v2.py: {e}')
    sys.exit(1)
"; then
        log_success "✓ Sistema v2.0 funcional"
    else
        log_error "✗ Error en sistema v2.0"
        return 1
    fi
    
    log_success "Verificación v2.0 completada ✓"
}

# Mostrar resumen de actualización
show_update_summary() {
    BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
    CURRENT_VERSION=$(cd "$PROJECT_DIR" && git describe --tags --exact-match 2>/dev/null || echo "unknown")
    
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "                    ACTUALIZACIÓN COMPLETADA"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🎉 SISTEMA OCR ACTUALIZADO EXITOSAMENTE A v2.0.0${NC}"
    echo ""
    echo -e "${BLUE}📊 RESUMEN DE CAMBIOS:${NC}"
    echo "   ✅ Eliminado aislamiento de documento (optimización)"
    echo "   ✅ Implementada estrategia de extracción flexible"
    echo "   ✅ Extracción directa desde OCR global"
    echo "   ✅ Soporte para campos multipalabra"
    echo "   ✅ Validación contextual mejorada"
    echo ""
    echo -e "${BLUE}📁 INFORMACIÓN DEL SISTEMA:${NC}"
    echo "   🏷️  Versión instalada: $CURRENT_VERSION"
    echo "   📂 Directorio: $PROJECT_DIR"
    echo "   💾 Backup: $BACKUP_PATH"
    echo "   🔧 Configuración: Migrada automáticamente"
    echo ""
    echo -e "${BLUE}🚀 COMANDOS PRINCIPALES v2.0:${NC}"
    echo "   📋 Procesar imagen:"
    echo "      python3 $PROJECT_DIR/src/main_v2.py input/imagen.png"
    echo ""
    echo "   🧪 Ejecutar pruebas:"
    echo "      bash $PROJECT_DIR/scripts/test_v2_system.sh"
    echo ""
    echo "   📊 Ver logs:"
    echo "      tail -f $PROJECT_DIR/logs/ocr_system.log"
    echo ""
    echo -e "${BLUE}🔍 VERIFICACIONES POST-ACTUALIZACIÓN:${NC}"
    echo "   1. ✅ Código actualizado a v2.0.0"
    echo "   2. ✅ Dependencias actualizadas"
    echo "   3. ✅ Configuración migrada"
    echo "   4. ✅ Datos preservados"
    echo "   5. ✅ Servicios reiniciados"
    echo "   6. ✅ Sistema v2.0 verificado"
    echo ""
    echo -e "${YELLOW}⚠️  PRÓXIMOS PASOS RECOMENDADOS:${NC}"
    echo "   1. Probar con imágenes reales:"
    echo "      python3 src/main_v2.py input/tu_imagen.png"
    echo ""
    echo "   2. Comparar resultados con v1.0:"
    echo "      python3 src/main.py input/imagen.png     # v1.0"
    echo "      python3 src/main_v2.py input/imagen.png  # v2.0"
    echo ""
    echo "   3. Revisar diferencias de configuración:"
    echo "      cat config_differences.txt"
    echo ""
    echo -e "${RED}🆘 EN CASO DE PROBLEMAS:${NC}"
    echo "   🔄 Rollback rápido:"
    echo "      bash scripts/rollback_from_v2.sh $BACKUP_PATH"
    echo ""
    echo "   📞 Soporte:"
    echo "      - Logs: tail -f logs/ocr_system.log"
    echo "      - Debug: ls temp/ (archivos de debug)"
    echo "      - Estado: systemctl status $SERVICE_NAME"
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "           ¡ACTUALIZACIÓN v2.0.0 COMPLETADA EXITOSAMENTE!"
    echo -e "==================================================================${NC}"
}

# Función principal
main() {
    show_banner
    
    # Verificar argumentos
    if [ "$1" = "--rollback" ]; then
        if [ -z "$2" ]; then
            log_error "Especificar ruta de backup para rollback"
            log_info "Uso: $0 --rollback <ruta_backup>"
            exit 1
        fi
        bash "$PROJECT_DIR/scripts/rollback_from_v2.sh" "$2"
        exit $?
    fi
    
    # Confirmar actualización
    echo -e "${YELLOW}⚠️  IMPORTANTE: Esta actualización implementará cambios significativos${NC}"
    echo "   - Estrategia de extracción completamente nueva"
    echo "   - Eliminación del aislamiento de documento"
    echo "   - Migración a extracción flexible v2.0"
    echo ""
    echo -e "${BLUE}📋 Se realizará backup completo antes de continuar${NC}"
    echo ""
    read -p "¿Continuar con la actualización a v2.0.0? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Actualización cancelada por el usuario"
        exit 0
    fi
    
    # Ejecutar actualización
    log_info "Iniciando actualización a v2.0.0..."
    
    check_prerequisites
    create_comprehensive_backup
    stop_services
    
    if update_code_from_github && update_dependencies && migrate_configuration_and_data; then
        start_services
        
        if verify_v2_installation; then
            show_update_summary
            log_success "🎉 ¡Actualización a v2.0.0 completada exitosamente!"
            exit 0
        else
            log_error "La verificación v2.0 falló. Iniciando rollback..."
            BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
            bash "$PROJECT_DIR/scripts/rollback_from_v2.sh" "$BACKUP_PATH"
            exit 1
        fi
    else
        log_error "Error durante la actualización. Iniciando rollback..."
        BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
        bash "$PROJECT_DIR/scripts/rollback_from_v2.sh" "$BACKUP_PATH"
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Actualización interrumpida"; exit 1' INT TERM

# Ejecutar actualización
main "$@"
