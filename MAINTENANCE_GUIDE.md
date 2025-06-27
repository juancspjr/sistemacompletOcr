# Guía de Mantenimiento y Soporte - Sistema OCR de Pagos Móviles

## Monitoreo del Sistema

### Verificación Diaria Automatizada

#### Script de Monitoreo Diario
\`\`\`bash
#!/bin/bash
# daily_monitor.sh - Monitoreo diario automatizado

LOG_FILE="/opt/ocr-pagos/logs/daily_monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] === MONITOREO DIARIO INICIADO ===" >> $LOG_FILE

# 1. Verificar estado del servicio
if systemctl is-active --quiet ocr-pagos; then
    echo "[$DATE] ✓ Servicio OCR activo" >> $LOG_FILE
else
    echo "[$DATE] ✗ ALERTA: Servicio OCR inactivo" >> $LOG_FILE
    # Intentar reiniciar
    sudo systemctl restart ocr-pagos
    sleep 5
    if systemctl is-active --quiet ocr-pagos; then
        echo "[$DATE] ✓ Servicio reiniciado exitosamente" >> $LOG_FILE
    else
        echo "[$DATE] ✗ ERROR CRÍTICO: No se pudo reiniciar el servicio" >> $LOG_FILE
    fi
fi

# 2. Verificar espacio en disco
DISK_USAGE=$(df /opt/ocr-pagos | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "[$DATE] ⚠ ALERTA: Uso de disco alto: ${DISK_USAGE}%" >> $LOG_FILE
else
    echo "[$DATE] ✓ Uso de disco: ${DISK_USAGE}%" >> $LOG_FILE
fi

# 3. Verificar memoria
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "[$DATE] ⚠ ALERTA: Uso de memoria alto: ${MEM_USAGE}%" >> $LOG_FILE
else
    echo "[$DATE] ✓ Uso de memoria: ${MEM_USAGE}%" >> $LOG_FILE
fi

# 4. Contar procesamiento últimas 24h
PROCESSED_COUNT=$(find /opt/ocr-pagos/data/processed_receipts/ -name "*.json" -mtime -1 | wc -l)
echo "[$DATE] ℹ Imágenes procesadas (24h): $PROCESSED_COUNT" >> $LOG_FILE

# 5. Verificar errores recientes
ERROR_COUNT=$(grep -c "ERROR" /opt/ocr-pagos/logs/system.log 2>/dev/null || echo "0")
if [ $ERROR_COUNT -gt 10 ]; then
    echo "[$DATE] ⚠ ALERTA: $ERROR_COUNT errores en logs" >> $LOG_FILE
else
    echo "[$DATE] ✓ Errores en logs: $ERROR_COUNT" >> $LOG_FILE
fi

# 6. Verificar feedback pendiente
if [ -f "/opt/ocr-pagos/data/feedback_loop/manual_feedback.csv" ]; then
    FEEDBACK_COUNT=$(wc -l < /opt/ocr-pagos/data/feedback_loop/manual_feedback.csv)
    if [ $FEEDBACK_COUNT -gt 1 ]; then  # Más de 1 línea (header)
        echo "[$DATE] ℹ Feedback pendiente: $((FEEDBACK_COUNT-1)) entradas" >> $LOG_FILE
    else
        echo "[$DATE] ✓ No hay feedback pendiente" >> $LOG_FILE
    fi
else
    echo "[$DATE] ✓ No hay feedback pendiente" >> $LOG_FILE
fi

echo "[$DATE] === MONITOREO DIARIO COMPLETADO ===" >> $LOG_FILE
echo "" >> $LOG_FILE
\`\`\`

#### Configurar Monitoreo Automático
\`\`\`bash
# Hacer ejecutable
chmod +x /opt/ocr-pagos/daily_monitor.sh

# Añadir a crontab
crontab -e

# Añadir línea para ejecutar cada día a las 8:00 AM
0 8 * * * /opt/ocr-pagos/daily_monitor.sh

# Verificar crontab
crontab -l
\`\`\`

### Dashboard de Monitoreo en Tiempo Real

#### Script de Estado del Sistema
\`\`\`bash
#!/bin/bash
# system_status.sh - Dashboard en tiempo real

clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SISTEMA OCR - DASHBOARD                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# Estado del servicio
echo "🔧 ESTADO DEL SERVICIO:"
if systemctl is-active --quiet ocr-pagos; then
    echo "   ✅ Servicio OCR: ACTIVO"
else
    echo "   ❌ Servicio OCR: INACTIVO"
fi

# Recursos del sistema
echo
echo "💻 RECURSOS DEL SISTEMA:"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% usado"
echo "   RAM: $(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "   Disco: $(df /opt/ocr-pagos | awk 'NR==2 {print $5}')"

# Estadísticas de procesamiento
echo
echo "📊 ESTADÍSTICAS DE PROCESAMIENTO:"
echo "   Hoy: $(find /opt/ocr-pagos/data/processed_receipts/ -name "*.json" -mtime -1 | wc -l) imágenes"
echo "   Esta semana: $(find /opt/ocr-pagos/data/processed_receipts/ -name "*.json" -mtime -7 | wc -l) imágenes"
echo "   Este mes: $(find /opt/ocr-pagos/data/processed_receipts/ -name "*.json" -mtime -30 | wc -l) imágenes"

# Últimos errores
echo
echo "🚨 ÚLTIMOS ERRORES:"
if [ -f "/opt/ocr-pagos/logs/system.log" ]; then
    tail -5 /opt/ocr-pagos/logs/system.log | grep "ERROR" | tail -3 || echo "   ✅ No hay errores recientes"
else
    echo "   ℹ️  Log no encontrado"
fi

# Feedback pendiente
echo
echo "📝 FEEDBACK PENDIENTE:"
if [ -f "/opt/ocr-pagos/data/feedback_loop/manual_feedback.csv" ]; then
    FEEDBACK_COUNT=$(wc -l < /opt/ocr-pagos/data/feedback_loop/manual_feedback.csv)
    if [ $FEEDBACK_COUNT -gt 1 ]; then
        echo "   ⚠️  $((FEEDBACK_COUNT-1)) correcciones pendientes"
    else
        echo "   ✅ No hay feedback pendiente"
    fi
else
    echo "   ✅ No hay feedback pendiente"
fi

echo
echo "🕐 Última actualización: $(date)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
\`\`\`

### Alertas por Email (Opcional)

#### Configurar Alertas
\`\`\`bash
# Instalar mailutils
sudo apt install -y mailutils

# Configurar script de alertas
cat > /opt/ocr-pagos/send_alert.sh << 'EOF'
#!/bin/bash
ALERT_TYPE=$1
MESSAGE=$2
EMAIL="admin@tudominio.com"

SUBJECT="[OCR System] Alerta: $ALERT_TYPE"
BODY="Fecha: $(date)
Sistema: $(hostname)
Alerta: $ALERT_TYPE

Detalles:
$MESSAGE

---
Sistema OCR de Pagos Móviles
"

echo "$BODY" | mail -s "$SUBJECT" "$EMAIL"
EOF

chmod +x /opt/ocr-pagos/send_alert.sh
\`\`\`

## Mantenimiento Periódico

### Limpieza Semanal Automatizada

#### Script de Limpieza
\`\`\`bash
#!/bin/bash
# weekly_cleanup.sh - Limpieza semanal automatizada

LOG_FILE="/opt/ocr-pagos/logs/maintenance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] === LIMPIEZA SEMANAL INICIADA ===" >> $LOG_FILE

# 1. Limpiar archivos temporales antiguos (>7 días)
TEMP_FILES_DELETED=$(find /opt/ocr-pagos/temp/ -type f -mtime +7 -delete -print | wc -l)
echo "[$DATE] Archivos temporales eliminados: $TEMP_FILES_DELETED" >> $LOG_FILE

# 2. Limpiar directorios temporales vacíos
find /opt/ocr-pagos/temp/ -type d -empty -delete
echo "[$DATE] Directorios temporales vacíos eliminados" >> $LOG_FILE

# 3. Comprimir logs antiguos (>30 días)
LOGS_COMPRESSED=$(find /opt/ocr-pagos/logs/ -name "*.log" -mtime +30 -exec gzip {} \; -print | wc -l)
echo "[$DATE] Logs comprimidos: $LOGS_COMPRESSED" >> $LOG_
