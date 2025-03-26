#!/usr/bin/env python3

import sys
import yaml
import os
import configparser

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
        
    # Generar configuración dinámica
    generar_config_ini(num_clientes)

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
    client_configs = {}
    for i in range(1, num_clientes + 1):
        client_name = f"client{i}"
        csv_filename = f"agency-{i}.csv"
        
        client_configs[client_name] = {
            "container_name": client_name,
            "image": "client:latest",
            "entrypoint": "/client",
            "environment": [
                f"CLI_ID={i}",
            ],
            "volumes": [
                "./client/config.yaml:/config.yaml",
                f"./.data/{csv_filename}:/{csv_filename}"
            ],
            "networks": ["testing_net"],
            "depends_on": ["server"]
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
        
def generar_config_ini(num_clientes):
    """
    Genera un archivo config.ini dinámico basado en el número de clientes,
    preservando la configuración existente y actualizando solo valores específicos
    """
    # Ruta del archivo de configuración
    config_path = './server/config.ini'
    
    # Asegurar que el directorio exista
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Crear un parser de configuración
    config = configparser.ConfigParser()
    
    # Leer la configuración existente si el archivo ya existe
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Valores a actualizar dinámicamente
    dynamic_updates = {
        'SERVER_LISTEN_BACKLOG': str(num_clientes)
    }
    
    # Actualizar secciones existentes o crear secciones por defecto
    if not config.sections():
        config['DEFAULT'] = {
            'SERVER_PORT': '12345',
            'SERVER_IP': 'server',
            'LOGGING_LEVEL': 'DEBUG'
        }
    
    # Aplicar actualizaciones dinámicas
    for section in config.sections() or ['DEFAULT']:
        for key, value in dynamic_updates.items():
            if config.has_option(section, key):
                config.set(section, key, value)
            else:
                config.set(section, key, value)
    
    # Escribir el archivo de configuración
    try:
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        print(f"Archivo de configuración actualizado en {config_path}")
    except Exception as e:
        print(f"Error al generar el archivo de configuración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Uso: {sys.argv[0]} <nombre-archivo-salida> <cantidad-clientes>")
        sys.exit(1)
    
    nombre_archivo = sys.argv[1]
    num_clientes = sys.argv[2]
    
    generar_compose(nombre_archivo, num_clientes)