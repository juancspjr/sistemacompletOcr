#!/bin/bash

# Script de Despliegue OCR v2.0.0 - Versión Corregida
# Actualiza el sistema local o en /opt/ocr-pagos

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Variables de configuración
DEFAULT_PROJECT_DIR="/opt/ocr-pagos"
CURRENT_DIR="$(pwd)"
BACKUP_DIR="/opt/ocr-backups"
SERVICE_NAME="ocr-pagos"

# Detectar directorio del proyecto
if [ -f "$CURRENT_DIR/src/main_v2.py" ]; then
    PROJECT_DIR="$CURRENT_DIR"
    log_info "Usando directorio actual: $PROJECT_DIR"
elif [ -d "$DEFAULT_PROJECT_DIR" ] && [ -f "$DEFAULT_PROJECT_DIR/src/main.py" ]; then
    PROJECT_DIR="$DEFAULT_PROJECT_DIR"
    log_info "Usando directorio estándar: $PROJECT_DIR"
else
    log_error "No se encontró instalación OCR válida"
    log_info "Ejecutar primero: bash scripts/quick_setup.sh"
    exit 1
fi

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
    echo "📂 Directorio: $PROJECT_DIR"
    echo "⚡ Actualización segura con backup automático"
    echo ""
}

# Verificar prerrequisitos
check_prerequisites() {
    log_step "Verificando prerrequisitos del sistema..."
    
    # Verificar directorio del proyecto
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Directorio del proyecto no encontrado: $PROJECT_DIR"
        exit 1
    fi
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 no está instalado"
        exit 1
    fi
    
    # Verificar archivos v2.0 en directorio actual
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ] && [ ! -f "$CURRENT_DIR/src/main_v2.py" ]; then
        log_error "Archivos v2.0 no encontrados en directorio actual"
        log_info "Ejecutar primero: bash scripts/quick_setup.sh"
        exit 1
    fi
    
    log_success "Prerrequisitos verificados ✓"
}

# Crear backup del sistema actual
create_backup() {
    log_step "Creando backup del sistema actual..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ]; then
        # Backup completo para instalación en /opt
        BACKUP_PATH="$BACKUP_DIR/backup_pre_v2_$TIMESTAMP"
        mkdir -p "$BACKUP_PATH"
        
        cd "$PROJECT_DIR"
        
        # Backup completo del código
        log_info "Copiando código fuente..."
        cp -r "$PROJECT_DIR" "$BACKUP_PATH/code"
        
        # Backup de datos críticos
        [ -d "$PROJECT_DIR/data" ] && cp -r "$PROJECT_DIR/data" "$BACKUP_PATH/"
        [ -f "$PROJECT_DIR/src/config.py" ] && cp "$PROJECT_DIR/src/config.py" "$BACKUP_PATH/config_v1.py"
        
        log_success "Backup completo creado en: $BACKUP_PATH"
        echo "$BACKUP_PATH" > /tmp/ocr_backup_path_v2
    else
        # Backup local
        BACKUP_PATH="$PROJECT_DIR/backup_pre_v2_$TIMESTAMP"
        mkdir -p "$BACKUP_PATH"
        
        # Backup de archivos importantes
        [ -d "src" ] && cp -r src "$BACKUP_PATH/"
        [ -d "data" ] && cp -r data "$BACKUP_PATH/"
        [ -d "templates" ] && cp -r templates "$BACKUP_PATH/"
        
        log_success "Backup local creado en: $BACKUP_PATH"
        echo "$BACKUP_PATH" > /tmp/ocr_backup_path_v2
    fi
}

# Crear script de rollback
create_rollback_script() {
    local backup_path="$1"
    
    mkdir -p "$PROJECT_DIR/scripts"
    
    cat > "$PROJECT_DIR/scripts/rollback_from_v2.sh" << EOF
#!/bin/bash

# Script de Rollback desde v2.0.0
# Restaura el sistema a la versión anterior

BACKUP_PATH="\$1"

if [ -z "\$BACKUP_PATH" ] || [ ! -d "\$BACKUP_PATH" ]; then
    echo "ERROR: Ruta de backup no válida"
    echo "Uso: \$0 <ruta_backup>"
    exit 1
fi

echo "🔄 Iniciando rollback desde v2.0.0..."
echo "📁 Backup: \$BACKUP_PATH"

# Detener servicios si existen
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Restaurar código
echo "📦 Restaurando código..."
if [ -d "\$BACKUP_PATH/code" ]; then
    # Restauración completa
    rm -rf $PROJECT_DIR
    cp -r "\$BACKUP_PATH/code" $PROJECT_DIR
else
    # Restauración local
    [ -d "\$BACKUP_PATH/src" ] && rm -rf src && cp -r "\$BACKUP_PATH/src" .
    [ -d "\$BACKUP_PATH/data" ] && rm -rf data && cp -r "\$BACKUP_PATH/data" .
    [ -d "\$BACKUP_PATH/templates" ] && rm -rf templates && cp -r "\$BACKUP_PATH/templates" .
fi

# Restaurar permisos
sudo chown -R \$(whoami):ocr-service $PROJECT_DIR 2>/dev/null || true

# Reiniciar servicios
sudo systemctl start $SERVICE_NAME 2>/dev/null || true

echo "✅ Rollback completado"
echo "📋 Verificar: systemctl status $SERVICE_NAME"
EOF
    
    chmod +x "$PROJECT_DIR/scripts/rollback_from_v2.sh"
}

# Detener servicios del sistema
stop_services() {
    log_step "Deteniendo servicios del sistema..."
    
    # Solo intentar detener servicios si estamos en /opt
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ]; then
        # Detener servicio systemd si existe
        if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
            sudo systemctl stop "$SERVICE_NAME"
            log_success "Servicio $SERVICE_NAME detenido"
        else
            log_info "Servicio $SERVICE_NAME no estaba ejecutándose"
        fi
        
        # Matar procesos Python relacionados
        if pgrep -f "python.*main.py" > /dev/null; then
            log_info "Deteniendo procesos Python del OCR..."
            pkill -f "python.*main.py" 2>/dev/null || true
            sleep 3
        fi
    else
        log_info "Instalación local, omitiendo detención de servicios"
    fi
    
    log_success "Servicios gestionados correctamente"
}

# Actualizar código
update_code() {
    log_step "Actualizando código a v2.0.0..."
    
    cd "$PROJECT_DIR"
    
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ]; then
        # Actualización desde directorio actual a /opt
        log_info "Copiando archivos v2.0 desde $CURRENT_DIR..."
        
        # Copiar archivos principales
        cp -r "$CURRENT_DIR/src"/* src/ 2>/dev/null || true
        cp -r "$CURRENT_DIR/scripts"/* scripts/ 2>/dev/null || true
        cp -r "$CURRENT_DIR/templates"/* templates/ 2>/dev/null || true
        
        # Copiar archivos de configuración
        [ -f "$CURRENT_DIR/requirements.txt" ] && cp "$CURRENT_DIR/requirements.txt" .
        
    else
        # Actualización local (ya debería estar actualizado por quick_setup.sh)
        log_info "Verificando archivos v2.0 locales..."
        
        if [ ! -f "src/main_v2.py" ]; then
            log_error "Archivos v2.0 no encontrados"
            log_info "Ejecutar primero: bash scripts/quick_setup.sh"
            exit 1
        fi
    fi
    
    # Hacer ejecutables los scripts
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x src/main*.py 2>/dev/null || true
    
    log_success "Código actualizado a v2.0.0 ✓"
}

# Actualizar dependencias Python
update_dependencies() {
    log_step "Actualizando dependencias Python..."
    
    cd "$PROJECT_DIR"
    
    # Verificar/crear entorno virtual
    if [ ! -f "venv/bin/activate" ]; then
        log_info "Creando entorno virtual..."
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
migrate_data() {
    log_step "Migrando configuración y datos..."
    
    BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
    
    # Migrar datos críticos
    log_info "Migrando datos del sistema..."
    
    # Crear directorios necesarios
    mkdir -p {input,output,temp,logs,data}
    
    # Modelo probabilístico
    if [ -f "$BACKUP_PATH/data/probabilistic_model.json" ]; then
        cp "$BACKUP_PATH/data/probabilistic_model.json" data/
        log_success "Modelo probabilístico migrado ✓"
    elif [ -f "$BACKUP_PATH/probabilistic_model.json" ]; then
        cp "$BACKUP_PATH/probabilistic_model.json" data/
        log_success "Modelo probabilístico migrado ✓"
    fi
    
    # Configurar permisos
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ]; then
        sudo chown -R $(whoami):ocr-service "$PROJECT_DIR" 2>/dev/null || true
    fi
}

# Iniciar servicios
start_services() {
    log_step "Iniciando servicios del sistema..."
    
    # Solo para instalación en /opt
    if [ "$PROJECT_DIR" = "$DEFAULT_PROJECT_DIR" ]; then
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
                systemctl status "$SERVICE_NAME" --no-pager -l
                return 1
            fi
        else
            log_info "Servicio systemd no configurado"
        fi
    else
        log_info "Instalación local, servicios no aplicables"
    fi
    
    log_info "El sistema puede ejecutarse con:"
    log_info "  python3 $PROJECT_DIR/src/main_v2.py <imagen>"
}

# Verificar instalación v2.0
verify_installation() {
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
    
    # Prueba básica del sistema v2.0
    log_info "Ejecutando prueba básica del sistema v2.0..."
    
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
show_summary() {
    BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
    
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "                    ACTUALIZACIÓN COMPLETADA"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🎉 SISTEMA OCR ACTUALIZADO EXITOSAMENTE A v2.0.0${NC}"
    echo ""
    echo -e "${BLUE}📁 INFORMACIÓN DEL SISTEMA:${NC}"
    echo "   📂 Directorio: $PROJECT_DIR"
    echo "   💾 Backup: $BACKUP_PATH"
    echo ""
    echo -e "${BLUE}🚀 COMANDOS PRINCIPALES v2.0:${NC}"
    echo "   📋 Procesar imagen:"
    echo "      python3 $PROJECT_DIR/src/main_v2.py input/imagen.png"
    echo ""
    echo "   🧪 Ejecutar pruebas:"
    echo "      bash $PROJECT_DIR/scripts/test_v2_system.sh"
    echo ""
    echo -e "${RED}🆘 EN CASO DE PROBLEMAS:${NC}"
    echo "   🔄 Rollback:"
    echo "      bash $PROJECT_DIR/scripts/rollback_from_v2.sh $BACKUP_PATH"
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "           ¡ACTUALIZACIÓN v2.0.0 COMPLETADA EXITOSAMENTE!"
    echo -e "==================================================================${NC}"
}

# Función principal
main() {
    show_banner
    
    # Confirmar actualización
    echo -e "${YELLOW}⚠️  Esta actualización implementará cambios significativos${NC}"
    echo "   - Estrategia de extracción completamente nueva"
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
    create_backup
    BACKUP_PATH=$(cat /tmp/ocr_backup_path_v2)
    create_rollback_script "$BACKUP_PATH"
    stop_services
    
    if update_code && update_dependencies && migrate_data; then
        start_services
        
        if verify_installation; then
            show_summary
            log_success "🎉 ¡Actualización a v2.0.0 completada exitosamente!"
            exit 0
        else
            log_error "La verificación v2.0 falló. Iniciando rollback..."
            bash "$PROJECT_DIR/scripts/rollback_from_v2.sh" "$BACKUP_PATH"
            exit 1
        fi
    else
        log_error "Error durante la actualización. Iniciando rollback..."
        bash "$PROJECT_DIR/scripts/rollback_from_v2.sh" "$BACKUP_PATH"
        exit 1
    fi
}

# Manejo de señales
trap 'log_error "Actualización interrumpida"; exit 1' INT TERM

# Ejecutar actualización
main "$@"
