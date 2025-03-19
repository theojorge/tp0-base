# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso

El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de: **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target                | accion                                                                                                                                                                                                                                                                                                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker-compose-up`   | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers.                                                                                                                                                                                   |
| `docker-compose-down` | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
| `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose.                                                                                                                                                                                                                            |
| `docker-image`        | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto.                                                                                                                       |
| `build`               | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_.                                                                                                                                         |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar.

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.

### Cliente

se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:

1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up` y luego `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```

## Parte 1: Introducción a Docker

En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:

Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes. El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc.

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:

Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).

### Ejercicio N°3:

Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `

### Ejercicio N°4:

Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:

Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente

Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Servidor

Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:

Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:

- Definición de un protocolo para el envío de los mensajes.
- Serialización de los datos.
- Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
- Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

### Ejercicio N°6:

Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_).
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del _batch_ fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB.

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia

En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_, deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega

Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
(hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Respetar las entradas de log planteadas en los ejercicios, pues son las que se chequean en cada uno de los tests.

La corrección personal tendrá en cuenta la calidad del código entregado y casos de error posibles, se manifiesten o no durante la ejecución del trabajo práctico. Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).

## Entrega TP 0

### Ejercicio 1:

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

que es el nombre utilizado por defecto en el Makefile, será necesario ejecutarlo manualmente o modificar el Makefile para que utilice el nombre correcto. Para hacerlo manualmente, primero se deben crear las imágenes ejecutando make docker-image. Luego, se lanza el contenedor con docker compose -f <nombre_archivo_salida> up -d --build.

El script también maneja errores en los parámetros de entrada, como ingresar un valor no numérico o negativo para la cantidad de clientes, o una cantidad incorrecta de argumentos, o un formato de archivo distinto de .yml o .yaml. En estos casos, se muestra un mensaje de error y el script se detiene.

### Ejercicio 3:

Se ha creado un script llamado `validar-echo-server.sh` que verifica el correcto funcionamiento del servidor echo utilizando `netcat`.

Para ejecutar el script de validación, asegúrate de que el servidor esté en funcionamiento y ejecuta:

```bash
./validar-echo-server.sh
```

Esto permitirá verificar que el servidor echo esté funcionando correctamente.

Se realizó un cambio en el script `generar-compose.sh` para que acepte 0 como cantidad de clientes. Este ajuste fue necesario para que los tests del Ejercicio 3 funcionen correctamente, permitiendo así la ejecución de pruebas sin requerir un número mínimo de clientes.

### Ejercicio 4:

He modificado tanto el servidor como el cliente para manejar de manera adecuada las señales SIGTERM, asegurando que todos los recursos (descriptores de archivo, sockets, etc.) se cierren correctamente antes de que la aplicación principal finalice.

En la implementación del cliente, he agregado un manejador de señales que captura SIGTERM. También implementé un método Stop() que utiliza un canal `stopCh chan struct{}` como mecanismo principal para coordinar la detención del loop del cliente. Sin embargo, si la ejecución está bloqueada en la operación `ReadString('\n')`, la verificación del canal `stopCh` no podrá realizarse hasta que la operación de lectura se complete o falle. Además de utilizar el canal, cierra la conexión, establece la conexión como nula tras un cierre exitoso y registra el cierre exitoso de la conexión. Este método es invocado por el manejador de señales cuando se recibe SIGTERM.

Para el servidor, he añadido una función manejadora de señales para SIGTERM y mejorado el método stop(). Este método ahora registra el inicio del cierre del socket, establece una bandera de ejecución en falso, cierra correctamente el socket utilizando SHUT_RDWR, y registra el cierre exitoso del socket, manejando también posibles errores durante este proceso.

Además, se ha implementado un sistema de logging estructurado para todas las operaciones, que registra eventos como action: shutdown_initiated al recibir SIGTERM, así como action: close_connection y action: close_socket durante el cierre de recursos.

## Ejercicio 4: Actualización

Este ejercicio implementa una mejora en el mecanismo de cierre del servidor, reemplazando el enfoque anterior de `shutdown` + `sys.exit(0)` por un método más elegante que utiliza un socket ficticio (dummy socket) para interrumpir el bloqueo causado por la llamada `accept()`.

### Problema a Resolver

El servidor TCP queda bloqueado en la llamada `accept()` cuando está esperando conexiones entrantes. Cuando se desea cerrar el servidor (por ejemplo, al recibir una señal `SIGTERM`), el hilo principal queda bloqueado en esta llamada, lo que impide un cierre limpio y ordenado del servidor.

### Solución Implementada

Para resolver este problema, se ha implementado una técnica que consiste en:

1. Cambiar el estado interno del servidor (`self._running = False`).
2. Crear un socket dummy que se conecta al propio servidor.
3. Esta conexión hace que el método `accept()` se desbloquee.
4. Al salir del bloqueo, se verifica el estado `self._running` para decidir si continuar o terminar.

### Código Clave de la Implementación

#### Método de Detención del Servidor

```python
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
```

#### Bucle Principal del Servidor Mejorado

```python
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
```

### Flujo de Ejecución

1. **Estado Normal de Ejecución**:

   - El servidor se ejecuta en un bucle infinito `while self._running`.
   - En cada iteración, se bloquea en `accept_new_connection()` esperando conexiones de clientes.

2. **Iniciando el Cierre**:

   - Cuando se requiere cerrar el servidor, se llama al método `stop()`.
   - El método cambia `self._running = False`.
   - Crea un socket dummy y se conecta al servidor para desbloquear `accept()`.

3. **Procesando el Cierre**:

   - La conexión dummy hace que el servidor salga del bloqueo en `accept()`.
   - El bucle verifica `if client_sock and self._running`.
   - Como `self._running` es `False`, no se procesa la conexión dummy.
   - El bucle principal termina y se ejecutan las operaciones de limpieza.

4. **Limpieza Final**:
   - Se cierra correctamente el socket del servidor con `shutdown()` y `close()`.
   - Se registra el cierre exitoso en el log.

### Ventajas de Esta Implementación

- **Cierre Limpio**: Permite que el servidor se cierre de manera ordenada.
- **No Forzado**: Evita el uso de `sys.exit(0)` que termina abruptamente la ejecución.
- **Robusto**: Maneja correctamente los errores que pueden ocurrir durante el cierre.
- **Controlado**: Permite un adecuado manejo de recursos antes de finalizar.

### Consideraciones de Implementación

- Es crucial verificar `self._running` después de `accept()` para ignorar la conexión del socket dummy.
- El método `shutdown()` se utiliza tanto en el socket dummy como en el socket del servidor para asegurar un cierre completo.
- Se implementan bloques `try/except` para manejar posibles errores durante el proceso de cierre.

### Ejercicio 5

El protocolo se basa en la serialización de varios campos de datos que se envían entre el cliente y el servidor. Los datos están organizados en bloques de información, cada uno con un identificador y longitud específica. A continuación, se describe la estructura detallada de los datos enviados.

## Campos del Protocolo

Los siguientes campos están involucrados en el protocolo de comunicación:

- **Agencia (1 byte)**: Este campo representa el identificador de la agencia (un número entre 1 y 255). Este campo no tiene un identificador asociado y se transmite como el primer byte con su valor.

- **NOMBRE (1 byte de longitud + N bytes de valor)**: Este campo almacena el nombre del cliente. La longitud del nombre está indicada por el primer byte, y los bytes siguientes contienen el valor del nombre.

- **APELLIDO (1 byte de longitud + N bytes de valor)**: Similar al campo NOMBRE, este campo contiene el apellido del cliente. La longitud se especifica con un byte, y los bytes siguientes contienen el valor del apellido.

- **DNI (1 byte de longitud + N bytes de valor)**: El número de documento de identidad del cliente. Al igual que los otros campos, su longitud está indicada por el primer byte y el valor por los bytes siguientes.

- **NACIMIENTO (1 byte de longitud + N bytes de valor)**: Fecha de nacimiento del cliente en formato de texto. Este campo se estructura de la misma forma que los anteriores.

- **NUMERO (1 byte de longitud + N bytes de valor)**: El número de apuesta proporcionado por el cliente. Este campo también sigue el mismo formato que los anteriores.

## Especificaciones

**Endianess**: Los campos que requieren longitud (por ejemplo, los campos de texto) se codifican en Big Endian.
**Longitud de los Campos**: Cada campo tiene un byte que indica su longitud. Este valor de longitud es un número entero de 1 byte (valor máximo de 255), por lo que los campos no pueden exceder los 255 bytes.

## Respuesta del Servidor

El servidor responde con un byte que indica si la operación fue exitosa o no:

- **STATUS_SUCCESS (0x01)**: Indica que la apuesta fue procesada con éxito.
- **STATUS_ERROR (0x00)**: Indica que ocurrió un error en el procesamiento de la apuesta.

## Flujo de Comunicación

El flujo de comunicación entre el cliente y el servidor sigue estos pasos:

1. **Cliente**: El cliente primero envía los datos en el siguiente orden:

   - Agencia (1 byte)
   - Nombre
   - Apellido
   - DNI
   - Nacimiento
   - Número de apuesta

2. **Servidor**: El servidor procesa los datos, los almacena (o maneja cualquier error que ocurra) y devuelve una respuesta de éxito o error mediante un solo byte.

## Detalles del Cliente

El cliente envía el mismo bet de manera continua en un bucle en `StartClientLoop`, utilizando las variables de entorno para definir los valores a enviar. Si alguna de estas variables de entorno no está definida, el cliente recurrirá a valores predeterminados. Este enfoque se implementa porque el objetivo principal del ejercicio es el protocolo de comunicación. Entonces parte del comportamiento del cliente de los ejercicios anteriores se mantuvo ya que lo que se espera es que el cliente reciba como variables de entorno los campos que representan la apuesta de una persona y los envíe al servidor.

# Ejercicio 6

## Descripción General

Este ejercicio implementa un sistema de procesamiento de apuestas en batch con ajustes dinámicos basados en restricciones de tamaño y cantidad. El sistema optimiza la transmisión de datos entre clientes y servidor, evitando la pérdida de apuestas debido a limitaciones en el buffer de salida.

## Características Principales

- **Ajuste dinámico de batches**: El sistema ajusta automáticamente el número de apuestas por batch según dos restricciones:

  - Máximo 255 apuestas por batch (limitación de 1 byte).
  - Tamaño máximo de 8KB por batch.

- **Persistencia de apuestas**: Las apuestas que no pueden incluirse en un batch debido a las restricciones se almacenan para su inclusión en el siguiente batch.

- **Configuración flexible**: Los parámetros de batch se definen en `config.yaml` bajo la clave `batch: maxAmount`.

## Funcionamiento del Sistema

### Cliente

1. **Lectura de datos**: Cada cliente lee apuestas desde su archivo correspondiente en `.data/agency-{N}.csv`.

2. **Formación de batches**:

   - Si el número de apuestas supera 255, se limita a 255 y se muestra una advertencia:
     ```
     WARNI BatchSize ({total_apuestas}) excede el límite de 1 byte. Se procesarán solo 255 apuestas.
     ```
   - Si el tamaño del batch excede 8KB después del primer ajuste, se reduce aún más:
     ```
     WARNI BatchSize ({apuestas_actualizadas}) exceden los 8kb. Se ajustará a {nuevo_límite}.
     ```

3. **Envío de datos**: El cliente envía los batches con el siguiente formato:

   - 1 byte para el ID de agencia.
   - 1 byte para la cantidad de apuestas en el batch.
   - Para cada apuesta:
     - NOMBRE (1 byte longitud + N bytes valor)
     - APELLIDO (1 byte longitud + N bytes valor)
     - DNI (1 byte longitud + N bytes valor)
     - NACIMIENTO (1 byte longitud + N bytes valor)
     - NUMERO (1 byte longitud + N bytes valor)

   Las apuestas no enviadas se guardan para el siguiente batch.

### Servidor

1. **Procesamiento de batches**: El servidor procesa cada batch recibido.

2. **Respuestas**:
   - **Éxito**: Si todas las apuestas son procesadas correctamente:
     ```
     INFO action: apuesta_recibida | result: success | cantidad: {CANTIDAD_DE_APUESTAS}
     ```
   - **Error**: Si hay un error en la lectura:
     ```
     INFO action: apuesta_recibida | result: fail | cantidad: {CANTIDAD_DE_APUESTAS}
     ```

## Parámetros de Configuración

Los parámetros del sistema se definen en `config.yaml`:

```yaml
batch:
  maxAmount: Número máximo de apuestas por batch (se ajustará automáticamente si es necesario)
```

## Limitaciones y Consideraciones

- Máximo 255 apuestas por batch (limitación de representación en 1 byte).
- Tamaño máximo de batch de 8KB.
- Los nombres, apellidos, DNIs, fechas de nacimiento y números de apuesta deben poder representarse cada uno con una longitud en 1 byte.

## Configuración con Docker

El sistema utiliza Docker para su implementación, con la siguiente configuración:

### Actualización del Generador de Docker-Compose

Se ha actualizado el script `generar_compose.py` para incluir automáticamente los archivos CSV de apuestas en los volúmenes de los contenedores cliente. La parte clave del código que implementa esta funcionalidad es:

```python
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
```

### Funcionamiento de los Volúmenes

El sistema carga los archivos CSV de apuestas desde un directorio host `.data/` y los mapea dentro de cada contenedor cliente:

- Cada cliente tiene acceso a su propio archivo de apuestas correspondiente.
- Los archivos se mantienen persistentes fuera de los contenedores.
- El formato del mapeo de volumen es: `./.data/agency-{N}.csv:/{csv_filename}`.
