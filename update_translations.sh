#!/bin/bash
# Actualiza archivos de traducción (.ts) usando Docker
# Extrae cadenas traducibles del código Python
# Uso: ./update_translations.sh

echo "Actualizando archivos de traducción..."

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Error: Docker no está instalado"
    echo "Instálalo con: sudo apt install docker.io"
    exit 1
fi

# Ejecutar lupdate con Docker
docker run --rm \
    -v "$(pwd):/workspace" \
    -w /workspace \
    ubuntu:22.04 bash -c "
        apt-get update -qq && \
        apt-get install -y -qq qt6-tools-dev-tools > /dev/null 2>&1 && \
        lupdate dictatux/ -ts dictatux/translations/*.ts
    "

if [ $? -eq 0 ]; then
    echo "✓ Archivos de traducción actualizados"
    echo "Edita los archivos .ts en dictatux/translations/ y luego ejecuta ./compile_translations.sh"
else
    echo "✗ Error al actualizar traducciones"
    exit 1
fi
