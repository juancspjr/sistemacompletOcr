# Guía de Instalación - Sistema OCR de Pagos Móviles

## Requisitos Previos del Sistema

### Sistema Operativo
- **Ubuntu Server LTS 22.04** (recomendado)
- **Ubuntu Server LTS 20.04** (compatible)
- Mínimo 4GB RAM, 2 CPU cores, 10GB espacio libre

### Verificación del Sistema
\`\`\`bash
# Verificar versión de Ubuntu
lsb_release -a

# Verificar recursos disponibles
free -h
df -h
nproc
\`\`\`

## Paso 1: Actualización del Sistema

\`\`\`bash
# Actualizar repositorios y paquetes
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y curl wget git build-essential software-properties-common
\`\`\`

## Paso 2: Instalación de Python 3.10+

\`\`\`bash
# Verificar versión actual de Python
python3 --version

# Si es menor a 3.9, instalar Python 3.10
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# Crear enlace simbólico (si es necesario)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
\`\`\`

## Paso 3: Instalación de Tesseract OCR

\`\`\`bash
# Instalar Tesseract y paquetes de idioma
sudo apt install -y tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng

# Verificar instalación
tesseract --version
tesseract --list-langs

# Debería mostrar: spa, eng, osd
\`\`\`

### Configuración Adicional de Tesseract
\`\`\`bash
# Verificar ubicación de datos de Tesseract
sudo find /usr -name "tessdata" -type d

# Instalar paquetes adicionales si es necesario
sudo apt install -y tesseract-ocr-script-latn
\`\`\`

## Paso 4: Instalación de Dependencias del Sistema

\`\`\`bash
# Librerías para OpenCV y procesamiento de imágenes
sudo apt install -y \
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

# Librerías adicionales para Pillow
sudo apt install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    zlib1g-dev
\`\`\`

## Paso 5: Clonación del Proyecto

\`\`\`bash
# Crear directorio base
sudo mkdir -p /opt/ocr-pagos
sudo chown $USER:$USER /opt/ocr-pagos
cd /opt/ocr-pagos

# Clonar repositorio (ajustar URL según tu repositorio)
git clone https://github.com/tu-usuario/sistema-ocr-pagos.git .

# Verificar estructura
ls -la
\`\`\`

## Paso 6: Configuración del Entorno Virtual

\`\`\`bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel
\`\`\`

## Paso 7: Instalación de Dependencias Python

\`\`\`bash
# Instalar dependencias desde requirements.txt
pip install -r requirements.txt

# Verificar instalaciones críticas
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import pytesseract; print('PyTesseract instalado correctamente')"
python -c "import PIL; print('Pillow:', PIL.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
\`\`\`

### Solución de Problemas Comunes en Instalación

#### Error de OpenCV
\`\`\`bash
# Si falla la instalación de opencv-python
pip uninstall opencv-python opencv-python-headless
pip install opencv-python-headless==4.8.1.78
\`\`\`

#### Error de PyTesseract
\`\`\`bash
# Verificar que Tesseract esté en PATH
which tesseract
echo $PATH

# Si no está en PATH, añadir a ~/.bashrc
echo 'export PATH="/usr/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
\`\`\`

## Paso 8: Configuración de Permisos y Directorios

\`\`\`bash
# Crear directorios necesarios
mkdir -p input temp logs data/processed_receipts data/feedback_loop templates

# Establecer permisos
chmod 755 src/*.py
chmod +x src/main.py src/update_probabilistic_model.py

# Crear usuario de servicio (opcional, para producción)
sudo useradd -r -s /bin/false ocr-service
sudo chown -R ocr-service:ocr-service /opt/ocr-pagos
\`\`\`

## Paso 9: Configuración Inicial

\`\`\`bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar configuración inicial
python3 src/config.py

# Verificar que se crearon los directorios
ls -la data/
ls -la templates/
\`\`\`

## Paso 10: Prueba de Instalación

\`\`\`bash
# Crear imagen de prueba simple
echo "Creando imagen de prueba..."

# Ejecutar prueba básica (requiere imagen de prueba)
python3 src/main.py input/test_image.jpg test_001

# Verificar logs
tail -f logs/system.log
\`\`\`

### Script de Prueba Completa
\`\`\`bash
# Crear script de verificación
cat > test_installation.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

try:
    import config
    import cv2
    import pytesseract
    import pandas as pd
    import yaml
    from PIL import Image
    
    print("✓ Todas las dependencias importadas correctamente")
    
    # Verificar Tesseract
    version = pytesseract.get_tesseract_version()
    print(f"✓ Tesseract versión: {version}")
    
    # Verificar directorios
    dirs_to_check = ['input', 'temp', 'logs', 'data', 'templates']
    for dir_name in dirs_to_check:
        if os.path.exists(dir_name):
            print(f"✓ Directorio {dir_name} existe")
        else:
            print(f"✗ Directorio {dir_name} NO existe")
    
    print("\n🎉 Instalación verificada correctamente!")
    
except Exception as e:
    print(f"✗ Error en la verificación: {e}")
    sys.exit(1)
EOF

python3 test_installation.py
\`\`\`

## Paso 11: Configuración de Servicio Systemd (Opcional)

\`\`\`bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/ocr-pagos.service << EOF
[Unit]
Description=Sistema OCR de Pagos Móviles
After=network.target

[Service]
Type=simple
User=ocr-service
Group=ocr-service
WorkingDirectory=/opt/ocr-pagos
Environment=PATH=/opt/ocr-pagos/venv/bin
ExecStart=/opt/ocr-pagos/venv/bin/python3 src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar servicio
sudo systemctl daemon-reload
sudo systemctl enable ocr-pagos.service
\`\`\`

## Paso 12: Configuración de Logs y Rotación

\`\`\`bash
# Configurar logrotate
sudo tee /etc/logrotate.d/ocr-pagos << EOF
/opt/ocr-pagos/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ocr-service ocr-service
    postrotate
        systemctl reload ocr-pagos || true
    endscript
}
EOF
\`\`\`

## Verificación Final

### Lista de Verificación Post-Instalación
- [ ] Python 3.10+ instalado y funcionando
- [ ] Tesseract OCR instalado con idiomas spa/eng
- [ ] Todas las dependencias Python instaladas
- [ ] Directorios del proyecto creados
- [ ] Permisos configurados correctamente
- [ ] Prueba básica ejecutada exitosamente
- [ ] Logs generándose correctamente

### Comandos de Verificación Rápida
\`\`\`bash
# Verificar instalación completa
cd /opt/ocr-pagos
source venv/bin/activate
python3 test_installation.py

# Verificar servicios
systemctl status ocr-pagos
journalctl -u ocr-pagos -f
\`\`\`

## Solución de Problemas de Instalación

### Error: "No module named 'cv2'"
\`\`\`bash
pip uninstall opencv-python
pip install opencv-python-headless==4.8.1.78
\`\`\`

### Error: "TesseractNotFoundError"
\`\`\`bash
# Verificar instalación
which tesseract
sudo apt reinstall tesseract-ocr

# Verificar variable de entorno
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/
\`\`\`

### Error de Permisos
\`\`\`bash
# Corregir permisos
sudo chown -R $USER:$USER /opt/ocr-pagos
chmod -R 755 /opt/ocr-pagos
\`\`\`

### Problemas de Memoria
\`\`\`bash
# Verificar memoria disponible
free -h

# Si es insuficiente, crear swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
\`\`\`

## Configuración para Producción

### Variables de Entorno
\`\`\`bash
# Crear archivo de entorno
cat > .env << EOF
PYTHONPATH=/opt/ocr-pagos/src
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/
LOG_LEVEL=INFO
CLEAN_TEMP_FILES=true
EOF

# Cargar en el perfil
echo "source /opt/ocr-pagos/.env" >> ~/.bashrc
\`\`\`

### Monitoreo Básico
\`\`\`bash
# Instalar herramientas de monitoreo
sudo apt install -y htop iotop nethogs

# Script de monitoreo simple
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== Estado del Sistema OCR ==="
echo "Memoria:"
free -h
echo -e "\nProcesos Python:"
ps aux | grep python3 | grep -v grep
echo -e "\nEspacio en disco:"
df -h /opt/ocr-pagos
echo -e "\nÚltimos logs:"
tail -5 /opt/ocr-pagos/logs/system.log
EOF

chmod +x monitor.sh
\`\`\`

## Próximos Pasos

1. **Configurar N8N**: Integrar con el sistema de automatización
2. **Añadir Plantillas**: Crear plantillas específicas para tus recibos
3. **Configurar Feedback**: Establecer proceso de corrección manual
4. **Monitoreo**: Implementar alertas y métricas
5. **Backup**: Configurar respaldo de datos y modelos

---

**¿Instalación completada?** Continúa con la [Guía de Usuario](USER_GUIDE.md) para aprender a usar el sistema.
