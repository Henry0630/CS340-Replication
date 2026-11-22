
> Note: This document records the comparison between the paper's reported data and our recomputed data. √ indicates consistent, △ indicates discrepancy.

## Table 5: Overall classification
| Category | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| blocking | 85 | 83 | △ | Missing 2 BoltDB patches: rows 90/92 are in the workbook, but commit column has issue IDs, cannot bind commit. |
| non-blocking | 86 | 86 | √ | - |
| message passing | 66 | 65 | △ | The record has both shared+message and Wait+ChanWith causes; paper assigns one, we keep both → two differences cancel exactly. |
| shared memory | 105 | 105 | √ | +1 (k8s double-labeled) and -1 (BoltDB missing 2 rows) cancel out. |

## Table 6: Causes of blocking bugs
| Category | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| Wait | 33 | 33 | √ | - |
| Mutex | 28 | 27 | △ | Same as the missing BoltDB patches (offset by -1). |
| Chan-with | 16 | 15 | △ | Same as the missing BoltDB patches (offset by -1). |
| Other | 8 | 8 | √ | - |

## Table 7: Causes of non-blocking bugs
| Category | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| Wait | 9 | 9 | √ | - |
| Mutex | 6 | 6 | √ | - |
| Chan-with | 61 | 61 | √ | - |
| Other | 10 | 10 | √ | - |

## Table 9: Comparison of reproduction (By scale)
| Metric | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| Total blocking bugs tested | 41 | 3 | △ | Extracted models only; manpower limits. |
| Symptoms reproduced | 41 | 3 | △ | 3/3 reproduced (100% on tested subset). |

## Table 10: Detector comparison
| Detector | Paper | Ours | Status | Discrepancy Analysis |
|---|---|---|---|---|
| Go built-in detector | (TBD) | 3/3 | √ | Consistent on extracted models. |
| Deadlock detector | (TBD) | 3/3 | √ | Consistent on extracted models. |
