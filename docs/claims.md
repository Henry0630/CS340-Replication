# Claims

The contract between the numbers and the report. Every claim states what the
paper claims, what we measured, and where a deviation is explained. Nobody
quotes a number that is not in this file.

Paper: Tu, Liu, Song, Zhang. *Understanding Real-World Concurrency Bugs in Go.*
ASPLOS'19. <https://songlh.github.io/paper/go-study.pdf>

## C1 — Go concurrency bugs are pervasive, and they need a taxonomy

**Paper.** The first empirical study of Go concurrency bugs. 171 bugs in six
production-grade Go programs (Docker, Kubernetes, gRPC, CockroachDB, etcd,
BoltDB), labelled along two independent dimensions: *cause* (shared-memory
access vs. message passing) and *behaviour* (blocking vs. non-blocking).

**Ours (L1).** Re-parse the pinned upstream snapshot
(`bug_table.xlsx`, commit `f2655063a2278cff64a51121b73801eda05fdcfa`) and
recompute Tables 5, 6, 7, 9, 10.

| | blocking | non-blocking | shared memory | message passing |
|---|---|---|---|---|
| Paper | 85 | 86 | 105 | 66 |
| Ours | 83 | 86 | 105 | 65 |
| Delta | −2 | 0 | 0 | −1 |

**Deviation.** Two BoltDB *blocking* bugs are absent from the released
snapshot; the −1 in the message-passing column is one of them (a BoltDB bug
whose cause was labelled message passing). Not a counting bug on our side —
the upstream data is incomplete. See `docs/deviations.md` (A).

**Status.** L1 done (A). Reproduced except the two missing upstream rows.

## C2 — Most Go concurrency bugs are caused by non-traditional, Go-specific problems

**Paper.** More than half of the 171 bugs are *not* classic shared-memory
races but problems specific to Go's own concurrency idioms (misuse of Go
libraries, goroutine/channel misuse, and similar). The paper therefore answers
the long-running "message passing vs. shared memory" debate for Go: message
passing is *not* automatically safer, because Go-specific idioms fail in
their own ways.

**Ours (L1).** The cause split re-derives exactly: 105 shared-memory and
65 message-passing bugs, i.e. the same 61 % non-traditional share. The
taxonomy method itself is re-implemented from the paper's definitions, not
copied from the paper's spreadsheet.

**Status.** L1 done (A). The taxonomy implementation is the deliverable; the
claim is re-derived from it.

## C3 — Existing fixes are often shallow, and some fixes introduce new bugs

**Paper.** The paper studies how the bugs were fixed: many fixes add
synchronisation without identifying the root cause, some fixes are
incomplete, and a non-trivial number of the fixes themselves introduce new
bugs.

**Ours (L2).** For every bug we rebuild and re-trigger, we compare the
upstream fix commit against our own reproduction and classify the fix.

**Status.** L2 — to be measured (C, weeks 2+). Do not state a number until
`repro/` has the logs.

## C4 — Go's built-in detectors miss most of these bugs

**Paper.** The paper evaluates Go's built-in deadlock detector and race
detector against the 41 bugs it re-ran, and finds that neither catches the
majority of them (paper Tables 8 and 12, sections 5.3 and 6.3).

**Ours (L2).** Same protocol: rebuild each selected bug at its buggy
commit, trigger it, and record whether the built-in detectors fire. The
protocol requires at least 3 runs per bug for statistics and 100 runs for
the race-detector experiment (paper Table 12 protocol).

**Status.** L2 — to be measured (C, weeks 2+). C's run logs are the only
accepted source.

## Extension — does Go 1.22 close the "anonymous function" bug class?

**Paper.** One of the nine observations is that the classic
"closure over a loop variable" bug class is specific to pre-1.22 Go, where
loop variables were shared across iterations.

**Ours.** The only factor we change is the Go language version: the same
image, `golang:1.21.13-bookworm` vs `golang:1.22.4-bookworm`. Go 1.22 gave
each loop iteration its own variables, which should remove this class.

**Status.** Planned (B builds the images, C runs the comparison, week 2+).

## Rule

A number may only appear in the report if it appears in this file or in
`docs/claims.md`'s sibling `docs/deviations.md`, with a pointer to where it
was produced (`results/tables/*.csv` for L1, `repro/*/logs` for L2).
