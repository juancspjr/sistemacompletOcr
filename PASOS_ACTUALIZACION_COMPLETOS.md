# Guía Completa de Actualización OCR v2.0.0

## 🚀 Comando Inicial Rápido

Para empezar desde cero o sincronizar con GitHub:

\`\`\`bash
# Descargar este comando y ejecutar
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/quick_setup.sh | bash
\`\`\`

O manualmente:

\`\`\`bash
# 1. Crear directorio y descargar script inicial
mkdir -p ocr-system && cd ocr-system
wget https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/quick_setup.sh
chmod +x quick_setup.sh

# 2. Ejecutar configuración automática
./quick_setup.sh
\`\`\`

## 📋 Opciones de Actualización

### Opción 1: Configuración Inicial Completa (Recomendada)

\`\`\`bash
# Descarga todo desde GitHub y configura localmente
bash scripts/quick_setup.sh
\`\`\`

**¿Qué hace?**
- ✅ Descarga código completo desde GitHub
- ✅ Crea backup de archivos existentes
- ✅ Configura entorno Python
- ✅ Instala dependencias
- ✅ Verifica funcionamiento
- ✅ Preserva datos locales importantes

### Opción 2: Actualización de Sistema Existente

\`\`\`bash
# Si ya tienes instalación en /opt/ocr-pagos
bash scripts/deploy_v2_fixed.sh
\`\`\`

**¿Qué hace?**
- ✅ Detecta instalación existente
- ✅ Crea backup completo
- ✅ Actualiza a v2.0.0
- ✅ Migra configuración y datos
- ✅ Reinicia servicios

### Opción 3: Solo Sincronizar Archivos

\`\`\`bash
# Solo descargar archivos sin configurar
git clone https://github.com/juancspjr/sistemacompletOcr.git
cd sistemacompletOcr
\`\`\`

## 🔧 Pasos Detallados Manuales

### 1. Preparación del Sistema

\`\`\`bash
# Verificar prerrequisitos
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Verificar versiones
python3 --version  # Debe ser 3.7+
git --version
\`\`\`

### 2. Descarga del Código

\`\`\`bash
# Opción A: Clonar repositorio completo
git clone https://github.com/juancspjr/sistemacompletOcr.git
cd sistemacompletOcr

# Opción B: Descargar solo archivos necesarios
mkdir ocr-v2 && cd ocr-v2
wget -r --no-parent --reject="index.html*" \
  https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/
\`\`\`

### 3. Configuración del Entorno

\`\`\`bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalación
python3 -c "import cv2, pytesseract, yaml; print('✓ Dependencias OK')"
\`\`\`

### 4. Configuración de Directorios

\`\`\`bash
# Crear estructura necesaria
mkdir -p {input,output,temp,logs,data}

# Configurar permisos
chmod +x scripts/*.sh
chmod +x src/main*.py
\`\`\`

### 5. Migración de Datos (Si Aplica)

\`\`\`bash
# Si tienes instalación anterior
cp /ruta/anterior/data/probabilistic_model.json data/
cp /ruta/anterior/templates/* templates/
cp /ruta/anterior/src/config.py config_backup.py
\`\`\`

### 6. Verificación del Sistema

\`\`\`bash
# Probar importación
python3 -c "
import sys
sys.path.append('src')
import main_v2
print('✓ Sistema v2.0 funcional')
"

# Probar con imagen de prueba
python3 src/main_v2.py --help
\`\`\`

## 🛠️ Solución de Problemas Comunes

### Error: "No such file or directory"

\`\`\`bash
# Verificar estructura de directorios
ls -la scripts/
ls -la src/

# Recrear directorios faltantes
mkdir -p scripts src data templates input output temp logs
\`\`\`

### Error: "Module not found"

\`\`\`bash
# Reinstalar dependencias
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Verificar PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"
\`\`\`

### Error: "Permission denied"

\`\`\`bash
# Corregir permisos
chmod +x scripts/*.sh
chmod +x src/*.py
sudo chown -R $USER:$USER .
\`\`\`

### Error de Conexión a GitHub

\`\`\`bash
# Verificar conectividad
ping github.com

# Usar HTTPS en lugar de SSH
git remote set-url origin https://github.com/juancspjr/sistemacompletOcr.git
\`\`\`

## 📊 Verificación Post-Instalación

### Verificar Archivos Críticos

\`\`\`bash
# Verificar archivos v2.0
ls -la src/main_v2.py
ls -la src/image_processor_optimized.py
ls -la src/template_manager_v2.py
ls -la src/data_extractor_v2.py
\`\`\`

### Probar Funcionalidad Básica

\`\`\`bash
# Crear imagen de prueba
python3 -c "
import cv2
import numpy as np
img = np.ones((100, 100, 3), dtype=np.uint8) * 255
cv2.imwrite('input/test.png', img)
print('Imagen de prueba creada')
"

# Probar procesamiento
python3 src/main_v2.py input/test.png
\`\`\`

### Verificar Logs

\`\`\`bash
# Ver logs del sistema
tail -f logs/ocr_system.log

# Ver archivos temporales
ls -la temp/
\`\`\`

## 🔄 Rollback en Caso de Problemas

### Rollback Automático

\`\`\`bash
# Si usaste deploy_v2_fixed.sh
bash scripts/rollback_from_v2.sh /ruta/del/backup
\`\`\`

### Rollback Manual

\`\`\`bash
# Restaurar desde backup
cp -r backup_pre_v2_*/src/* src/
cp -r backup_pre_v2_*/data/* data/
cp -r backup_pre_v2_*/templates/* templates/

# Reinstalar dependencias anteriores
pip install -r backup_pre_v2_*/requirements.txt
\`\`\`

## 📞 Soporte y Ayuda

### Información del Sistema

\`\`\`bash
# Ver versión actual
cd src && python3 -c "print('OCR v2.0.0')"

# Ver configuración
cat src/config.py

# Ver estado de servicios (si aplica)
systemctl status ocr-pagos
\`\`\`

### Logs de Debug

\`\`\`bash
# Habilitar debug
export OCR_DEBUG=1
python3 src/main_v2.py input/imagen.png

# Ver logs detallados
tail -f logs/debug.log
\`\`\`

### Contacto

- 📧 Reportar problemas: GitHub Issues
- 📖 Documentación: README.md
- 🔧 Configuración: src/config.py

---

## ✅ Resumen de Comandos Esenciales

\`\`\`bash
# 🚀 INICIO RÁPIDO (Recomendado)
bash scripts/quick_setup.sh

# 🔄 ACTUALIZACIÓN EXISTENTE
bash scripts/deploy_v2_fixed.sh

# 🧪 PROBAR SISTEMA
python3 src/main_v2.py input/imagen.png

# 📊 VER LOGS
tail -f logs/ocr_system.log

# 🆘 ROLLBACK
bash scripts/rollback_from_v2.sh /ruta/backup
