#!/bin/bash

# Script de Instalación del Sistema OCR v2.0.0
# Para instalación en /opt/ocr-pagos con servicios systemd

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
INSTALL_DIR="/opt/ocr-pagos"
SERVICE_NAME="ocr-pagos"
SERVICE_USER="ocr-service"
TEMP_DIR="/tmp/ocr_system_install_$$"

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

# Verificar permisos de root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script debe ejecutarse como root"
        log_info "Usar: sudo $0"
        exit 1
    fi
}

# Crear usuario del sistema
create_system_user() {
    log_step "Creando usuario del sistema..."
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "Usuario $SERVICE_USER ya existe"
    else
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        log_success "Usuario $SERVICE_USER creado"
    fi
}

# Instalar dependencias del sistema
install_system_dependencies() {
    log_step "Instalando dependencias del sistema..."
    
    apt-get update
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        tesseract-ocr \
        tesseract-ocr-spa \
        libtesseract-dev \
        libopencv-dev \
        python3-opencv \
        build-essential \
        pkg-config \
        supervisor
    
    log_success "Dependencias del sistema instaladas"
}

# Descargar e instalar código
install_application() {
    log_step "Descargando e instalando aplicación..."
    
    # Limpiar directorio temporal
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    
    # Clonar repositorio
    git clone "$REPO_URL" "$TEMP_DIR"
    
    # Crear directorio de instalación
    mkdir -p "$INSTALL_DIR"
    
    # Copiar archivos
    cp -r "$TEMP_DIR"/* "$INSTALL_DIR/"
    
    # Crear directorios necesarios
    mkdir -p "$INSTALL_DIR"/{input,output,temp,logs,data}
    
    # Configurar permisos
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod +x "$INSTALL_DIR"/scripts/*.sh
    chmod +x "$INSTALL_DIR"/src/main*.py
    
    log_success "Aplicación instalada en $INSTALL_DIR"
}

# Configurar entorno Python
setup_python_environment() {
    log_step "Configurando entorno Python..."
    
    cd "$INSTALL_DIR"
    
    # Crear entorno virtual como usuario del servicio
    sudo -u "$SERVICE_USER" python3 -m venv venv
    
    # Instalar dependencias
    sudo -u "$SERVICE_USER" bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    "
    
    log_success "Entorno Python configurado"
}

# Crear servicio systemd
create_systemd_service() {
    log_step "Creando servicio systemd..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" &lt;&lt; EOF
[Unit]
Description=Sistema OCR de Pagos Móviles v2.0.0
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/main_v2.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Recargar systemd
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    log_success "Servicio systemd creado y habilitado"
}

# Configurar logrotate
setup_logrotate() {
    log_step "Configurando rotación de logs..."
    
    cat > "/etc/logrotate.d/$SERVICE_NAME" &lt;&lt; EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_success "Rotación de logs configurada"
}

# Verificar instalación
verify_installation() {
    log_step "Verificando instalación..."
    
    cd "$INSTALL_DIR"
    
    # Verificar archivos críticos
    critical_files=(
        "src/main_v2.py"
        "src/config.py"
        "requirements.txt"
        "venv/bin/python"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file"
        else
            log_error "✗ $file (FALTANTE)"
            return 1
        fi
    done
    
    # Verificar importaciones Python
    sudo -u "$SERVICE_USER" bash -c "
        source venv/bin/activate
        cd src
        python3 -c 'import main_v2; print(\"✓ main_v2.py funcional\")'
    "
    
    log_success "Instalación verificada"
}

# Mostrar resumen final
show_final_summary() {
    echo ""
    echo -e "${PURPLE}=================================================================="
    echo "                INSTALACIÓN DEL SISTEMA COMPLETADA"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}🎉 SISTEMA OCR v2.0.0 INSTALADO COMO SERVICIO${NC}"
    echo ""
    echo -e "${BLUE}📁 DIRECTORIO: $INSTALL_DIR${NC}"
    echo -e "${BLUE}👤 USUARIO: $SERVICE_USER${NC}"
    echo -e "${BLUE}🔧 SERVICIO: $SERVICE_NAME${NC}"
    echo ""
    echo -e "${BLUE}🚀 COMANDOS DE ADMINISTRACIÓN:${NC}"
    echo "   systemctl start $SERVICE_NAME     # Iniciar servicio"
    echo "   systemctl stop $SERVICE_NAME      # Detener servicio"
    echo "   systemctl status $SERVICE_NAME    # Ver estado"
    echo "   systemctl restart $SERVICE_NAME   # Reiniciar servicio"
    echo ""
    echo -e "${BLUE}📋 COMANDOS DE USO:${NC}"
    echo "   sudo -u $SERVICE_USER bash"
    echo "   cd $INSTALL_DIR"
    echo "   source venv/bin/activate"
    echo "   python3 src/main_v2.py input/imagen.png"
    echo ""
    echo -e "${BLUE}📂 DIRECTORIOS IMPORTANTES:${NC}"
    echo "   $INSTALL_DIR/input/    # Imágenes de entrada"
    echo "   $INSTALL_DIR/temp/     # Resultados temporales"
    echo "   $INSTALL_DIR/logs/     # Logs del sistema"
    echo ""
    echo -e "${BLUE}📊 LOGS:${NC}"
    echo "   journalctl -u $SERVICE_NAME -f    # Logs del servicio"
    echo "   tail -f $INSTALL_DIR/logs/system.log  # Logs de la aplicación"
    echo ""
    echo -e "${GREEN}✅ ¡Sistema listo para usar!${NC}"
    echo -e "${PURPLE}==================================================================${NC}"
}

# Función principal
main() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "           INSTALACIÓN DEL SISTEMA OCR v2.0.0"
    echo "=================================================================="
    echo -e "${NC}"
    echo "🔧 Instalación completa en /opt/ocr-pagos"
    echo "👤 Usuario del sistema: $SERVICE_USER"
    echo "🔧 Servicio systemd: $SERVICE_NAME"
    echo ""
    
    read -p "¿Continuar con la instalación del sistema? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Instalación cancelada"
        exit 0
    fi
    
    check_root
    install_system_dependencies
    create_system_user
    install_application
    setup_python_environment
    create_systemd_service
    setup_logrotate
    
    if verify_installation; then
        # Limpiar archivos temporales
        rm -rf "$TEMP_DIR"
        
        show_final_summary
        log_success "🎉 ¡Instalación del sistema completada!"
        
        # Preguntar si iniciar el servicio
        read -p "¿Iniciar el servicio ahora? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            systemctl start "$SERVICE_NAME"
            sleep 3
            systemctl status "$SERVICE_NAME" --no-pager
        fi
        
        exit 0
    else
        log_error "La verificación falló"
        exit 1
    fi
}

# Ejecutar instalación
main "$@"
