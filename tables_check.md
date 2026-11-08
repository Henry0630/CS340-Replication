# Paper vs Ours: Cell-by-Cell Verification (Table 5/6/7/9/10)

> Note: This document records the comparison between the paper's reported data and our recomputed data. √ indicates consistent, △ indicates discrepancy.

## Table 5: Overall classification

| Category | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| blocking | 85 | 83 | △ | Missing 2 BoltDB patches (see deviations) |
| non-blocking | 86 | 86 | √ | — |
| message passing | 66 | 65 | △ | Double-labeled kubernetes#11298 offset issue (see claim C2) |
| shared memory | 105 | 105 | √ | Two errors cancel each other out |

*(Note: Templates for Table 6, 7, 9, 10 will be added following this format)*