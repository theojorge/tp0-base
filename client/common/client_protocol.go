package common

import (
	"bytes"
	"fmt"
	"net"
)

const (
	STATUS_SUCCESS = 0x01
	STATUS_ERROR   = 0x00
	BYTE_SIZE      = 255
	MAX_BUFFER_SIZE = 8192
)

type ProtocolClient struct {
	conn net.Conn
}

func shortWrite(conn net.Conn, data []byte) error {
	totalWritten := 0
	for totalWritten < len(data) {
		n, err := conn.Write(data[totalWritten:])
		if err != nil {
			return fmt.Errorf("error al escribir datos: %w", err)
		}
		totalWritten += n
	}
	return nil
}

func readExact(conn net.Conn, size int) ([]byte, error) {
	buffer := make([]byte, size)
	totalRead := 0
	for totalRead < size {
		n, err := conn.Read(buffer[totalRead:])
		if err != nil {
			return nil, fmt.Errorf("error al leer datos: %w", err)
		}
		totalRead += n
	}
	return buffer, nil
}

func (p *ProtocolClient) serialize(bets []Bet, agencia int) ([]byte, int, []Bet, error) {
	var buffer bytes.Buffer

	if agencia < 0 || agencia > BYTE_SIZE {
		return nil, 0, nil, fmt.Errorf("El número de agencia debe estar entre 0 y %d", BYTE_SIZE)
	}

	// Escribir el byte de agencia
	if err := buffer.WriteByte(byte(agencia)); err != nil {
		return nil, 0, nil, fmt.Errorf("error al escribir agencia: %w", err)
	}

	// Posición para escribir el batchSize (se actualizará luego)
	batchPos := buffer.Len()
	if err := buffer.WriteByte(0); err != nil {
		return nil, 0, nil, fmt.Errorf("error al escribir batch size: %w", err)
	}

	validBets := 0
	var remainingBets []Bet

	// Limitar a BYTE_SIZE apuestas
	if len(bets) > BYTE_SIZE {
		log.Warningf("BatchSize (%d) excede el límite de 1 byte. Se procesarán solo %d apuestas.", len(bets), BYTE_SIZE)
		remainingBets = bets[BYTE_SIZE:] // Las apuestas restantes
		bets = bets[:BYTE_SIZE]          // Solo procesamos hasta el límite
	}

	// Función auxiliar para escribir los campos con su longitud
	writeField := func(data string) bool {
		fieldSize := len(data) + 1 // 1 byte para la longitud del campo
		if buffer.Len()+fieldSize > MAX_BUFFER_SIZE {
			return false // No hay espacio suficiente
		}

		if err := buffer.WriteByte(byte(len(data))); err != nil {
			return false // Error al escribir la longitud
		}
		buffer.Write([]byte(data)) // Escribir contenido
		return true
	}

	// Serializar apuestas
	for i, bet := range bets {
		startSize := buffer.Len() // Guardamos el tamaño antes de escribir

		if len(bet.Nombre) > BYTE_SIZE || len(bet.Apellido) > BYTE_SIZE ||
			len(bet.DNI) > BYTE_SIZE || len(bet.Nacimiento) > BYTE_SIZE || len(bet.Numero) > BYTE_SIZE {
			fmt.Printf("Error: Un campo en esta apuesta excede los %d bytes, se omite.\n", BYTE_SIZE)
			continue
		}

		// Intentamos escribir los campos
		if !writeField(bet.Nombre) || !writeField(bet.Apellido) || !writeField(bet.DNI) ||
			!writeField(bet.Nacimiento) || !writeField(bet.Numero) {
			// Si no cabe en el buffer, revertimos esta apuesta y cortamos el loop
			buffer.Truncate(startSize)
			log.Warningf("El batchSize (%d) excede los 8KB, ajustando a %d apuestas.", len(bets), validBets)
			remainingBets = append(remainingBets, bets[i:]...) // Agregar las no enviadas
			break
		}

		validBets++ // Incrementamos solo si la apuesta completa se añadió correctamente
	}

	// Modificar el batchSize en la posición reservada
	data := buffer.Bytes()
	data[batchPos] = byte(validBets)

	return data, validBets, remainingBets, nil
}

func (p *ProtocolClient) send_bets(bets []Bet, agencia int) (int, []Bet) {
	data, cantBets, remainingBets, err := p.serialize(bets, agencia)
	if err != nil {
		fmt.Println("Error al serializar los datos:", err)
		return 0, nil
	}

	if err := shortWrite(p.conn, data); err != nil {
		fmt.Println("Error al enviar los datos:", err)
		return 0, nil
	}

	response, err := readExact(p.conn, 1)
	if err != nil {
		fmt.Println("Error al recibir la respuesta:", err)
		return 0, nil
	}

	if response[0] == STATUS_SUCCESS {
		return cantBets, remainingBets
	} else {
		return 0, nil
	}
}

func (p *ProtocolClient) notify_end_of_bets(agencia int) error {
	var buffer bytes.Buffer
	buffer.WriteByte(byte(agencia))
	buffer.WriteByte(0)

	if err := shortWrite(p.conn, buffer.Bytes()); err != nil {
		return fmt.Errorf("error al enviar notificación de fin: %w", err)
	}

	response, err := readExact(p.conn, 1)
	if err != nil {
		return fmt.Errorf("error al recibir confirmación de fin: %w", err)
	}

	if response[0] == STATUS_SUCCESS {
		return nil
	}
	return fmt.Errorf("el servidor rechazó la notificación")
}

func (p *ProtocolClient) read_winners(agencia int) ([]string, error) {
	winners := []string{}
	countBuffer, err := readExact(p.conn, 1)
	if err != nil {
		return nil, fmt.Errorf("error al recibir la cantidad de ganadores: %w", err)
	}
	count := int(countBuffer[0])

	for i := 0; i < count; i++ {
		lengthBuffer, err := readExact(p.conn, 1)
		if err != nil {
			return nil, fmt.Errorf("error al recibir la longitud del DNI: %w", err)
		}
		dniLength := int(lengthBuffer[0])

		dniBuffer, err := readExact(p.conn, dniLength)
		if err != nil {
			return nil, fmt.Errorf("error al recibir el DNI: %w", err)
		}
		winners = append(winners, string(dniBuffer))
	}
	return winners, nil
}