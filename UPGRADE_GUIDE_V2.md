# Guía de Actualización a OCR v2.0 Optimizado

## 🚀 Resumen de Cambios

La versión 2.0 del sistema OCR implementa una **estrategia de extracción flexible** basada en los excelentes resultados del análisis de `direct_ocr_extractor_polished.py`. Los cambios principales incluyen:

### ✅ Mejoras Implementadas

1. **Eliminación del Aislamiento de Documento**
   - Desactivado permanentemente en `image_processor_optimized.py`
   - La imagen preprocesada completa se usa para OCR
   - Elimina recortes erróneos que causaban extracciones fallidas

2. **Estrategia de Extracción de Dos Fases**
   - **Fase A**: Extracción anclada por palabras clave
   - **Fase B**: Extracción generalizada sin ancla
   - Búsqueda inteligente en datos del OCR global

3. **Extracción Directa desde OCR Global**
   - Sin reprocesamientos ni recortes individuales
   - Utiliza directamente las bbox y confianza de Tesseract
   - Elimina operaciones de guardado de recortes (`*_recorte.png`)

4. **Validación Flexible y Robusta**
   - Soporte para campos multipalabra (ej. "0108 - BBVA PROVINCIAL")
   - Heurísticas contextuales mejoradas
   - Validación cruzada entre campos

## 📁 Archivos Nuevos y Modificados

### Archivos Principales v2.0
- `src/main_v2.py` - Orquestador principal optimizado
- `src/image_processor_optimized.py` - Sin aislamiento de documento
- `src/template_manager_v2.py` - Estrategia de extracción flexible
- `src/data_extractor_v2.py` - Extracción directa desde OCR global

### Scripts de Prueba
- `scripts/test_v2_system.sh` - Validación del sistema v2.0

### Documentación
- `UPGRADE_GUIDE_V2.md` - Esta guía
- `CHANGELOG.md` - Registro de cambios detallado

## 🔧 Instalación y Migración

### 1. Backup del Sistema Actual
\`\`\`bash
# Crear backup de la versión actual
cp -r src/ src_backup_v1/
cp -r templates/ templates_backup_v1/
\`\`\`

### 2. Implementar Archivos v2.0
\`\`\`bash
# Los nuevos archivos v2.0 coexisten con los v1.0
# No se requiere reemplazar archivos existentes
\`\`\`

### 3. Probar el Sistema v2.0
\`\`\`bash
# Ejecutar pruebas con el nuevo sistema
chmod +x scripts/test_v2_system.sh
./scripts/test_v2_system.sh
\`\`\`

### 4. Comparar Resultados
\`\`\`bash
# Procesar la misma imagen con ambas versiones
python3 src/main.py input/test2.png          # v1.0
python3 src/main_v2.py input/test2.png       # v2.0

# Comparar resultados en temp/
\`\`\`

## 📊 Mejoras de Rendimiento Esperadas

Basado en el análisis de `ocr_details_debug.json`:

| Campo | v1.0 (Anterior) | v2.0 (Optimizado) | Mejora |
|-------|-----------------|-------------------|---------|
| Monto | "o", "NN" | "209,08" (96%) | ✅ 100% |
| Fecha | Fallas | "20/06/2025" (96%) | ✅ 100% |
| Operación | Fallas | "003039392904" (95%) | ✅ 100% |
| Identificación | Fallas | "27061025" (96%) | ✅ 100% |
| Banco | Fallas | "0108 - BBVA PROVINCIAL" | ✅ 100% |

## 🎯 Campos Soportados v2.0

### Campos con Palabra Clave Ancla (Fase A)
- `monto` - Busca cerca de "Bs", "Monto", "Total"
- `fecha` - Busca cerca de "Fecha:", "Fecha"
- `operacion` - Busca cerca de "Operación:", "Ref"
- `identificacion` - Busca cerca de "Identificación:", "C.I."
- `origen_numero` - Busca cerca de "Origen:"
- `destino_numero` - Busca cerca de "Destino:"
- `banco_completo` - Busca cerca de "Banco:" (multipalabra)
- `concepto` - Busca cerca de "Concepto:" (multipalabra)

### Campos de Extracción Generalizada (Fase B)
- `nombre_o_info_completa` - Busca patrones de nombres sin ancla

## 🔍 Validación y Debugging

### Archivos de Debug Generados
- `extraction_result_v2.json` - Resultado completo
- `extraction_summary_v2.json` - Resumen ejecutivo
- `debug_overlay_v2.png` - Visualización de campos extraídos

### Logs Detallados
\`\`\`bash
# Ver logs en tiempo real
tail -f logs/ocr_system.log

# Filtrar logs v2.0
grep "v2.0" logs/ocr_system.log
\`\`\`

## ⚡ Uso del Sistema v2.0

### Comando Básico
\`\`\`bash
python3 src/main_v2.py input/imagen.png
\`\`\`

### Códigos de Salida
- `0` - Éxito completo
- `2` - Advertencia (baja confianza/validación fallida)
- `1` - Error en procesamiento

### Ejemplo de Salida
\`\`\`
RESUMEN DE PROCESAMIENTO OCR v2.0
============================================================
Estado: success
Método de extracción: flexible_zoi_v2
Campos extraídos: 8
Confianza general: 94.2%
Tiempo de procesamiento: 3.45s

CAMPOS EXTRAÍDOS:
----------------------------------------
monto          : 209,08              (96.0%)
fecha          : 20/06/2025          (96.0%)
operacion      : 003039392904        (95.0%)
identificacion : 27061025            (96.0%)
origen_numero  : 0102****3799        (85.0%)
destino_numero : 04125318244         (96.0%)
banco_completo : 0108 - BBVA PROVINCIAL (94.0%)
concepto       : pago Luzmar         (92.0%)
============================================================
\`\`\`

## 🔄 Rollback (Si es Necesario)

Si necesita volver a la versión anterior:

\`\`\`bash
# El sistema v1.0 permanece intacto
python3 src/main.py input/imagen.png

# O restaurar desde backup
rm -rf src/
mv src_backup_v1/ src/
\`\`\`

## 📈 Próximos Pasos

1. **Validar** el sistema v2.0 con sus imágenes de prueba
2. **Comparar** resultados con la versión anterior
3. **Reportar** cualquier problema o mejora necesaria
4. **Migrar** gradualmente a v2.0 una vez validado

## 🆘 Soporte

Si encuentra problemas:

1. Revisar logs en `logs/ocr_system.log`
2. Verificar archivos de debug en `temp/`
3. Ejecutar `scripts/test_v2_system.sh` para diagnóstico
4. Reportar issues con archivos de debug adjuntos

---

**¡El sistema v2.0 está listo para maximizar la precisión de extracción basándose en los excelentes resultados del OCR global!** 🎉
