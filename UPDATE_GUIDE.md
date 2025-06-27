# Guía de Actualización del Sistema OCR de Pagos Móviles

## Gestión de Versiones en GitHub

### Estructura de Ramas Recomendada

\`\`\`
main (producción estable)
├── develop (desarrollo activo)
├── feature/mejoras-preprocesamiento
├── hotfix/correccion-critica
└── release/v1.1.0
\`\`\`

### Configuración Inicial del Repositorio

#### 1. Crear Repositorio en GitHub
\`\`\`bash
# En tu máquina local o servidor
cd /opt/ocr-pagos

# Inicializar git si no existe
git init

# Configurar usuario
git config user.name "Tu Nombre"
git config user.email "tu-email@dominio.com"

# Añadir archivos al repositorio
git add .
git commit -m "Initial commit - Sistema OCR v1.0.0"

# Conectar con GitHub (reemplaza con tu URL)
git remote add origin https://github.com/tu-usuario/sistema-ocr-pagos.git

# Subir código inicial
git branch -M main
git push -u origin main
\`\`\`

#### 2. Crear Rama de Desarrollo
\`\`\`bash
# Crear y cambiar a rama develop
git checkout -b develop
git push -u origin develop

# Establecer develop como rama por defecto para desarrollo
git checkout develop
\`\`\`

### Sistema de Versionado Semántico

#### Formato de Versiones: `MAJOR.MINOR.PATCH`
- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nuevas funcionalidades compatibles
- **PATCH**: Correcciones de errores

#### Ejemplos:
- `v1.0.0` - Versión inicial
- `v1.1.0` - Mejoras de preprocesamiento (nueva funcionalidad)
- `v1.1.1` - Corrección de bugs
- `v2.0.0` - Cambios arquitectónicos importantes

### Gestión de Releases en GitHub

#### 1. Crear Release desde Línea de Comandos
\`\`\`bash
# Crear tag para nueva versión
git tag -a v1.1.0 -m "Versión 1.1.0 - Mejoras de preprocesamiento optimizado"

# Subir tag a GitHub
git push origin v1.1.0

# Crear release usando GitHub CLI (opcional)
gh release create v1.1.0 --title "v1.1.0 - Preprocesamiento Optimizado" --notes-file CHANGELOG.md
\`\`\`

#### 2. Crear Release desde GitHub Web
1. Ve a tu repositorio en GitHub
2. Click en "Releases" → "Create a new release"
3. Selecciona el tag (ej: v1.1.0)
4. Añade título y descripción
5. Adjunta archivos si es necesario
6. Marca como "Latest release"

## Procedimientos de Actualización en el Servidor

### Método 1: Actualización Automática (Recomendado)

#### Script de Actualización Automática
