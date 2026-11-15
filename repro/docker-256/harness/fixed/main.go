// Extracted model of moby/moby#256 at the fixing revision.
//
// Source: archive.go, func CmdStream(cmd *exec.Cmd) (io.Reader, error), after
// 58befe3081726ef74ea09198cd9488fb42c51f51 ("Fix a deadlock in CmdStream").
// The only semantic difference from ../buggy is that stderr is drained by a
// second goroutine and the stdout goroutine waits for it before cmd.Wait().
//
// See patches/upstream-fix.diff and ../notes.md.
package main

import (
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
)

// CmdStream is the post-fix body: stderr is drained concurrently.
func CmdStream(cmd *exec.Cmd) (io.Reader, error) {
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		return nil, err
	}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	errChan := make(chan []byte)
	go func() {
		errText, err := ioutil.ReadAll(stderr)
		if err != nil {
			errText = []byte("(...couldn't fetch stderr: " + err.Error() + ")")
		}
		errChan <- errText
	}()
	pipeR, pipeW := io.Pipe()
	go func() {
		_, err := io.Copy(pipeW, stdout)
		if err != nil {
			pipeW.CloseWithError(err)
		}
		errText := <-errChan
		if err := cmd.Wait(); err != nil {
			// FIXME: we are deliberately not closing the pipe in the error case
			pipeW.CloseWithError(errors.New(err.Error() + ": " + string(errText)))
		} else {
			pipeW.Close()
		}
	}()
	return pipeR, nil
}

func main() {
	fmt.Println("repro: docker-256: starting /bin/sh -c 'dd if=/dev/zero bs=1k count=1000 of=/dev/stderr; echo hello'")
	cmd := exec.Command("/bin/sh", "-c", "dd if=/dev/zero bs=1k count=1000 of=/dev/stderr; echo hello")
	out, err := CmdStream(cmd)
	if err != nil {
		fmt.Fprintf(os.Stderr, "repro: docker-256: CmdStream failed: %v\n", err)
		os.Exit(1)
	}
	if _, err := io.Copy(io.Discard, out); err != nil {
		fmt.Fprintf(os.Stderr, "repro: docker-256: reading the output pipe failed: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("ORACLE: docker-256: command completed and stdout was read to EOF")
}
