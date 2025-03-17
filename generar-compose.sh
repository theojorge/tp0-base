#!/bin/bash

# Verifica que se proporcionen la cantidad de parámetros correctos
if [ $# -ne 2 ]; then
    echo "Uso: $0 <nombre-archivo-salida> <cantidad-clientes>"
    exit 1
fi

OUTPUT_FILE=$1
CLIENT_COUNT=$2

# Verifica que la cantidad de clientes sea un número entero positivo
if ! [[ "$CLIENT_COUNT" =~ ^[0-9]+$ ]] || [ "$CLIENT_COUNT" -lt 1 ]; then
    echo "Uso: La cantidad de clientes debe ser un número entero positivo."
    exit 1
fi

echo "Nombre del archivo de salida: $OUTPUT_FILE"
echo "Cantidad de clientes: $CLIENT_COUNT"

# Invoca el subscript de Python para generar el archivo de Docker Compose
if ! python3 ./generador-compose.py "$OUTPUT_FILE" "$CLIENT_COUNT"; then
    echo "Error: No se pudo generar el archivo Docker Compose."
    exit 1
fi

echo "Archivo Docker Compose generado exitosamente: $OUTPUT_FILE"