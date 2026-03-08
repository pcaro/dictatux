#!/bin/bash
# Compila recursos Qt usando Docker (sin instalar nada en el sistema)
# Uso: ./compile_resources.sh [archivo.qrc] [salida.py]

QRC_FILE="${1:-dictatux/dictatux.qrc}"
OUTPUT_FILE="${2:-dictatux/dictatux_rc.py}"

echo "Compilando $QRC_FILE -> $OUTPUT_FILE usando Docker..."

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instálalo con: sudo apt install docker.io"
    exit 1
fi

# Ejecutar con Docker
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    ubuntu:22.04 bash -c "
        apt-get update -qq && \
        apt-get install -y -qq python3-pyqt6-dev-tools > /dev/null 2>&1 && \
        pyrcc6 '$QRC_FILE' -o '$OUTPUT_FILE'
    "

if [ $? -eq 0 ]; then
    echo "✓ Archivo compilado exitosamente: $OUTPUT_FILE"
else
    echo "✗ Error al compilar"
    exit 1
fi
