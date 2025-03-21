import logging
from .utils import store_bets, Bet, load_bets, has_won

TIMEOUT_SECONDS = 5

class ServerProtocol:
    # Constantes para el estado de respuesta
    STATUS_SUCCESS = 0x01
    STATUS_ERROR   = 0x00
    
    def __init__(self):
        # Control para el sorteo
        self.agency_sockets = {}  # Diccionario para guardar las direcciones por agencia
        self.draw_done = False  # Flag para indicar si se realizó el sorteo
        self.all_agencies = set() # Conjunto para rastrear todas las agencias únicas que han enviado mensajes
        self.winners = {}  # Diccionario para almacenar ganadores por agenc

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
        conn.settimeout(TIMEOUT_SECONDS)
        try:
            # Leer 1 byte: Agencia
            agency_byte = self.read_exact(conn, 1)
            agency = agency_byte[0]
            self.all_agencies.add(agency)
            # Leer 1 byte: Batch Size (Cantidad de apuestas en el mensaje)
            batch_size_byte = self.read_exact(conn, 1)
            batch_size = batch_size_byte[0]
            # Notificación de fin de apuestas
            if batch_size == 0:
                self.agency_sockets[agency] = conn  # Guardar el socket activo

                logging.info(f"action: notificacion_fin | result: success | agencia: {agency}")
                #logging.debug(f"Socket activo guardado para la agencia: {agency}, total de sockets activos: {len(self.agency_sockets)}")

                # Enviar confirmación
                conn.sendall(bytes([self.STATUS_SUCCESS]))
                #logging.info(f"Confirmación enviada a la agencia: {agency}")

                # Si todas las agencias han terminado, realizar el sorteo
                if len(self.agency_sockets) >= len(self.all_agencies) and not self.draw_done:
                    self.draw_done = True
                    #logging.info("Se han recibido apuestas de todas las agencias, procediendo con el sorteo.")
                    return self.draw_done
                #logging.debug("No se ha alcanzado el número máximo de agencias, manteniendo la conexión abierta.")
                return self.draw_done  # No cerrar la conexión, se mantiene abierta
           
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
                    conn.close()
                    return self.draw_done # Terminar el proceso

            # Almacenar todas las apuestas del batch
            store_bets(bets)  

            logging.info(f"action: apuesta_recibida | result: success | cantidad: {batch_size}")

            #for bet in bets:
                #logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}")
            
            # Enviar respuesta de éxito (1 byte: STATUS_SUCCESS)
            conn.sendall(bytes([self.STATUS_SUCCESS]))
            
            conn.close()

            return self.draw_done

        except Exception as e:
            print("Error al procesar las apuestas:", e)
            try:
                conn.sendall(bytes([self.STATUS_ERROR]))  # Enviar error si falla
            except Exception as inner_e:
                print("Error al enviar respuesta de error:", inner_e)
            finally:
                conn.close()
                return self.draw_done
       
        
    def perform_draw(self):
        """Realiza el sorteo y notifica a todas las agencias conectadas."""
        # Cargar todas las apuestas
        all_bets = load_bets()

        # Inicializar diccionario de ganadores por agencia
        winners_by_agency = {}

        # Verificar cada apuesta
        for bet in all_bets:
            if has_won(bet):  # Si la apuesta es ganadora
                agency = bet.agency
                if agency not in winners_by_agency:
                    winners_by_agency[agency] = []
                winners_by_agency[agency].append(bet.document)  # Guardar DNI del ganador

        # Guardar los ganadores
        self.winners = winners_by_agency

        # Notificar a las agencias que enviaron apuestas
        self.notify_all_agencies()

    def notify_all_agencies(self):
        """Envía los resultados del sorteo a todas las agencias conectadas."""
        for agency, conn in self.agency_sockets.items():
            try:
                # 1. Obtener ganadores para esta agencia
                agency_winners = self.winners.get(agency, [])

                # 2. Enviar cantidad de ganadores (1 byte)
                conn.sendall(bytes([len(agency_winners)]))

                # 3. Enviar cada DNI
                for dni in agency_winners:
                    conn.sendall(bytes([len(dni)]))  # Enviar longitud del DNI
                    conn.sendall(dni.encode("utf-8"))  # Enviar DNI

            except Exception as e:
                logging.error(f"Error al notificar a la agencia {agency}: {e}")
        
            finally:
                conn.close()  # Cerrar la conexión después de enviar el resultado
 
        self.draw_done = False
        self.agency_sockets.clear()  # Limpiar conexiones activas después del sorteo
        

