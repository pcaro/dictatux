#!/bin/bash
# Actualiza archivos de traducción (.ts) usando PySide6 (entorno virtual)
# Extrae cadenas traducibles del código Python
# Uso: ./update_translations.sh

set -e

echo "Actualizando archivos de traducción..."

# Usar pyside6-lupdate del entorno virtual con uv
# -no-obsolete: Elimina entradas obsoletas/vanished que ya no existen
# -extensions py: Procesa solo archivos Python
uv run pyside6-lupdate -no-obsolete -extensions py dictatux/ -ts dictatux/translations/*.ts

if [ $? -eq 0 ]; then
    echo "✓ Archivos de traducción actualizados"
    echo "Edita los archivos .ts en dictatux/translations/ y luego ejecuta ./compile_translations.sh"
else
    echo "✗ Error al actualizar traducciones"
    exit 1
fi
