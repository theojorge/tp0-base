#!/bin/bash

# Definir variables
MSG="TEST_ECHO_MESSAGE"
PORT=12345
CONTAINER_IMAGE="alpine:latest"
NETWORK_NAME="tp0_testing_net"
SERVER_NAME="server"

# Ejecutar prueba de comunicación con el servidor
RECEIVED_MSG=$(docker run --rm --network "$NETWORK_NAME" "$CONTAINER_IMAGE" \
  sh -c "echo $MSG | nc -w 5 $SERVER_NAME $PORT")

# Validar respuesta del servidor
if [ "$RECEIVED_MSG" == "$MSG" ]; then
  echo "action: test_echo_server | result: success"
  exit 0
else
  echo "action: test_echo_server | result: fail"
  exit 1
fi
