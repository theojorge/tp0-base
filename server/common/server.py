import socket
import logging
from .server_protocol import ServerProtocol  # Asegúrate de que la ruta sea correcta

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        self._protocol = ServerProtocol()
        

    def stop(self):
        """Stops the server and closes the socket"""
        logging.info("action: close_socket | result: in_progress")
        self._running = False
        try:
             dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
             server_address = self._server_socket.getsockname()
             dummy_socket.connect(('localhost', server_address[1]))
             
        except OSError as e:
             logging.error(f"action: close_socket | result: error | error: {e}")
        finally:
            try:
                dummy_socket.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                logging.error(f"action: shutdown_dummy_socket | result: error | error: {e}")
            dummy_socket.close()
        
    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
    
        while self._running:
         try:
            client_sock = self.__accept_new_connection()
            if client_sock and self._running:  
                self.__handle_client_connection(client_sock)
         except Exception as e:
            logging.error(f"Error en el servidor: {e}")
            self.stop() 
            
        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()
        logging.info("action: close_socket | result: success")
            
    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self._protocol.handle_client(client_sock)
           
            
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        
        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
