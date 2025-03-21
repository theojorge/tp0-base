package common

import (
	"net"
    "fmt"
	"time"
	"github.com/op/go-logging"
     "strconv"
)

var log = logging.MustGetLogger("log")


// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
    BatchSize     int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
    stopCh chan struct{}
    protocol ProtocolClient
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
        stopCh: make(chan struct{}),
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() bool {
	conn, err := net.DialTimeout("tcp", c.config.ServerAddress, 5*time.Second)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
        return false 
	}
	c.conn = conn
	c.protocol = ProtocolClient{conn: c.conn,}
	return true
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {

	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
    agencyID, err := strconv.Atoi(c.config.ID)
	if err != nil {
		log.Errorf("Error al convertir ID de agencia a int: %v", err)
		return
	}

    betsReader, err := NewBetsReader(fmt.Sprintf("/agency-%d.csv", agencyID))
    if err != nil {
        log.Errorf("Error al abrir archivo de apuestas: %v", err)
        return
    }
    defer betsReader.Close()

    adjustedBatchSize := c.config.BatchSize
    var remainingBets []Bet

	for {
        adjustedBatchSize = c.config.BatchSize - len(remainingBets)

        newBets, err := betsReader.GetBatch(adjustedBatchSize)
        if err != nil {
            log.Errorf("Error al obtener batch de apuestas: %v", err)
            return
        }

        //log.Infof("Nuevas apuestas obtenidas: %d", len(newBets))
        bets := append(remainingBets, newBets...)
        //log.Infof("Total de apuestas después de combinar: %d", len(bets))

        // Create the connection the server in every loop iteration. 
        if !c.createClientSocket() {
          return  
        }

        if len(bets) == 0 {
            c.protocol.notify_end_of_bets(agencyID)
            // Leer los ganadores después de notificar el fin de apuestas
            winners, err := c.protocol.read_winners(agencyID)
            if err != nil {
                log.Errorf("Error al leer ganadores: %v", err)
                return
            }
            log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winners))
            // Manejar la lista de ganadores según sea necesario
            if len(winners) > 0 {
                fmt.Println("Ganadores recibidos:", winners)
            }

            break
        }

	    // Sends the bet to the server and if it sends less than the batch it updates to not lose more bets.
	    c.config.BatchSize, remainingBets = c.protocol.send_bets(bets, agencyID)
        //log.Infof("Apuestas restantes después de enviar: %d", len(remainingBets))
      
        if c.sleepWithStopCheck(c.config.LoopPeriod) {
            return
        }
        

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func (c *Client) sleepWithStopCheck(duration time.Duration) bool {
    select {
    case <-c.stopCh:
        log.Infof("action: client_stopped | result: success | client_id: %v", c.config.ID)
        if c.conn != nil {
         log.Infof("action: close_socket | result: in_progress | client_id: %v", c.config.ID)
         c.conn.Close() 
		 log.Infof("action: close_socket | result: success | client_id: %v", c.config.ID)
         c.conn = nil
        }
        return true
    case <-time.After(duration):
        return false
    }
}


func (c *Client) Stop() {
    close(c.stopCh)
}
