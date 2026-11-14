// Smoke test compiled inside the experiment image.
// It exists to prove, at build time, that the image can do what the reproducers
// need: cgo, the race detector, goroutines and a channel. If `docker build`
// passes, the toolchain is usable; if it fails, the image is broken and no
// experiment result should be trusted.
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	out := make(chan int, 2)
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			out <- n
		}(i)
	}
	wg.Wait()
	close(out)
	sum := 0
	for v := range out {
		sum += v
	}
	if sum != 1 {
		panic(fmt.Sprintf("unexpected channel sum %d", sum))
	}
	fmt.Println("smoke ok", sum)
}
