#!/bin/bash
# Compila archivos de traducción (.ts → .qm) usando Docker
# Uso: ./compile_translations.sh

echo "Compilando traducciones..."

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instálalo con: sudo apt install docker.io"
    exit 1
fi

# Ejecutar lrelease con Docker
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    ubuntu:22.04 bash -c "
        apt-get update -qq && \
        apt-get install -y -qq qt6-tools-dev-tools > /dev/null 2>&1 && \
        lrelease dictatux/translations/*.ts
    "

if [ $? -eq 0 ]; then
    echo "✓ Traducciones compiladas exitosamente"
    echo "Los archivos .qm han sido generados en dictatux/translations/"
else
    echo "✗ Error al compilar traducciones"
    exit 1
fi
