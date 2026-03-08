#!/bin/bash
# Compila recursos Qt usando PySide6 (entorno virtual)
# Uso: ./compile_resources.sh [archivo.qrc] [salida.py]

set -e

QRC_FILE="${1:-dictatux/dictatux.qrc}"
OUTPUT_FILE="${2:-dictatux/dictatux_rc.py}"

echo "Compilando $QRC_FILE -> $OUTPUT_FILE..."

# Usar pyside6-rcc del entorno virtual con uv
uv run pyside6-rcc "$QRC_FILE" -o "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Archivo compilado exitosamente: $OUTPUT_FILE"
else
    echo "✗ Error al compilar"
    exit 1
fi
