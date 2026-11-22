# Deviations from Paper Setup

| Item | Paper Setup | Our Setup | Reason |
|---|---|---|---|
| Go Version | Older version | Go 1.22.4 | Unified environment |
| Reproduction Scale | 41 bugs | 15-20 bugs | Manpower limits |
| Experiment Host | Unspecified | GitHub runner + Win11 | Cross-platform check |
| | Dataset Missing | 2 BoltDB patches | 2 rows in our workbook (blocking rows 90 / 92) | The commit column stores issue IDs instead of hashes, so we cannot bind them to commits. |
- **Note**: Extracted model ≠ Complete application. All L2 results must explicitly state which layer they belong to.
