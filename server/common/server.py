import socket
import logging
import threading
from threading import Lock, Barrier, BrokenBarrierError
from .server_protocol import ServerProtocol, TIMEOUT_SECONDS
import time

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = True
        self._client_threads = []
        self._lock = Lock()  # Lock para proteger recursos compartidos
        
        # Contadores para sincronización
        self._clients_processed = 0
        self._total_clients = 0
        
        # Barrera para sincronizar el perform_draw
        # Se inicializa con 1 (será reconfigurada cuando sepamos el número real de clientes)
        self._draw_barrier = None
        self._draw_lock = Lock()  # Lock adicional para proteger la creación/reset de la barrera

    def stop(self):
        """Stops the server and closes the socket"""
        with self._lock:
            if not self._running:
                return
            self._running = False
        
        logging.info("action: close_socket | result: in_progress")
        
        # Romper la barrera si existe para que no se queden esperando los threads
        with self._draw_lock:
            if self._draw_barrier:
                try:
                    self._draw_barrier.abort()
                except BrokenBarrierError:
                    pass
        
        try:
            # Send dummy connection to unblock accept()
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
        Server loop with multithreading

        Server that accepts new connections and handles each client
        in a separate thread to allow parallel processing.
        """
        try:
            while self._running:
                try:
                    # Set timeout for accept to periodically check if server should stop
                    # self._server_socket.settimeout(TIMEOUT_SECONDS)
                    client_sock, addr = self._server_socket.accept()
                    
                    # Check if we're still running after accept returns
                    if not self._running:
                        client_sock.close()
                        break
                    
                    logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
                    
                    # Incrementar contador de clientes totales y actualizar la barrera
                    with self._lock:
                        self._total_clients += 1
                        # Crear o reconfigurar la barrera con el nuevo total de hilos
                        with self._draw_lock:
                            if self._draw_barrier:
                                self._draw_barrier.abort()  # Abortar barrera anterior
                            self._draw_barrier = Barrier(self._total_clients)
                    
                    # Create and start a new thread to handle this client
                    client_thread = threading.Thread(
                        target=self.__handle_client_connection,
                        args=(client_sock,)
                    )
                    client_thread.daemon = True  # Make thread exit when main thread exits
                    client_thread.start()
                    
                    with self._lock:
                        self._client_threads.append(client_thread)
                        
                        
                except OSError as e:
                    if not self._running:  # Expected when stopping the server
                        break
                    logging.error(f"action: accept_connections | result: error | error: {e}")
                    if self._running:  # Only try to stop if not already stopping
                        self.stop()
                    break
                
        finally:
            # Wait for all client threads to finish
            for thread in self._client_threads:
                thread.join(timeout=0.1)  # Wait with timeout to avoid blocking forever
                
            # Close server socket
            try:
                self._server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # Socket might already be closed
            self._server_socket.close()
            logging.info("action: close_socket | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Thread function to handle a client connection.
        """
        protocol = None
        try:
            # Use protocol to handle client
            protocol = ServerProtocol(client_sock)
            success = protocol.handle_client()  # Procesar apuestas hasta notificación de fin
            # Esperar en la barrera después de handle_client
            time.sleep(1)   
            logging.info(f'action: wait_for_barrier | result: in_progress | thread: {threading.current_thread().name}')
            self._draw_barrier.wait()  # Todos los threads esperan aquí
            logging.info(f'action: wait_for_barrier | result: success | thread: {threading.current_thread().name}')
            
            if success:
                # Una vez que todos los threads pasan la barrera, realizar el sorteo
                logging.info("action: sorteo | result: success | thread: {}".format(threading.current_thread().name))
                protocol.perform_draw()
                #logging.info(f'action: perform_draw | thread: {threading.current_thread().name} | result: success')
            
            # Incrementar el contador de clientes procesados y decidir si detener
            should_stop = False
            with self._lock:
                self._clients_processed += 1
                if self._clients_processed == self._total_clients:
                    should_stop = True
        
            if should_stop:
                logging.info('action: stop | result: in_progress | thread: {}'.format(threading.current_thread().name))
                self.stop()
                    
        except Exception as e:
            logging.error(f"action: handle_client | result: error | error: {e}")
        finally:
            # Cerrar el socket después del sorteo
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client_sock.close()
            #logging.info(f'action: client_connection_closed | thread: {threading.current_thread().name} | result: success')