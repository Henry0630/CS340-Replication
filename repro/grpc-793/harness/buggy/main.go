// Extracted model of grpc/grpc-go#793 at the pre-fix revision.
//
// Source: server.go, func (s *Server) GracefulStop(), checked out at
// 7c6103d142da5fd11a36964c3a42cf698056b00b (first parent of the fixing commit
// 5a547ed72c09faf4050739d54caea1d51f4d276d).
//
// The early-return branch takes s.mu a second time (s.mu.Lock()), so the second
// GracefulStop call self-deadlocks. The fixing commit changes it to
// s.mu.Unlock(); see ../../../patches/upstream-fix.diff.
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

// GracefulStop is copied from the pre-fix server.go. Do not "fix" this file;
// the fixed variant lives in ../fixed.
func (s *server) GracefulStop() {
	s.mu.Lock()
	if s.drain == true || s.conns == nil {
		s.mu.Lock()
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
