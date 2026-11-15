// Extracted model of moby/moby#256 at the pre-fix revision.
//
// Source: archive.go, func CmdStream(cmd *exec.Cmd) (io.Reader, error),
// checked out at 1d6929c8bc6cbc5ad63dce083869460b6bb377ad (parent of the
// fixing commit 58befe3081726ef74ea09198cd9488fb42c51f51).
//
// The pre-fix helper reads stdout to EOF before reading stderr, so a child
// that fills its stderr pipe deadlocks the three-way handshake. The fixing
// commit drains stderr concurrently; see patches/upstream-fix.diff.
//
// Only the Docker binary built around CmdStream is substituted with a small
// main; the function body is kept as close to upstream as this package needs.
// See ../notes.md.
package main

import (
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"os/exec"
)

// CmdStream is copied from the pre-fix archive.go. Do not "fix" this file;
// the fixed variant lives in ../fixed.
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
	pipeR, pipeW := io.Pipe()
	go func() {
		_, err := io.Copy(pipeW, stdout)
		if err != nil {
			pipeW.CloseWithError(err)
		}
		errText, e := ioutil.ReadAll(stderr)
		if e != nil {
			errText = []byte("(...couldn't fetch stderr: " + e.Error() + ")")
		}
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
