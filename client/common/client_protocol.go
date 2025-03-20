package common

import (
	"bytes"
	"fmt"
	"net"
	
)

// Definir constantes para los identificadores de los campos
const (
	STATUS_SUCCESS = 0x01
	STATUS_ERROR   = 0x00
    BYTE_SIZE     = 255   // Máximo número de apuestas por batch
	MAX_BUFFER_SIZE    = 8192  // Tamaño máximo del buffer en bytes
)

type ProtocolClient struct {
	conn net.Conn
}

func (p *ProtocolClient) serialize(bets []Bet, agencia int) ([]byte, int, []Bet, error) {
	var buffer bytes.Buffer

	if agencia < 0 || agencia > BYTE_SIZE {
		return nil, 0, nil, fmt.Errorf("El número de agencia debe estar entre 0 y %d", BYTE_SIZE)
	}


	// Escribir el byte de agencia
	buffer.WriteByte(byte(agencia))

	// Posición donde escribiremos el tamaño del batch
	batchPos := buffer.Len()
	buffer.WriteByte(0) // Placeholder para el batchSize

	validBets := 0 // Contador de apuestas válidas
    var remainingBets []Bet // Contador de apuestas sobrantes

	if len(bets) > BYTE_SIZE {
        log.Warningf("BatchSize (%d) excede el límite de 1 byte. Se procesarán solo %d apuestas.", len(bets), BYTE_SIZE)
		bets = bets[:BYTE_SIZE]
		// Las apuestas que exceden 255 van directamente a remainingBets
		remainingBets = bets[BYTE_SIZE:]
	}

	// Función auxiliar para escribir los campos con su longitud (1 byte) y su valor
	writeField := func(data string) bool {
		fieldSize := len(data) + 1 // 1 byte para la longitud del campo
		if buffer.Len()+fieldSize > MAX_BUFFER_SIZE {
			return false // Indica que no hay espacio suficiente
		}

		buffer.WriteByte(byte(len(data))) // Escribir longitud
		buffer.Write([]byte(data))        // Escribir contenido
		return true
	}

	// Serializar cada apuesta en el batch
	for i, bet := range bets {
		startSize := buffer.Len() // Guardamos el tamaño antes de escribir la apuesta

        if len(bet.Nombre) > BYTE_SIZE || len(bet.Apellido) > BYTE_SIZE || len(bet.DNI) > BYTE_SIZE ||
			len(bet.Nacimiento) > BYTE_SIZE || len(bet.Numero) > BYTE_SIZE {
			fmt.Printf("Error: Un campo en esta apuesta excede los %d bytes, se omite esta apuesta.", BYTE_SIZE)
			continue // Salta esta apuesta y sigue con la siguiente
		}

		// Intentamos escribir los campos de la apuesta
		if !writeField(bet.Nombre) || !writeField(bet.Apellido) || !writeField(bet.DNI) ||
			!writeField(bet.Nacimiento) || !writeField(bet.Numero) {
            // Si no entra en el buffer, revertimos esta apuesta y cortamos el loop
		    buffer.Truncate(startSize)
            log.Warningf("BatchSize (%d) exceden los 8kb. Se ajustará a %d.", len(bets), validBets)
            remainingBets = append(bets[i:], remainingBets...)
			break 
		}

		validBets++ // Solo se incrementa si la apuesta completa se añadió correctamente
	}

	// Escribir el tamaño real del batch en la posición reservada
	buffer.Bytes()[batchPos] = byte(validBets)

	return buffer.Bytes(), validBets, remainingBets, nil
}



func (p *ProtocolClient) send_bets(bets []Bet, agencia int) (int, []Bet) {

	// Serializar los datos antes de enviarlos
	data, cantBets, remainingBets, err := p.serialize(bets, agencia)
	if err != nil {
		fmt.Println("Error al serializar los datos:", err)
		return 0, nil
	}

	// Enviar los datos al servidor
	_, err = p.conn.Write(data)
	if err != nil {
		fmt.Println("Error al enviar los datos:", err)
		return 0, nil
	}

	// Recibir solo 1 byte de respuesta del servidor
	buffer := make([]byte, 1)
	n, err := p.conn.Read(buffer)
	if err != nil {
		fmt.Println("Error al recibir la respuesta:", err)
		return 0, nil
	}

	// Verificar que realmente se haya leído 1 byte
	if n != 1 {
		fmt.Println("Error: No se recibió el byte esperado")
		return 0, nil
	}
 
	// Interpretar la respuesta del servidor
	if buffer[0] == STATUS_SUCCESS {
		log.Infof("action: apuesta_enviadas | result: success | cantidad: %d", cantBets)
        return cantBets, remainingBets
	} else if buffer[0] == STATUS_ERROR {
		log.Infof("action: apuesta_enviadas | result: error")
        return 0, nil
	} else {
		fmt.Printf("Respuesta desconocida del servidor: %x\n", buffer[0])
        return 0, nil
	}
}
