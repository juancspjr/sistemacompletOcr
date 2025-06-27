FROM ubuntu:22.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-spa \
    tesseract-ocr-eng \
    libopencv-dev \
    python3-opencv \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /opt/ocr-pagos

# Copiar archivos del proyecto
COPY . .

# Crear entorno virtual e instalar dependencias
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p input temp logs data templates

# Configurar permisos
RUN chmod +x src/main.py src/update_probabilistic_model.py

# Exponer puerto si es necesario
EXPOSE 8000

# Comando por defecto
CMD ["venv/bin/python3", "src/main.py"]
