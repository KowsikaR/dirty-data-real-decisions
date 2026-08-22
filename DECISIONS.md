# Analytical decisions

These rules are part of the audit trail, not hidden implementation details.

## Duplicate handling

Text is trimmed and case-folded before duplicate identity is assessed. Exact duplicate rows are collapsed. Repeated `case_id` values are treated as one case for operational summaries: the first row in source order is the representative, while every removed row and its reason is logged. This avoids double-counting but does not pretend conflicting records are reconciled.

## Missing values

Missing `case_id` rows are excluded from case-level analysis because identity cannot be established. Missing intake dates cannot be assigned to a year. Missing closure dates cannot produce a duration. Missing categories are labeled `Unknown` rather than imputed from an unrelated row. No duration is imputed.

## Date cleaning

Whitespace is removed and dates are parsed with explicit format attempts followed by conservative `pandas.to_datetime` fallbacks. ISO-like values are parsed first. For slash-separated values, an obviously month-first value (second component greater than 12) is parsed month-first; other slash values use day-first. This makes the ambiguity policy visible rather than silently varying by machine locale. The original values remain available in the raw input and all transformed rows are logged. A date is valid only when both dates are parseable and the closure is on or after intake.

## Invalid records

Rows with an impossible interval (`closure_date < intake_date`) are excluded from duration analysis and logged. They are not “fixed” by swapping dates, because that would invent an event history. Rows with missing dates remain in the cleaned file with null derived fields so their loss from a particular metric is visible.

## Category normalization

Categories are converted to strings, trimmed, case-folded, and whitespace-collapsed. Known spelling variants are mapped to a small controlled vocabulary (`Billing`, `Technical`, `Account`, `Complaint`, `Request`, `Other`). Unknown non-empty values are title-cased and retained as `Other` only when they are not stable enough to interpret. Blank values become `Unknown`. The raw category is retained as `category_raw`.

## Causation

The observed dataset contains identifiers, dates, and categories but no staffing, queue, priority, backlog, policy, or process-change fields. Therefore Question 3 cannot be answered reliably. Descriptive associations are not presented as causes.
