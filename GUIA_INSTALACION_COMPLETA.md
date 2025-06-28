# 🚀 GUÍA COMPLETA DE INSTALACIÓN OCR v2.0.0

## 📋 Resumen Ejecutivo

Esta guía te llevará paso a paso para instalar el Sistema OCR v2.0.0 completamente desde cero, eliminando cualquier instalación previa y asegurando que todo funcione perfectamente.

## 🧹 PASO 1: Limpieza Completa del Sistema

### 1.1 Eliminar Instalaciones Previas

\`\`\`bash
# Detener servicios relacionados
sudo systemctl stop ocr-pagos 2>/dev/null || true
sudo systemctl disable ocr-pagos 2>/dev/null || true

# Eliminar directorios de instalación
sudo rm -rf /opt/ocr-pagos
sudo rm -rf /opt/ocr-backups
rm -rf ~/ocr-*
rm -rf ~/sistemacompletOcr

# Limpiar servicios systemd
sudo rm -f /etc/systemd/system/ocr-pagos.service
sudo systemctl daemon-reload

# Limpiar procesos
pkill -f "python.*main" 2>/dev/null || true
pkill -f "python.*ocr" 2>/dev/null || true

# Limpiar archivos temporales
sudo rm -rf /tmp/ocr_*
sudo rm -rf /tmp/tesseract_*

echo "✅ Limpieza completa terminada"
\`\`\`

### 1.2 Verificar Limpieza

\`\`\`bash
# Verificar que no queden procesos
ps aux | grep -i ocr
ps aux | grep -i tesseract

# Verificar directorios
ls -la /opt/ | grep ocr
ls -la ~/ | grep ocr

# Verificar servicios
systemctl list-units | grep ocr
\`\`\`

## 🔧 PASO 2: Preparación del Sistema

### 2.1 Actualizar Sistema Base

\`\`\`bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    pkg-config
\`\`\`

### 2.2 Instalar Tesseract OCR

\`\`\`bash
# Instalar Tesseract con soporte para español
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev

# Verificar instalación
tesseract --version
tesseract --list-langs | grep spa
\`\`\`

### 2.3 Instalar OpenCV

\`\`\`bash
# Instalar OpenCV
sudo apt install -y \
    libopencv-dev \
    python3-opencv

# Verificar instalación
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
\`\`\`

## 🚀 PASO 3: Instalación del Sistema

### Opción A: Instalación Personal (Recomendada para desarrollo)

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

### Opción B: Instalación del Sistema (Para producción)

\`\`\`bash
# 1. Descargar script de instalación del sistema
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/scripts/install_system.sh -o install_system.sh

# 2. Ejecutar como root
chmod +x install_system.sh
sudo ./install_system.sh
\`\`\`

## ✅ PASO 4: Verificación de la Instalación

### 4.1 Verificación Básica

\`\`\`bash
# Para instalación personal
cd ~/ocr-sistema-v2
source venv/bin/activate

# Para instalación del sistema
sudo -u ocr-service bash
cd /opt/ocr-pagos
source venv/bin/activate

# Verificar estructura
ls -la
echo "Debe mostrar: src/, data/, templates/, scripts/, venv/, input/, logs/"

# Verificar importaciones
python3 -c "
import sys
sys.path.append('src')

try:
    import config
    print('✅ config.py - OK')
    print(f'Versión: {config.VERSION}')
except Exception as e:
    print(f'❌ config.py - ERROR: {e}')

try:
    import main_v2
    print('✅ main_v2.py - OK')
except Exception as e:
    print(f'❌ main_v2.py - ERROR: {e}')
"
\`\`\`

### 4.2 Prueba Funcional

\`\`\`bash
# Crear imagen de prueba
python3 -c "
from PIL import Image, ImageDraw
import os

os.makedirs('input', exist_ok=True)
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)

text_lines = [
    'COMPROBANTE DE PAGO MÓVIL',
    'Banco: Banco de Venezuela',
    'Fecha: 28/12/2024',
    'Monto: Bs. 150.000,00',
    'Referencia: 123456789',
    'C.I.: 12.345.678'
]

y = 50
for line in text_lines:
    draw.text((50, y), line, fill='black')
    y += 60

img.save('input/test.png')
print('✅ Imagen de prueba creada')
"

# Procesar imagen de prueba
python3 src/main_v2.py input/test.png

# Verificar resultados
ls temp/test_*/
cat temp/test_*/extraction_summary_v2.json
\`\`\`

## 🔧 PASO 5: Configuración Avanzada

### 5.1 Configurar Variables de Entorno

\`\`\`bash
# Para modo debug
export OCR_DEBUG=1

# Para configuración personalizada
cp src/config.py src/config_backup.py
# Editar src/config.py según necesidades
\`\`\`

### 5.2 Configurar Servicio (Solo instalación del sistema)

\`\`\`bash
# Verificar servicio
sudo systemctl status ocr-pagos

# Iniciar servicio
sudo systemctl start ocr-pagos

# Habilitar inicio automático
sudo systemctl enable ocr-pagos

# Ver logs del servicio
journalctl -u ocr-pagos -f
\`\`\`

## 🧪 PASO 6: Pruebas Completas

### 6.1 Prueba con Imagen Real

\`\`\`bash
# Copiar tu imagen de comprobante
cp /ruta/a/tu/comprobante.png input/

# Procesar
python3 src/main_v2.py input/comprobante.png

# Ver resultados detallados
cat temp/comprobante_*/extraction_result_v2.json | jq .
\`\`\`

### 6.2 Prueba de Rendimiento

\`\`\`bash
# Procesar múltiples imágenes
for img in input/*.png; do
    echo "Procesando: $img"
    time python3 src/main_v2.py "$img"
done
\`\`\`

## 🔍 PASO 7: Solución de Problemas

### 7.1 Problemas Comunes

#### Error: "module 'config' has no attribute 'LOG_FILE'"

\`\`\`bash
# Verificar config.py
python3 -c "
import sys
sys.path.append('src')
import config
print('Atributos disponibles:', [attr for attr in dir(config) if not attr.startswith('_')])
"

# Si falla, reemplazar config.py
curl -sSL https://raw.githubusercontent.com/juancspjr/sistemacompletOcr/main/src/config.py -o src/config.py
\`\`\`

#### Error de Tesseract

\`\`\`bash
# Verificar Tesseract
which tesseract
tesseract --version
tesseract --list-langs

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

### 7.2 Logs de Diagnóstico

\`\`\`bash
# Activar debug completo
export OCR_DEBUG=1

# Ejecutar con logs detallados
python3 src/main_v2.py input/test.png 2>&1 | tee debug_completo.log

# Revisar logs del sistema
tail -f logs/system.log

# Para instalación del sistema
journalctl -u ocr-pagos -f
\`\`\`

## 📊 PASO 8: Monitoreo y Mantenimiento

### 8.1 Monitoreo de Logs

\`\`\`bash
# Logs de la aplicación
tail -f logs/system.log

# Logs del sistema (solo instalación del sistema)
journalctl -u ocr-pagos -f

# Estadísticas de uso
find temp/ -name "*.json" -mtime -1 | wc -l  # Procesados hoy
\`\`\`

### 8.2 Mantenimiento Regular

\`\`\`bash
# Limpiar archivos temporales antiguos (más de 7 días)
find temp/ -type d -mtime +7 -exec rm -rf {} +

# Rotar logs manualmente
sudo logrotate /etc/logrotate.d/ocr-pagos

# Actualizar sistema
git pull origin main  # Si tienes repositorio local
# O repetir instalación para actualizar
\`\`\`

## 🎯 COMANDOS DE USO DIARIO

### Uso Básico

\`\`\`bash
# Activar entorno (SIEMPRE necesario para instalación personal)
source venv/bin/activate

# Procesar una imagen
python3 src/main_v2.py input/mi_comprobante.png

# Ver resultados
ls temp/mi_comprobante_*/
cat temp/mi_comprobante_*/extraction_summary_v2.json

# Ver logs en tiempo real
tail -f logs/system.log
\`\`\`

### Uso Avanzado

\`\`\`bash
# Modo debug
OCR_DEBUG=1 python3 src/main_v2.py input/imagen_problema.png

# Procesar lote de imágenes
for img in input/*.png; do
    python3 src/main_v2.py "$img"
done

# Extraer solo resúmenes
find temp/ -name "extraction_summary_v2.json" -exec cat {} \; | jq .
\`\`\`

## 🆘 Soporte y Ayuda

### Información del Sistema

\`\`\`bash
# Versión del sistema
python3 src/main_v2.py --help

# Estado de dependencias
python3 -c "
import sys
sys.path.append('src')
import config
print(f'Versión OCR: {config.VERSION}')
print(f'Directorio base: {config.BASE_DIR}')
print(f'Tesseract: {config.TESSERACT_LANG}')
"
\`\`\`

### Contacto y Documentación

- **Repositorio**: https://github.com/juancspjr/sistemacompletOcr
- **Documentación**: Ver archivos README.md y USER_GUIDE.md
- **Issues**: Crear issue en GitHub para reportar problemas

---

## ✅ Checklist Final

- [ ] Sistema base actualizado
- [ ] Tesseract instalado con español
- [ ] OpenCV instalado
- [ ] Código descargado desde GitHub
- [ ] Entorno Python configurado
- [ ] Dependencias instaladas
- [ ] Prueba funcional exitosa
- [ ] Logs funcionando
- [ ] Configuración personalizada (opcional)
- [ ] Servicio configurado (solo instalación del sistema)

**¡Si todos los puntos están marcados, tu sistema OCR v2.0.0 está listo para usar!**
