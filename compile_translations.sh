#!/bin/bash
# Compila archivos de traducción (.ts → .qm) usando Docker
# Uso: ./compile_translations.sh

set -e

IMAGE_NAME="dictatux-dev-tools"

echo "Compilando traducciones..."

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

# Ejecutar lrelease con Docker
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    "$IMAGE_NAME" \
    lrelease dictatux/translations/*.ts

if [ $? -eq 0 ]; then
    echo "✓ Traducciones compiladas exitosamente"
    echo "Los archivos .qm han sido generados en dictatux/translations/"
else
    echo "✗ Error al compilar traducciones"
    exit 1
fi
