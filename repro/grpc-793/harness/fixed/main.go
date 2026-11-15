// Extracted model of grpc/grpc-go#793 at the fixing revision.
//
// Source: server.go, func (s *Server) GracefulStop(), after
// 5a547ed72c09faf4050739d54caea1d51f4d276d ("Merge pull request #795 from
// tamird/graceful-deadlock"). The only semantic difference from ../buggy is the
// upstream-fix line s.mu.Unlock() in the early-return branch.
//
// Only the surrounding grpc types are substituted with local stand-ins so the
// function can be compiled without the rest of the repository. See ../notes.md.
package main

import (
	"fmt"
	"io"
	"net"
	"sync"
)

// serverTransport stands in for transport.ServerTransport; only Drain is used
// by GracefulStop.
type serverTransport interface {
	Drain()
}

// eventLog stands in for golang.org/x/net/trace.EventLog; always nil here.
type eventLog interface {
	Finish()
}

type server struct {
	mu     sync.Mutex
	lis    map[net.Listener]bool
	conns  map[io.Closer]bool
	drain  bool
	cv     *sync.Cond
	events eventLog
}

func newServer() *server {
	s := &server{
		lis:   make(map[net.Listener]bool),
		conns: make(map[io.Closer]bool),
	}
	s.cv = sync.NewCond(&s.mu)
	return s
}

// GracefulStop is the post-fix body: the early return releases s.mu instead of
// taking it a second time.
func (s *server) GracefulStop() {
	s.mu.Lock()
	if s.drain == true || s.conns == nil {
		s.mu.Unlock()
		return
	}
	s.drain = true
	for lis := range s.lis {
		lis.Close()
	}
	s.lis = nil
	for c := range s.conns {
		c.(serverTransport).Drain()
	}
	for len(s.conns) != 0 {
		s.cv.Wait()
	}
	s.conns = nil
	if s.events != nil {
		s.events.Finish()
		s.events = nil
	}
	s.mu.Unlock()
}

func main() {
	s := newServer()
	fmt.Println("repro: grpc-793: server created with no listeners or connections")
	for i := 1; i <= 3; i++ {
		fmt.Printf("repro: grpc-793: GracefulStop call %d begin\n", i)
		s.GracefulStop()
		fmt.Printf("repro: grpc-793: GracefulStop call %d returned\n", i)
	}
	fmt.Println("ORACLE: grpc-793: repeated GracefulStop returned")
}
