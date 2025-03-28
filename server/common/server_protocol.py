import logging
from .utils import store_bets, Bet, load_bets, has_won

TIMEOUT_SECONDS = 500

def short_write(conn, data: bytes):
    """Envía todos los bytes de `data` al socket `conn`, asegurando que no haya escrituras parciales."""
    total_sent = 0
    while total_sent < len(data):
        try:
            sent = conn.send(data[total_sent:])
            if sent == 0:
                raise RuntimeError("Conexión cerrada inesperadamente")
            total_sent += sent
        except Exception as e:
            raise RuntimeError(f"Error al escribir en el socket: {e}")
        
def read_exact(conn, n):
        """Lee exactamente n bytes de la conexión, evitando short read."""
        data = b""
        while len(data) < n:
            packet = conn.recv(n - len(data))
            if not packet:
                raise Exception("Conexión cerrada antes de leer todos los bytes")
            data += packet
        return data

class ServerProtocol:
    STATUS_SUCCESS = 0x01
    STATUS_ERROR = 0x00

    def __init__(self, conn):
        self.agency = None
        self.conn = conn
        self.winners = []
        self.bets = [] 

    def handle_client(self):
        self.conn.settimeout(TIMEOUT_SECONDS)
        try:
            agency = read_exact(self.conn, 1)[0]
            if self.agency is None:
                self.agency = agency
            elif self.agency != agency:
                raise RuntimeError(f"Agencia inconsistente: esperada {self.agency}, recibida {agency}")

            batch_size = read_exact(self.conn, 1)[0]
            if batch_size == 0:
                logging.info(f"action: notificacion_fin | result: success | agencia: {agency}")
                short_write(self.conn, bytes([self.STATUS_SUCCESS]))
                return True, None

    
            field_names = ["NOMBRE", "APELLIDO", "DOCUMENTO", "NACIMIENTO", "NUMERO"]

            for _ in range(batch_size):
                fields = {}
                try:
                    for field_name in field_names:
                        field_length = read_exact(self.conn, 1)[0]
                        field_value = read_exact(self.conn, field_length).decode("utf-8")
                        fields[field_name] = field_value
                    
                    self.bets.append(Bet(
                        agency=agency,
                        first_name=fields["NOMBRE"],
                        last_name=fields["APELLIDO"],
                        document=fields["DOCUMENTO"],
                        birthdate=fields["NACIMIENTO"],
                        number=fields["NUMERO"]
                    ))
                except Exception as e:
                    logging.error(f"Error procesando apuesta: {e}")
                    short_write(self.conn, bytes([self.STATUS_ERROR]))
                    self.conn.close()
                    return False, e
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {batch_size}")
            short_write(self.conn, bytes([self.STATUS_SUCCESS]))
            return False, None

        except Exception as e:
            logging.error(f"Error al procesar las apuestas: {e}")
            short_write(self.conn, bytes([self.STATUS_ERROR]))
            self.conn.close()
            return False, e

    def store_bets(self):
        store_bets(self.bets)
        self.bets = []
   
    def perform_draw(self):
        all_bets = load_bets()
        agency_bets = [bet for bet in all_bets if bet.agency == self.agency]
        self.winners = [bet.document for bet in agency_bets if has_won(bet)]
    
    def notify_agency(self):
        try:
            if self.conn.fileno() == -1:
                logging.error(f"Conexión ya cerrada, no se puede notificar a la agencia {self.agency}.")
                return 
            
            agency_winners = self.winners
            short_write(self.conn, bytes([len(agency_winners)]))

            for dni in agency_winners:
                short_write(self.conn, bytes([len(dni)]))
                short_write(self.conn, dni.encode("utf-8"))
        except Exception as e:
            logging.error(f"Error al notificar a la agencia {self.agency}: {e}")
        finally:
            self.conn.close()