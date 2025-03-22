import logging
from .utils import store_bets, Bet, load_bets, has_won

TIMEOUT_SECONDS = 500

class ServerProtocol:
    # Constantes para el estado de respuesta
    STATUS_SUCCESS = 0x01
    STATUS_ERROR   = 0x00
    
    def __init__(self, conn):
        # Control para el sorteo
        self.agency = None # Agencia que envio la notificacion de fin de sorteo
        self.conn = conn # Conexion con la agencia
        self.winners = []  # Lista para almacenar ganadores 

    def read_exact(self, n):
        """Lee exactamente n bytes de la conexión, evitando short read."""
        data = b""
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                raise Exception("Conexión cerrada antes de leer todos los bytes")
            data += packet
        return data

    def handle_client(self):
        """Procesa la conexión del cliente leyendo apuestas en batch continuamente."""
        self.conn.settimeout(TIMEOUT_SECONDS)
        try:
            while True:  # Bucle infinito hasta recibir notificación de fin
                # Leer 1 byte: Agencia
                agency_byte = self.read_exact(1) 
                agency = agency_byte[0]
                if self.agency is None:
                    self.agency = agency  # Establecer la agencia la primera vez
                elif self.agency != agency:
                    raise Exception(f"Agencia inconsistente: esperada {self.agency}, recibida {agency}")

                # Leer 1 byte: Batch Size (Cantidad de apuestas en el mensaje)
                batch_size_byte = self.read_exact(1)
                batch_size = batch_size_byte[0]

                # Notificación de fin de apuestas
                if batch_size == 0:
                    logging.info(f"action: notificacion_fin | result: success | agencia: {agency}")
                
                    # Enviar confirmación
                    self.conn.sendall(bytes([self.STATUS_SUCCESS]))

                    return True  # Retornar, pero socket sigue abierto

                bets = []  # Lista para almacenar todas las apuestas recibidas
                field_names = ["NOMBRE", "APELLIDO", "DOCUMENTO", "NACIMIENTO", "NUMERO"]

                for _ in range(batch_size):  # Procesar cada apuesta en el batch
                    fields = {}
                    try:
                        for field_name in field_names:
                            # Leer 1 byte: longitud del campo
                            length_byte = self.read_exact(1)
                            field_length = length_byte[0]

                            # Leer el valor del campo (n bytes)
                            field_value_bytes = self.read_exact(field_length)
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
                        if bets:
                            store_bets(bets)
                            logging.info(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
                            self.conn.sendall(bytes([self.STATUS_ERROR]))
                        else:
                            logging.info(f"action: apuesta_recibida | result: fail | cantidad: 0")
                            self.conn.sendall(bytes([self.STATUS_ERROR]))
                        return False  # Terminar si hay error grave

                # Almacenar todas las apuestas del batch
                store_bets(bets)
                logging.info(f"action: apuesta_recibida | result: success | cantidad: {batch_size}")

                # Enviar respuesta de éxito (1 byte: STATUS_SUCCESS)
                self.conn.sendall(bytes([self.STATUS_SUCCESS]))
                # Aquí NO cerramos la conexión, seguimos leyendo el próximo batch

        except Exception as e:
            print("Error al procesar las apuestas:", e)
            try:
                self.conn.sendall(bytes([self.STATUS_ERROR]))  # Enviar error si falla
            except Exception as inner_e:
                print("Error al enviar respuesta de error:", inner_e)
            finally:
                self.conn.close()  # Solo cerrar en caso de excepción grave
                return False
        
        
    def perform_draw(self):
        """Realiza el sorteo para las apuestas de esta agencia."""
        # Cargar todas las apuestas (se asume que load_bets puede filtrar por agencia si es necesario)
        all_bets = load_bets()

        # Filtrar solo las apuestas de esta agencia
        agency_bets = [bet for bet in all_bets if bet.agency == self.agency]

        # Verificar cada apuesta de la agencia
        self.winners = [bet.document for bet in agency_bets if has_won(bet)]

        # Notificar a la agencia
        self.notify_agency()

    def notify_agency(self):
        """Envía los resultados del sorteo a la agencia conectada."""
        try:
            # 1. Obtener ganadores para esta agencia
            agency_winners = self.winners

            # 2. Enviar cantidad de ganadores (1 byte)
            self.conn.sendall(bytes([len(agency_winners)]))

            # 3. Enviar cada DNI
            for dni in agency_winners:
                self.conn.sendall(bytes([len(dni)]))  # Enviar longitud del DNI
                self.conn.sendall(dni.encode("utf-8"))  # Enviar DNI

        except Exception as e:
            logging.error(f"Error al notificar a la agencia {self.agency}: {e}")
        
        finally:
            self.conn.close()  # Cerrar la conexión después de enviar el resultado
 
        
        

