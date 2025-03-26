import socket
import logging
import multiprocessing
from multiprocessing import Lock, Barrier, Value, Event
from .server_protocol import ServerProtocol, TIMEOUT_SECONDS
import time

class Server:
    def __init__(self, port, listen_backlog):
        # Inicializar socket del servidor
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._running = multiprocessing.Value('b', True)  # Valor compartido para indicar si el server está corriendo
        self._client_processes = []
        self._lock = Lock()

        # Contadores compartidos
        self._clients_processed = Value('i', 0)
        self._total_clients = Value('i', 0)
        self._stop_event = Event()
        
        # Barrera de sincronización
        self._draw_barrier = Barrier(listen_backlog)  # Se configura con el máximo de clientes esperados

    def stop(self):
        """Detiene el servidor y cierra el socket"""
        with self._lock:
            if not self._running.value:
                return
            self._running.value = False  # Indicar que el servidor debe detenerse
            self._stop_event.set()
        logging.info("action: close_socket | result: in_progress")

        # Romper la barrera si es necesario
        try:
            self._draw_barrier.abort()
        except Exception:
            pass
   
        try:
            # Enviar conexión dummy para desbloquear `accept()`
            dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = self._server_socket.getsockname()
            dummy_socket.connect(('localhost', server_address[1]))
        except OSError as e:
            logging.error(f"action: close_socket | result: error | error: {e}")
        finally:
            try:
                dummy_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            dummy_socket.close()

        # Cerrar el socket del servidor
        try:
            self._server_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self._server_socket.close()
        logging.info("action: close_socket | result: success")

    
    def run(self):
        """Bucle principal del servidor con multiprocessing."""
        try:
            while self._running.value:
                try:
                    client_sock, addr = self._server_socket.accept()
                    
                    if not self._running.value:
                        client_sock.close()
                        for process in self._client_processes:
                         process.join(timeout=0.1)
                        break
                    
                    logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')

                    # Incrementar contador de clientes
                    with self._lock:
                        self._total_clients.value += 1
                    
                    # Crear y lanzar un proceso para manejar al cliente
                    client_process = multiprocessing.Process(
                        target=self.__handle_client_connection,
                        args=(client_sock, self._stop_event)
                    )
                    client_process.daemon = True
                    client_process.start()

                    with self._lock:
                        self._client_processes.append(client_process)
                        
                except OSError as e:
                    if not self._running.value:
                        break
                    logging.error(f"action: accept_connections | result: error | error: {e}")
                    if self._running.value:
                        self.stop()
                    break
                
        finally:
            # Esperar a que todos los procesos terminen
            for process in self._client_processes:
                process.join(timeout=0.1)

            # Cerrar el socket del servidor
            try:
                self._server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._server_socket.close()
            logging.info("action: close_socket | result: success")

    def __handle_client_connection(self, client_sock, stop_event):
        """Función que maneja la conexión de un cliente en un proceso separado."""
        protocol = None
        try:
            protocol = ServerProtocol(client_sock)
            success = False
            while not success:
                success, error = protocol.handle_client() # Nuevo método paso a paso
                if error is not None:  # Si hay un error, salir del bucle 
                  break  
                if stop_event.is_set():
                    return
                
            
            # Esperar en la barrera después de `handle_client`
            logging.info(f'action: wait_for_barrier | result: in_progress | process: {multiprocessing.current_process().name}')
            try:
                self._draw_barrier.wait()
                logging.info(f'action: wait_for_barrier | result: success | process: {multiprocessing.current_process().name}')
            except Exception as e:
                logging.warning(f'action: wait_for_barrier | result: aborted | process: {multiprocessing.current_process().name}')
                return

            if success:
                logging.info(f"action: sorteo | result: success | process: {multiprocessing.current_process().name}")
                protocol.perform_draw()
                protocol.notify_agency()
                
            
            # Incrementar el contador de clientes procesados y decidir si detener
            should_stop = False
            with self._lock:
                self._clients_processed.value += 1
                if self._clients_processed.value == self._total_clients.value:
                    should_stop = True
        
            if should_stop:
                logging.info(f'action: stop | result: in_progress | process: {multiprocessing.current_process().name}')
                self.stop()
                    
        except Exception as e:
            logging.error(f"action: handle_client | result: error | error: {e}")
        finally:
            try:
                client_sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client_sock.close()
