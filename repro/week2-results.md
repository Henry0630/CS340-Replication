# Week-two extracted-model results

Owner: Haotong Xie (1230022122), role C.

The [Linux CI run](https://github.com/Henry0630/CS340-Replication/actions/runs/43679686655)
completed all three jobs using the repository's pinned `cs340-repro:go1.22`
Dockerfile (Go 1.22.4). Each job uploaded its raw `results/raw/<bug>/` logs,
including per-trial JSONL, stdout, stderr, stacks, and build logs, as a
separate workflow artifact. The image was built from the base digest recorded
in [`docs/environment.md`](../docs/environment.md).

| Model | Buggy symptom trials | Detector trial | Fixed controls | Observed buggy status |
|---|---:|---:|---:|---|
| `grpc-793` | 3/3 | 1/1, no runtime deadlock report | 3/3 completed | timeout after 10 s |
| `docker-256` | 3/3 | 1/1, no runtime deadlock report | 3/3 completed | timeout after 10 s |
| `grpc-1424` | 3/3 | 1/1, runtime deadlock report | 3/3 completed | `deadlock_reported` |

Every trial used the same input for its buggy and fixed variant. The fixed
controls returned the expected oracle marker. The runners return 0 for observed
symptoms, 1 when a requested buggy symptom is absent, and 2 for build, setup,
argument, or oracle failures. Each JSONL row includes the week-two fields
`bug`, `run`, `verdict`, and `wall_s`, plus provenance and environment data.

These are `extracted_model` runs that preserve the relevant upstream
synchronization but replace surrounding application dependencies. In
`grpc-1424`, the harness blocks its last goroutine to observe a missing
notification, which can make the runtime report a global deadlock even though
the original application symptom is a goroutine leak. The detector observations
above therefore do **not** estimate the paper's Table 8 coverage for complete
applications. The paper's 2/21 blocking and 10/20 race results remain paper
figures, not measurements by this team. The workbook's 19/23 reproduced flags
are upstream annotations, not our run counts.
