#!/bin/bash

# Script de prueba para el sistema OCR v2.0 optimizado
# Valida la nueva estrategia de extracción flexible

echo "=========================================="
echo "PRUEBA DEL SISTEMA OCR v2.0 OPTIMIZADO"
echo "=========================================="

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INPUT_DIR="$PROJECT_ROOT/input"
OUTPUT_DIR="$PROJECT_ROOT/output"
TEMP_DIR="$PROJECT_ROOT/temp"

# Crear directorios si no existen
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR" "$TEMP_DIR"

echo "Directorio del proyecto: $PROJECT_ROOT"
echo "Directorio de entrada: $INPUT_DIR"
echo "Directorio de salida: $OUTPUT_DIR"

# Verificar que existe el archivo principal v2.0
MAIN_V2="$PROJECT_ROOT/src/main_v2.py"
if [ ! -f "$MAIN_V2" ]; then
    echo "ERROR: No se encuentra main_v2.py en $MAIN_V2"
    exit 1
fi

echo "✓ Sistema v2.0 encontrado: $MAIN_V2"

# Buscar imágenes de prueba
TEST_IMAGES=()
for ext in png jpg jpeg; do
    while IFS= read -r -d '' file; do
        TEST_IMAGES+=("$file")
    done < <(find "$INPUT_DIR" -name "*.$ext" -print0 2>/dev/null)
done

if [ ${#TEST_IMAGES[@]} -eq 0 ]; then
    echo "ADVERTENCIA: No se encontraron imágenes de prueba en $INPUT_DIR"
    echo "Coloque archivos .png, .jpg o .jpeg en el directorio input/"
    exit 1
fi

echo "✓ Encontradas ${#TEST_IMAGES[@]} imágenes de prueba"

# Función para procesar una imagen
process_image() {
    local image_path="$1"
    local image_name=$(basename "$image_path")
    
    echo ""
    echo "----------------------------------------"
    echo "Procesando: $image_name"
    echo "----------------------------------------"
    
    # Ejecutar el sistema v2.0
    cd "$PROJECT_ROOT"
    python3 "$MAIN_V2" "$image_path"
    local exit_code=$?
    
    case $exit_code in
        0)
            echo "✓ ÉXITO: Procesamiento completado exitosamente"
            return 0
            ;;
        2)
            echo "⚠ ADVERTENCIA: Procesamiento con baja confianza o validación fallida"
            return 2
            ;;
        *)
            echo "✗ ERROR: Procesamiento falló (código: $exit_code)"
            return 1
            ;;
    esac
}

# Procesar todas las imágenes
echo ""
echo "Iniciando procesamiento de imágenes..."

total_images=${#TEST_IMAGES[@]}
successful=0
warnings=0
errors=0

for image_path in "${TEST_IMAGES[@]}"; do
    process_image "$image_path"
    case $? in
        0) ((successful++)) ;;
        2) ((warnings++)) ;;
        *) ((errors++)) ;;
    esac
done

# Resumen final
echo ""
echo "=========================================="
echo "RESUMEN DE PRUEBAS v2.0"
echo "=========================================="
echo "Total de imágenes procesadas: $total_images"
echo "Exitosas: $successful"
echo "Con advertencias: $warnings"
echo "Con errores: $errors"

# Mostrar archivos de salida generados
echo ""
echo "Archivos generados en temp/:"
find "$TEMP_DIR" -name "*.json" -o -name "*.png" | head -10

if [ $errors -eq 0 ]; then
    if [ $warnings -eq 0 ]; then
        echo ""
        echo "🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE"
        exit 0
    else
        echo ""
        echo "⚠ PRUEBAS COMPLETADAS CON ADVERTENCIAS"
        exit 2
    fi
else
    echo ""
    echo "❌ ALGUNAS PRUEBAS FALLARON"
    exit 1
fi
