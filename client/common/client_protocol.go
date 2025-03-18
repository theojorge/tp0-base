package common

import (
	"bytes"
	"fmt"
	"net"
	"strconv"
)

// Definir constantes para los identificadores de los campos
const (
	STATUS_SUCCESS = 0x01
	STATUS_ERROR   = 0x00
)

type Bet struct {
	Agencia    string
	Nombre     string
	Apellido   string
	DNI        string
	Nacimiento string
	Numero     string
}

type ProtocolClient struct {
	conn net.Conn
}

// Serializa los datos de Bet en el formato: [Agencia][Longitud][Campo 1][Longitud][Campo 2]... [Longitud][Campo n]
func (p *ProtocolClient) serialize(bet Bet) ([]byte, error) {
	var buffer bytes.Buffer

	// Convertir agencia a entero y asegurarse de que esté en el rango de 0-255
	agencia, err := strconv.Atoi(bet.Agencia)
	if err != nil {
		fmt.Println("Error al convertir Agencia a int:", err)
		return nil, err
	}
	if agencia < 0 || agencia > 255 {
		return nil, fmt.Errorf("El número de agencia debe estar entre 0 y 255")
	}

	// Escribir 1 byte con la agencia
	if err := buffer.WriteByte(byte(agencia)); err != nil {
		return nil, err
	}

	// Función auxiliar para escribir los campos con su longitud (1 byte) y su valor
	writeField := func(data string) error {
		// Escribir la longitud del campo (1 byte)
		if len(data) > 255 {
			return fmt.Errorf("El campo excede el límite de 255 bytes")
		}
		if err := buffer.WriteByte(byte(len(data))); err != nil {
			return err
		}
		// Escribir el valor del campo
		_, err := buffer.Write([]byte(data))
		return err
	}

	// Serializar cada campo con su longitud y valor
	if err := writeField(bet.Nombre); err != nil {
		return nil, err
	}
	if err := writeField(bet.Apellido); err != nil {
		return nil, err
	}
	if err := writeField(bet.DNI); err != nil {
		return nil, err
	}
	if err := writeField(bet.Nacimiento); err != nil {
		return nil, err
	}
	if err := writeField(bet.Numero); err != nil {
		return nil, err
	}

	return buffer.Bytes(), nil
}


func (p *ProtocolClient) send_bet(bet Bet) {
	// Serializar los datos antes de enviarlos
	data, err := p.serialize(bet)
	if err != nil {
		fmt.Println("Error al serializar los datos:", err)
		return
	}

	// Enviar los datos al servidor
	_, err = p.conn.Write(data)
	if err != nil {
		fmt.Println("Error al enviar los datos:", err)
		return
	}

	// Recibir solo 1 byte de respuesta del servidor
	buffer := make([]byte, 1)
	n, err := p.conn.Read(buffer)
	if err != nil {
		fmt.Println("Error al recibir la respuesta:", err)
		return
	}

	// Verificar que realmente se haya leído 1 byte
	if n != 1 {
		fmt.Println("Error: No se recibió el byte esperado")
		return
	}

	// Interpretar la respuesta del servidor
	if buffer[0] == STATUS_SUCCESS {
		log.Infof("action: apuesta_enviada | result: success | dni: %s | numero: %s\n", bet.DNI, bet.Numero)
	} else if buffer[0] == STATUS_ERROR {
		log.Infof("action: apuesta_enviada | result: error")
	} else {
		fmt.Printf("Respuesta desconocida del servidor: %x\n", buffer[0])
	}
}
