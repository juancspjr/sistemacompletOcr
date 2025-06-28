#!/bin/bash

# Script para preparar release v2.0.0 en GitHub
# Crea tag, actualiza changelog y prepara archivos

set -e

# Configuración
VERSION="v2.0.0"
BRANCH="main"
CHANGELOG_FILE="CHANGELOG.md"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Preparando release $VERSION para GitHub...${NC}"

# Verificar que estamos en la rama correcta
current_branch=$(git branch --show-current)
if [ "$current_branch" != "$BRANCH" ]; then
    echo -e "${YELLOW}Cambiando a rama $BRANCH...${NC}"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
fi

# Verificar que no hay cambios sin commit
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: Hay cambios sin commit. Commit primero."
    exit 1
fi

# Actualizar CHANGELOG.md
echo -e "${BLUE}Actualizando CHANGELOG.md...${NC}"

cat > "$CHANGELOG_FILE" << 'EOF'
# Changelog - Sistema OCR Pagos Móviles

## [v2.0.0] - 2024-12-27

### 🚀 CAMBIOS PRINCIPALES - ESTRATEGIA OPTIMIZADA

#### ✅ Nuevas Características
- **Estrategia de Extracción Flexible v2.0**: Implementación de dos fases (anclada + generalizada)
- **Eliminación del Aislamiento de Documento**: Procesamiento sobre imagen completa preprocesada
- **Extracción Directa desde OCR Global**: Sin reprocesamientos ni recortes individuales
- **Soporte Multipalabra**: Campos como "0108 - BBVA PROVINCIAL" extraídos correctamente
- **Validación Contextual Mejorada**: Heurísticas inteligentes basadas en proximidad

#### 🔧 Archivos Nuevos
- `src/main_v2.py` - Orquestador principal optimizado
- `src/image_processor_optimized.py` - Preprocesamiento sin aislamiento
- `src/template_manager_v2.py` - Estrategia de extracción flexible
- `src/data_extractor_v2.py` - Extracción directa desde OCR global
- `scripts/deploy_v2.sh` - Script de actualización desde GitHub
- `scripts/test_v2_system.sh` - Validación del sistema v2.0

#### 📊 Mejoras de Rendimiento
- **Monto**: De extracciones fallidas ("o", "NN") a "209,08" (96% confianza)
- **Fecha**: De fallas a "20/06/2025" (96% confianza)
- **Operación**: De fallas a "003039392904" (95% confianza)
- **Identificación**: De fallas a "27061025" (96% confianza)
- **Banco**: Soporte completo para "0108 - BBVA PROVINCIAL"

#### 🔄 Compatibilidad
- Sistema v1.0 permanece intacto para rollback
- Migración automática de configuración y datos
- Scripts de rollback incluidos

#### 🛠️ Mejoras Técnicas
- Eliminación de operaciones de guardado de recortes individuales
- Búsqueda inteligente basada en bbox reales de Tesseract
- Validación cruzada entre campos extraídos
- Debug overlay v2.0 con visualización mejorada

### 📋 Instrucciones de Actualización

\`\`\`bash
# Desde el servidor
cd /opt/ocr-pagos
wget https://raw.githubusercontent.com/tu-usuario/sistema-ocr-pagos/v2.0.0/scripts/deploy_v2.sh
chmod +x deploy_v2.sh
./deploy_v2.sh
