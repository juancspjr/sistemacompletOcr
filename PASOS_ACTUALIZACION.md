# Pasos para Actualizar Sistema OCR a v2.0.0

## Preparación Previa

### 1. Verificar Estado Actual del Sistema
\`\`\`bash
# Ir al directorio del proyecto
cd /opt/ocr-pagos

# Verificar versión actual
git describe --tags --always

# Verificar estado del servicio
sudo systemctl status ocr-pagos

# Verificar espacio en disco (necesario para backup)
df -h /opt/
\`\`\`

### 2. Configurar Repositorio GitHub (Si no está configurado)
\`\`\`bash
# Inicializar git si no existe
cd /opt/ocr-pagos
git init

# Configurar usuario
git config user.name "Tu Nombre"
git config user.email "tu-email@dominio.com"

# Añadir archivos al repositorio
git add .
git commit -m "Sistema OCR v1.0.0 - Estado actual"

# Conectar con GitHub (reemplaza con tu URL)
git remote add origin https://github.com/tu-usuario/sistema-ocr-pagos.git

# Subir código inicial
git branch -M main
git push -u origin main
\`\`\`

## Método 1: Actualización Automática (Recomendado)

### Paso 1: Descargar Script de Actualización
\`\`\`bash
# Ir al directorio del proyecto
cd /opt/ocr-pagos

# Hacer el script ejecutable
chmod +x scripts/deploy_v2.sh

# Verificar que el script existe
ls -la scripts/deploy_v2.sh
\`\`\`

### Paso 2: Ejecutar Actualización Automática
\`\`\`bash
# Ejecutar actualización (NO como root)
bash scripts/deploy_v2.sh

# El script hará automáticamente:
# - Backup completo del sistema actual
# - Descarga de v2.0.0 desde GitHub
# - Migración de configuración y datos
# - Verificación del sistema actualizado
\`\`\`

### Paso 3: Verificar Actualización
\`\`\`bash
# Verificar versión instalada
cd /opt/ocr-pagos
git describe --tags --exact-match

# Debería mostrar: v2.0.0

# Verificar servicio
sudo systemctl status ocr-pagos

# Probar sistema v2.0
python3 src/main_v2.py input/imagen_prueba.png
\`\`\`

## Método 2: Actualización Manual

### Paso 1: Crear Backup Manual
\`\`\`bash
# Crear directorio de backup
sudo mkdir -p /opt/ocr-backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="/opt/ocr-backups/backup_manual_$TIMESTAMP"

# Crear backup completo
sudo cp -r /opt/ocr-pagos "$BACKUP_PATH"

# Guardar información del backup
echo "Backup creado: $(date)" > "$BACKUP_PATH/backup_info.txt"
echo "Versión anterior: $(cd /opt/ocr-pagos && git describe --tags --always)" >> "$BACKUP_PATH/backup_info.txt"

echo "Backup creado en: $BACKUP_PATH"
\`\`\`

### Paso 2: Detener Servicios
\`\`\`bash
# Detener servicio OCR
sudo systemctl stop ocr-pagos

# Verificar que no hay procesos activos
ps aux | grep python | grep main
\`\`\`

### Paso 3: Actualizar Código
\`\`\`bash
cd /opt/ocr-pagos

# Guardar cambios locales si los hay
git stash push -m "Cambios locales antes de v2.0.0"

# Obtener última versión
git fetch origin --tags

# Cambiar a v2.0.0
git checkout v2.0.0

# Verificar versión
git describe --tags --exact-match
\`\`\`

### Paso 4: Actualizar Dependencias
\`\`\`bash
cd /opt/ocr-pagos

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar nuevas dependencias
pip install -r requirements.txt --upgrade
\`\`\`

### Paso 5: Migrar Datos
\`\`\`bash
# Los datos importantes se preservan automáticamente:
# - data/probabilistic_model.json
# - data/feedback_loop/
# - templates/ (plantillas personalizadas)

# Verificar que los datos están presentes
ls -la data/
ls -la templates/
\`\`\`

### Paso 6: Reiniciar Servicios
\`\`\`bash
# Recargar configuración systemd
sudo systemctl daemon-reload

# Iniciar servicio
sudo systemctl start ocr-pagos

# Verificar estado
sudo systemctl status ocr-pagos
\`\`\`

## Verificación Post-Actualización

### 1. Verificar Archivos Críticos v2.0
\`\`\`bash
cd /opt/ocr-pagos

# Verificar archivos principales v2.0
ls -la src/main_v2.py
ls -la src/image_processor_optimized.py
ls -la src/template_manager_v2.py
ls -la src/data_extractor_v2.py

# Todos deben existir
\`\`\`

### 2. Probar Funcionalidad Básica
\`\`\`bash
# Crear imagen de prueba si no existe
mkdir -p input

# Probar sistema v2.0 (sin imagen real, solo verificar que funciona)
python3 -c "
import sys
sys.path.append('src')
import main_v2
print('✓ Sistema v2.0 funcional')
"
\`\`\`

### 3. Comparar con Versión Anterior
\`\`\`bash
# Si tienes una imagen de prueba:
# Versión 1.0 (si está disponible)
python3 src/main.py input/imagen.png

# Versión 2.0
python3 src/main_v2.py input/imagen.png

# Comparar resultados
\`\`\`

## Solución de Problemas

### Si la Actualización Falla

#### Rollback Automático
\`\`\`bash
# Si usaste el script automático
BACKUP_PATH="/opt/ocr-backups/backup_pre_v2_[TIMESTAMP]"
bash scripts/rollback_from_v2.sh "$BACKUP_PATH"
\`\`\`

#### Rollback Manual
\`\`\`bash
# Detener servicios
sudo systemctl stop ocr-pagos

# Restaurar desde backup
BACKUP_PATH="/opt/ocr-backups/backup_manual_[TIMESTAMP]"
sudo rm -rf /opt/ocr-pagos
sudo cp -r "$BACKUP_PATH" /opt/ocr-pagos

# Restaurar permisos
sudo chown -R $(whoami):ocr-service /opt/ocr-pagos

# Reiniciar servicios
sudo systemctl start ocr-pagos
\`\`\`

### Problemas Comunes

#### Error: "No se puede conectar a GitHub"
\`\`\`bash
# Verificar conexión
ping github.com

# Verificar configuración git
git remote -v
\`\`\`

#### Error: "Dependencias faltantes"
\`\`\`bash
# Reinstalar dependencias
cd /opt/ocr-pagos
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
\`\`\`

#### Error: "Servicio no inicia"
\`\`\`bash
# Ver logs del servicio
sudo journalctl -u ocr-pagos -f

# Ver logs del sistema
tail -f logs/ocr_system.log
\`\`\`

## Comandos de Verificación Final

\`\`\`bash
# 1. Verificar versión
cd /opt/ocr-pagos
git describe --tags --exact-match
# Debe mostrar: v2.0.0

# 2. Verificar servicio
sudo systemctl is-active ocr-pagos
# Debe mostrar: active

# 3. Verificar logs
tail -5 logs/ocr_system.log

# 4. Probar procesamiento
python3 src/main_v2.py --help

# 5. Verificar estructura de archivos
ls -la src/main_v2.py src/image_processor_optimized.py
\`\`\`

## Diferencias Principales v2.0.0

### Cambios Arquitectónicos
- ✅ **Eliminado**: Aislamiento de documento
- ✅ **Añadido**: Extracción directa desde OCR global
- ✅ **Mejorado**: Soporte para campos multipalabra
- ✅ **Optimizado**: Validación contextual

### Nuevos Archivos
- `src/main_v2.py` - Punto de entrada v2.0
- `src/image_processor_optimized.py` - Procesamiento optimizado
- `src/template_manager_v2.py` - Gestión de plantillas v2.0
- `src/data_extractor_v2.py` - Extracción flexible

### Archivos Preservados
- `data/probabilistic_model.json` - Modelo de aprendizaje
- `data/feedback_loop/` - Datos de feedback
- `templates/` - Plantillas personalizadas
- `src/config.py` - Configuración (con posibles actualizaciones)

## Contacto y Soporte

Si encuentras problemas durante la actualización:

1. **Revisar logs**: `tail -f logs/ocr_system.log`
2. **Verificar estado**: `systemctl status ocr-pagos`
3. **Rollback si es necesario**: Usar comandos de rollback arriba
4. **Documentar el problema**: Guardar logs y mensajes de error

La actualización a v2.0.0 mejora significativamente la precisión y flexibilidad del sistema OCR.
\`\`\`

```shellscript file="scripts/quick_update.sh"
#!/bin/bash

# Script de Actualización Rápida a v2.0.0
# Para usuarios que quieren actualizar sin configuración compleja

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Actualización Rápida OCR v2.0.0${NC}"
echo "=================================="

# Verificar directorio
if [ ! -d "/opt/ocr-pagos" ]; then
    echo -e "${RED}❌ Directorio /opt/ocr-pagos no encontrado${NC}"
    exit 1
fi

cd /opt/ocr-pagos

# Crear backup rápido
echo -e "${BLUE}📦 Creando backup...${NC}"
BACKUP_DIR="/tmp/ocr_backup_$(date +%Y%m%d_%H%M%S)"
cp -r /opt/ocr-pagos "$BACKUP_DIR"
echo -e "${GREEN}✅ Backup en: $BACKUP_DIR${NC}"

# Detener servicios
echo -e "${BLUE}⏹️  Deteniendo servicios...${NC}"
sudo systemctl stop ocr-pagos 2>/dev/null || true

# Actualizar código
echo -e "${BLUE}📥 Descargando v2.0.0...${NC}"
git fetch origin --tags
git checkout v2.0.0

# Actualizar dependencias
echo -e "${BLUE}📚 Actualizando dependencias...${NC}"
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Reiniciar servicios
echo -e "${BLUE}▶️  Reiniciando servicios...${NC}"
sudo systemctl start ocr-pagos 2>/dev/null || true

# Verificar
echo -e "${BLUE}🔍 Verificando instalación...${NC}"
VERSION=$(git describe --tags --exact-match 2>/dev/null || echo "error")

if [ "$VERSION" = "v2.0.0" ]; then
    echo -e "${GREEN}🎉 ¡Actualización exitosa a v2.0.0!${NC}"
    echo -e "${YELLOW}📋 Probar con: python3 src/main_v2.py input/imagen.png${NC}"
    echo -e "${YELLOW}🔄 Rollback: cp -r $BACKUP_DIR /opt/ocr-pagos${NC}"
else
    echo -e "${RED}❌ Error en actualización${NC}"
    echo -e "${YELLOW}🔄 Restaurando backup...${NC}"
    sudo systemctl stop ocr-pagos 2>/dev/null || true
    rm -rf /opt/ocr-pagos
    cp -r "$BACKUP_DIR" /opt/ocr-pagos
    sudo systemctl start ocr-pagos 2>/dev/null || true
    exit 1
fi
