// Application-level workload for grpc/grpc-go#793.
//
// Builds against the complete upstream grpc-go tree at the pinned revision
// (pre-fix 7c6103d142da5fd11a36964c3a42cf698056b00b for the buggy variant,
// fixing commit 5a547ed72c09faf4050739d54caea1d51f4d276d for the control).
//
// The workload creates a real server and calls GracefulStop twice. The pre-fix
// server self-deadlocks on the second call inside (*Server).GracefulStop; the
// fixed server returns and the oracle line is printed.
package main

import (
	"fmt"

	"google.golang.org/grpc"
)

func main() {
	fmt.Println("WORKLOAD: initialising grpc server")
	s := grpc.NewServer()
	fmt.Println("WORKLOAD: first GracefulStop")
	s.GracefulStop()
	fmt.Println("WORKLOAD: first GracefulStop returned")
	fmt.Println("WORKLOAD: second GracefulStop")
	s.GracefulStop()
	fmt.Println("ORACLE: grpc-793 fixed: second GracefulStop returned")
}
