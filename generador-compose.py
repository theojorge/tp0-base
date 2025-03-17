#!/usr/bin/env python3

import sys
import yaml

def generar_compose(nombre_archivo, num_clientes):
    try:
        if not num_clientes.isdigit():
            raise ValueError("El número de clientes debe ser un entero positivo")
        num_clientes = int(num_clientes)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    if not nombre_archivo.endswith('.yml') and not nombre_archivo.endswith('.yaml'):
        print("Error: El archivo de salida debe tener una extensión .yml o .yaml")
        sys.exit(1)

    # Configuración de la red
    network_config = {
        "networks": {
            "testing_net": {
                "ipam": {
                    "driver": "default",
                    "config": [{"subnet": "172.25.125.0/24"}]
                }
            }
        }
    }

    # Configuración del servidor
    server_config = {
        "server": {
            "container_name": "server",
            "image": "server:latest",
            "entrypoint": "python3 /main.py",
            "environment": [
                "PYTHONUNBUFFERED=1",
            ],
            "volumes": [
                "./server/config.ini:/config.ini"
            ],
            "networks": ["testing_net"]
        }
    }

    # Configuración de los clientes
    client_configs = {
        f"client{i}": {
            "container_name": f"client{i}",
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": [
                f"CLI_ID={i}",
            ],
            "volumes": [
                "./client/config.yaml:/config.yaml"
            ],
            "networks": ["testing_net"],
            "depends_on": ["server"]
        }
        for i in range(1, num_clientes + 1)
    }

    # Estructura final del archivo Docker Compose
    compose = {
        "name": "tp0",
        "services": {**server_config, **client_configs},
        **network_config
    }

    # Escritura del archivo YAML
    try:
        with open(nombre_archivo, 'w') as f:
            yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Error al escribir el archivo '{nombre_archivo}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <nombre-archivo-salida> <cantidad-clientes>")
        sys.exit(1)
    
    nombre_archivo = sys.argv[1]
    num_clientes = sys.argv[2]
    
    generar_compose(nombre_archivo, num_clientes)