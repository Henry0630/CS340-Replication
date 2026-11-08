# Deviations from Paper Setup

| Item | Paper Setup | Our Setup | Reason |
|---|---|---|---|
| Go Version | Older version used in the paper | Go 1.22.4 | Unified reproduction environment, easily accessible |
| Reproduction Scale | Authors re-ran 41 bugs | Plan to reconstruct 15-20 bugs | Limited manpower and time; counting metrics are insensitive to scale |
| Hardware | Not specified in detail | Local host machine / Docker | Counting metrics are insensitive to hardware; will discuss in Limitations |
| Dataset Missing | 3 BoltDB blocking patches | Only 1 available in the official dataset | Upstream did not release those patches (see paper §5.3) |