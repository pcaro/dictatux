#!/bin/bash
# Actualiza archivos de traducción (.ts) usando Docker
# Extrae cadenas traducibles del código Python
# Uso: ./update_translations.sh

set -e

IMAGE_NAME="dictatux-dev-tools"

echo "Actualizando archivos de traducción..."

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

# Ejecutar lupdate con Docker
# -no-obsolete: Elimina entradas obsoletas/vanished que ya no existen
# -extensions py: Procesa solo archivos Python
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    "$IMAGE_NAME" \
    lupdate -no-obsolete -extensions py dictatux/ -ts dictatux/translations/*.ts

if [ $? -eq 0 ]; then
    echo "✓ Archivos de traducción actualizados"
    echo "Edita los archivos .ts en dictatux/translations/ y luego ejecuta ./compile_translations.sh"
else
    echo "✗ Error al actualizar traducciones"
    exit 1
fi
