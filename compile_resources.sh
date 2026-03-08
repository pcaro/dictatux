#!/bin/bash
# Compila recursos Qt usando Docker (sin instalar nada en el sistema)
# Uso: ./compile_resources.sh [archivo.qrc] [salida.py]

set -e

IMAGE_NAME="dictatux-dev-tools"

QRC_FILE="${1:-dictatux/dictatux.qrc}"
OUTPUT_FILE="${2:-dictatux/dictatux_rc.py}"

echo "Compilando $QRC_FILE -> $OUTPUT_FILE usando Docker..."

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instálalo con: sudo apt install docker.io"
    exit 1
fi

# Verificar si la imagen existe, si no, construirla
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Imagen '$IMAGE_NAME' no encontrada. Construyendo..."
    docker build -t "$IMAGE_NAME" -f Dockerfile.dev-tools .
    echo "✓ Imagen construida exitosamente"
fi

# Ejecutar con Docker
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    "$IMAGE_NAME" \
    pyrcc6 "$QRC_FILE" -o "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✓ Archivo compilado exitosamente: $OUTPUT_FILE"
else
    echo "✗ Error al compilar"
    exit 1
fi
