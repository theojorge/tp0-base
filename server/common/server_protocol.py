import logging
import socket
import struct
from .utils import store_bets, Bet

class ServerProtocol:
    # Constantes para el estado de respuesta
    STATUS_SUCCESS = 0x01
    STATUS_ERROR   = 0x00

    def read_exact(self, sock, n):
        """Lee exactamente n bytes de la conexión, evitando short read."""
        data = b""
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                raise Exception("Conexión cerrada antes de leer todos los bytes")
            data += packet
        return data

    def handle_client(self, conn):
        """Procesa la conexión del cliente leyendo los campos, almacenando la apuesta y enviando respuesta."""
        try:
            fields = {}
            
            # Leer 1 byte: la agencia
            agency_byte = self.read_exact(conn, 1)
            agency = agency_byte[0]

            # Se esperan 5 campos, sin necesidad de identificador
            field_names = ["NOMBRE", "APELLIDO", "DOCUMENTO", "NACIMIENTO", "NUMERO"]
            for field_name in field_names:
                # Leer 1 byte: longitud del campo
                length_byte = self.read_exact(conn, 1)
                field_length = length_byte[0]

                # Leer el valor del campo (n bytes)
                field_value_bytes = self.read_exact(conn, field_length)
                field_value = field_value_bytes.decode("utf-8")

                # Guardar el campo usando el nombre
                fields[field_name] = field_value

            # Obtener los datos de los campos
            dni = fields.get("DOCUMENTO", "")
            numero = fields.get("NUMERO", "")
            nombre = fields.get("NOMBRE", "")
            apellido = fields.get("APELLIDO", "")
            nacimiento = fields.get("NACIMIENTO", "")
            
            # Crear la apuesta
            bet = Bet(agency=agency, first_name=nombre, last_name=apellido, document=dni, birthdate=nacimiento, number=numero)
            
            # Almacenar la apuesta
            store_bets([bet]) 

            logging.info(f'action: apuesta_almacenada | result: success | dni: {dni} | numero: {numero}')
            
            # Enviar respuesta de éxito (1 byte: STATUS_SUCCESS)
            conn.sendall(bytes([self.STATUS_SUCCESS]))
        
        except Exception as e:
            print("Error al procesar la apuesta:", e)
            try:
                # En caso de error, enviar STATUS_ERROR
                conn.sendall(bytes([self.STATUS_ERROR]))
            except Exception as inner_e:
                print("Error al enviar respuesta de error:", inner_e)
        finally:
            conn.close()