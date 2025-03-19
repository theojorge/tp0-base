package common

import (
	"encoding/csv"
	"os"
)

// Estructura para representar una apuesta
type Bet struct {
	Nombre     string
	Apellido   string
	DNI        string
	Nacimiento string
	Numero     string
}

// Estructura para manejar la lectura del archivo CSV en batches
type BetsReader struct {
	file     *os.File
	reader   *csv.Reader
	position int // Puntero a la posición actual en el archivo
}

// Crea una nueva instancia de BetsReader y abre el archivo CSV
func NewBetsReader(filename string) (*BetsReader, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}

	reader := csv.NewReader(file)

	return &BetsReader{
		file:     file,
		reader:   reader,
		position: 0,
	}, nil
}

// Lee un batch de apuestas desde el archivo
func (a *BetsReader) GetBatch(batchSize int) ([]Bet, error) {
	var bets []Bet
	for i := 0; i < batchSize; i++ {
		record, err := a.reader.Read()
		if err != nil {
			// Si llegamos al final del archivo, retornamos lo que hemos leído hasta ahora
			if err.Error() == "EOF" {
				return bets, nil
			}
			return nil, err
		}

		// Crear una apuesta a partir de la línea leída
		bet := Bet{
			Nombre:     record[0],
			Apellido:   record[1],
			DNI:        record[2],
			Nacimiento: record[3],
			Numero:     record[4],
		}
		bets = append(bets, bet)
	}

	return bets, nil
}

// Cierra el archivo al terminar
func (a *BetsReader) Close() error {
	return a.file.Close()
}
