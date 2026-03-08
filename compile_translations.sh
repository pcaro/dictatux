#!/bin/bash
# Compila archivos de traducción (.ts → .qm) usando PySide6 (entorno virtual)
# Uso: ./compile_translations.sh

set -e

echo "Compilando traducciones..."

# Usar pyside6-lrelease del entorno virtual con uv
uv run pyside6-lrelease dictatux/translations/*.ts

if [ $? -eq 0 ]; then
    echo "✓ Traducciones compiladas exitosamente"
    echo "Los archivos .qm han sido generados en dictatux/translations/"
else
    echo "✗ Error al compilar traducciones"
    exit 1
fi
