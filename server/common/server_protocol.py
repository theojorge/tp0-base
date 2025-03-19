import logging
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
        """Procesa la conexión del cliente leyendo apuestas en batch."""
        try:
            # Leer 1 byte: Agencia
            agency_byte = self.read_exact(conn, 1)
            agency = agency_byte[0]

            # Leer 1 byte: Batch Size (Cantidad de apuestas en el mensaje)
            batch_size_byte = self.read_exact(conn, 1)
            batch_size = batch_size_byte[0]

            bets = []  # Lista para almacenar todas las apuestas recibidas
            field_names = ["NOMBRE", "APELLIDO", "DOCUMENTO", "NACIMIENTO", "NUMERO"]

            for _ in range(batch_size):  # Procesar cada apuesta en el batch
                fields = {}

                try:
                    for field_name in field_names:
                        # Leer 1 byte: longitud del campo
                        length_byte = self.read_exact(conn, 1)
                        field_length = length_byte[0]

                        # Leer el valor del campo (n bytes)
                        field_value_bytes = self.read_exact(conn, field_length)
                        field_value = field_value_bytes.decode("utf-8")

                        # Guardar el campo en el diccionario
                        fields[field_name] = field_value
                        

                    # Crear el objeto Bet
                    bet = Bet(
                        agency=agency,
                        first_name=fields["NOMBRE"],
                        last_name=fields["APELLIDO"],
                        document=fields["DOCUMENTO"],
                        birthdate=fields["NACIMIENTO"],
                        number=fields["NUMERO"]
                    )

                    bets.append(bet)  # Agregar la apuesta a la lista

                except Exception as e:
                    logging.error(f"Error procesando apuesta: {e}")
                    
                    # Si al menos una apuesta se recibió correctamente, la almacenamos
                    if bets:
                        store_bets(bets)
                        logging.info(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
                        conn.sendall(bytes([self.STATUS_ERROR]))  
                    else:
                        logging.info(f"action: apuesta_recibida | result: fail | cantidad: 0")
                        conn.sendall(bytes([self.STATUS_ERROR]))  

                    return  # Terminar el proceso

            # Almacenar todas las apuestas del batch
            store_bets(bets)  

            logging.info(f"action: apuesta_recibida | result: success | cantidad: {batch_size}")

            #for bet in bets:
                #logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}")
            
            # Enviar respuesta de éxito (1 byte: STATUS_SUCCESS)
            conn.sendall(bytes([self.STATUS_SUCCESS]))

        except Exception as e:
            print("Error al procesar las apuestas:", e)
            try:
                conn.sendall(bytes([self.STATUS_ERROR]))  # Enviar error si falla
            except Exception as inner_e:
                print("Error al enviar respuesta de error:", inner_e)
        finally:
            conn.close()
