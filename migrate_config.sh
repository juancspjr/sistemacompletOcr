#!/bin/bash

# Script de Migración de Configuración
# Compara y migra configuraciones entre versiones

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OLD_CONFIG="$1"
NEW_CONFIG="$2"

if [ ! -f "$OLD_CONFIG" ] || [ ! -f "$NEW_CONFIG" ]; then
    echo -e "${RED}Error: Archivos de configuración no encontrados${NC}"
    echo "Uso: bash migrate_config.sh <config_anterior> <config_nueva>"
    echo
    echo "Ejemplo:"
    echo "  bash migrate_config.sh /backup/config.py src/config.py"
    exit 1
fi

echo -e "${BLUE}=== MIGRACIÓN DE CONFIGURACIÓN ===${NC}"
echo
echo "📁 Configuración anterior: $OLD_CONFIG"
echo "📁 Configuración nueva: $NEW_CONFIG"
echo

# Crear backup de la configuración actual
BACKUP_CONFIG="${NEW_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$NEW_CONFIG" "$BACKUP_CONFIG"
echo -e "${GREEN}✓${NC} Backup creado: $BACKUP_CONFIG"

# Analizar diferencias
echo
echo -e "${YELLOW}📋 DIFERENCIAS DETECTADAS:${NC}"
echo "----------------------------------------"

if diff -u "$OLD_CONFIG" "$NEW_CONFIG" > /tmp/config_diff.txt; then
    echo -e "${GREEN}✓ No hay diferencias en la configuración${NC}"
    rm -f /tmp/config_diff.txt
    exit 0
else
    # Mostrar diferencias de manera legible
    cat /tmp/config_diff.txt | head -50
    
    if [ $(wc -l &lt; /tmp/config_diff.txt) -gt 50 ]; then
        echo "... (diferencias truncadas, ver archivo completo en /tmp/config_diff.txt)"
    fi
fi

echo
echo "----------------------------------------"

# Extraer variables importantes de la configuración anterior
echo -e "${BLUE}🔍 ANALIZANDO CONFIGURACIÓN ANTERIOR:${NC}"

# Buscar configuraciones personalizadas importantes
CUSTOM_SETTINGS=$(grep -E "^[A-Z_]+ = " "$OLD_CONFIG" | grep -v "^#" || true)

if [ -n "$CUSTOM_SETTINGS" ]; then
    echo "Configuraciones personalizadas encontradas:"
    echo "$CUSTOM_SETTINGS" | while read line; do
        echo "  • $line"
    done
else
    echo "No se encontraron configuraciones personalizadas"
fi

echo

# Opciones de migración
echo -e "${YELLOW}🔧 OPCIONES DE MIGRACIÓN:${NC}"
echo "1) Mantener configuración actual (nueva)"
echo "2) Restaurar configuración anterior completa"
echo "3) Migración interactiva (recomendado)"
echo "4) Mostrar diferencias detalladas"
echo "5) Cancelar"
echo

read -p "Selecciona una opción (1-5): " -n 1 -r
echo

case $REPLY in
    1)
        echo -e "${GREEN}✓ Manteniendo configuración nueva${NC}"
        echo "La configuración anterior está disponible en: $BACKUP_CONFIG"
        ;;
    2)
        echo -e "${YELLOW}⚠ Restaurando configuración anterior completa${NC}"
        cp "$OLD_CONFIG" "$NEW_CONFIG"
        echo -e "${GREEN}✓ Configuración anterior restaurada${NC}"
        echo "ADVERTENCIA: Puede que falten nuevas configuraciones requeridas"
        ;;
    3)
        echo -e "${BLUE}🔄 Iniciando migración interactiva...${NC}"
        
        # Migración interactiva variable por variable
        python3 &lt;&lt; 'EOF'
import re
import sys

def extract_variables(file_path):
    """Extrae variables de configuración de un archivo Python"""
    variables = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar asignaciones de variables
        pattern = r'^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$'
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                match = re.match(pattern, line)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2)
                    variables[var_name] = var_value
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
    
    return variables

def interactive_migration(old_file, new_file):
    """Migración interactiva de configuración"""
    old_vars = extract_variables(old_file)
    new_vars = extract_variables(new_file)
    
    print("\n🔄 MIGRACIÓN INTERACTIVA DE VARIABLES:")
    print("=" * 50)
    
    # Variables que han cambiado
    changed_vars = {}
    for var_name in old_vars:
        if var_name in new_vars and old_vars[var_name] != new_vars[var_name]:
            changed_vars[var_name] = {
                'old': old_vars[var_name],
                'new': new_vars[var_name]
            }
    
    # Variables nuevas
    new_only_vars = {k: v for k, v in new_vars.items() if k not in old_vars}
    
    # Variables eliminadas
    removed_vars = {k: v for k, v in old_vars.items() if k not in new_vars}
    
    if changed_vars:
        print(f"\n📝 Variables modificadas ({len(changed_vars)}):")
        for var_name, values in changed_vars.items():
            print(f"\n  Variable: {var_name}")
            print(f"    Anterior: {values['old']}")
            print(f"    Nueva:    {values['new']}")
            
            choice = input("    ¿Mantener valor anterior? (y/N): ").strip().lower()
            if choice in ['y', 'yes', 's', 'si']:
                new_vars[var_name] = old_vars[var_name]
                print("    ✓ Valor anterior mantenido")
            else:
                print("    ✓ Valor nuevo mantenido")
    
    if new_only_vars:
        print(f"\n🆕 Variables nuevas ({len(new_only_vars)}):")
        for var_name, value in new_only_vars.items():
            print(f"  • {var_name} = {value}")
        print("  (Estas variables se mantendrán con sus valores por defecto)")
    
    if removed_vars:
        print(f"\n🗑️ Variables eliminadas ({len(removed_vars)}):")
        for var_name, value in removed_vars.items():
            print(f"  • {var_name} = {value}")
        print("  (Estas variables ya no son necesarias)")
    
    # Escribir nueva configuración
    try:
        with open(new_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar variables modificadas
        for var_name, value in new_vars.items():
            if var_name in changed_vars and new_vars[var_name] == old_vars[var_name]:
                # Reemplazar con valor anterior
                pattern = rf'^({var_name}\s*=\s*)(.+)$'
                content = re.sub(pattern, rf'\1{value}', content, flags=re.MULTILINE)
        
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ Configuración migrada exitosamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante migración: {e}")
        return False

# Ejecutar migración interactiva
if interactive_migration(sys.argv[1], sys.argv[2]):
    print("🎉 Migración completada")
else:
    print("💥 Migración falló")
    sys.exit(1)
EOF
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Migración interactiva completada${NC}"
        else
            echo -e "${RED}✗ Error en migración interactiva${NC}"
            echo "Restaurando backup..."
            cp "$BACKUP_CONFIG" "$NEW_CONFIG"
        fi
        ;;
    4)
        echo -e "${BLUE}📋 DIFERENCIAS DETALLADAS:${NC}"
        echo "========================================"
        cat /tmp/config_diff.txt
        echo "========================================"
        echo
        echo "Archivo de diferencias guardado en: /tmp/config_diff.txt"
        ;;
    5)
        echo -e "${YELLOW}❌ Migración cancelada${NC}"
        echo "Configuración no modificada"
        exit 0
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

# Limpiar archivos temporales
rm -f /tmp/config_diff.txt

echo
echo -e "${GREEN}🎯 MIGRACIÓN COMPLETADA${NC}"
echo "📁 Configuración actual: $NEW_CONFIG"
echo "💾 Backup disponible: $BACKUP_CONFIG"
echo
echo "🔍 PRÓXIMOS PASOS:"
echo "1. Verificar que la configuración es correcta"
echo "2. Probar el sistema con una imagen de prueba"
echo "3. Revisar logs para detectar posibles problemas"
