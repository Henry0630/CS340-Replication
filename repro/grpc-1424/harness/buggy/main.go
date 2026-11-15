// Extracted model of grpc/grpc-go#1424 at the pre-fix revision.
//
// Source: clientconn.go, func (cc *ClientConn) lbWatcher(doneChan chan struct{}),
// checked out at 39c8c3866d926d95e11c03508bf83d00f2963f91 (parent of the fixing
// commit 4e56696c6c5a8cd7b711a1eb8936463559361da5).
//
// The initial-connection waiter is notified through doneChan only when a
// balancer address arrives. If the balancer closes its Notify channel before
// the first address, the range ends without ever closing doneChan, so the
// waiter blocks forever and the dialer goroutine leaks.
//
// See patches/upstream-fix.diff and ../notes.md.
package main

import (
	"fmt"
	"os"
	"sync"
)

type Address struct {
	Addr     string
	Type     string
	Metadata interface{}
}

type addrConn struct {
	cc   *ClientConn
	addr Address
}

func (ac *addrConn) tearDown(err error) {}

type balancer interface {
	Notify() <-chan []Address
	Close() error
}

type dialOptions struct {
	balancer balancer
}

type ClientConn struct {
	mu    sync.Mutex
	conns map[Address]*addrConn
	dopts dialOptions
}

func (cc *ClientConn) resetAddrConn(addr Address, blocking bool) error {
	ac := &addrConn{cc: cc, addr: addr}
	cc.mu.Lock()
	defer cc.mu.Unlock()
	if cc.conns == nil {
		return fmt.Errorf("ClientConn is closed")
	}
	cc.conns[addr] = ac
	return nil
}

// lbWatcher is copied from the pre-fix clientconn.go (local stand-ins for
// Address, addrConn, and the balancer interface). Do not "fix" this file; the
// fixed variant lives in ../fixed.
func (cc *ClientConn) lbWatcher(doneChan chan struct{}) {
	for addrs := range cc.dopts.balancer.Notify() {
		var add []Address
		var del []*addrConn
		cc.mu.Lock()
		for _, a := range addrs {
			if c, ok := cc.conns[a]; ok {
				c.addr = a
			} else {
				add = append(add, a)
			}
		}
		for k, c := range cc.conns {
			var keep bool
			for _, a := range addrs {
				if a == k {
					keep = true
					break
				}
			}
			if !keep {
				del = append(del, c)
				delete(cc.conns, k)
			}
		}
		cc.mu.Unlock()
		for _, a := range add {
			if doneChan != nil {
				err := cc.resetAddrConn(a, true)
				if err == nil {
					close(doneChan)
					doneChan = nil
				}
			} else {
				err := cc.resetAddrConn(a, false)
				if err != nil {
					fmt.Fprintf(os.Stderr, "grpc: error while adding connection: %v\n", err)
				}
			}
		}
		for _, c := range del {
			c.tearDown(fmt.Errorf("draining"))
		}
	}
}

// blockingBalancer returns a Notify channel that never receives an address and
// is closed by Close; it mirrors the resolver that closes before the first
// update.
type blockingBalancer struct {
	mu   sync.Mutex
	ch   chan []Address
	done chan struct{}
}

func newBlockingBalancer() *blockingBalancer {
	return &blockingBalancer{ch: make(chan []Address), done: make(chan struct{})}
}

func (b *blockingBalancer) Notify() <-chan []Address { return b.ch }

func (b *blockingBalancer) Close() error {
	b.mu.Lock()
	defer b.mu.Unlock()
	select {
	case <-b.done:
	default:
		close(b.ch)
		close(b.done)
	}
	return nil
}

func main() {
	b := newBlockingBalancer()
	cc := &ClientConn{
		conns: make(map[Address]*addrConn),
		dopts: dialOptions{balancer: b},
	}
	doneChan := make(chan struct{})
	go cc.lbWatcher(doneChan)
	fmt.Println("repro: grpc-1424: lbWatcher started; closing the balancer before its first address list")
	_ = b.Close()
	fmt.Println("repro: grpc-1424: blocking on the initial-connection notification")
	<-doneChan
	fmt.Println("ORACLE: grpc-1424: initial dial wait unblocked after the balancer closed")
}
