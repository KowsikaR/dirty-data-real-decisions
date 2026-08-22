| check                       |   count | interpretation                       |
|:----------------------------|--------:|:-------------------------------------|
| Rows loaded                 |   15003 | all source rows                      |
| Columns loaded              |       4 | source schema                        |
| Exact duplicate rows        |       3 | excluded from analysis               |
| Repeated case IDs           |       0 | representative retained              |
| Missing values              |      15 | retained where possible; not imputed |
| Date parse failures         |       5 | no duration calculated               |
| Impossible intervals        |       5 | no duration calculated               |
| Rows used for case analysis |   15000 | deduplicated, identified cases       |
| Valid duration records      |   14985 | used for duration metrics            |