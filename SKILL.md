---
name: financial-reporting
description: Global recipe for Block FP&A financial reporting. Governs all reporting agents — formatting standards, metric formats, comparison framework, style rules, and deviation handling. Load this skill first before any financial reporting sub-skill. Use when generating or populating any Block financial report (weekly, monthly, quarterly, board).
allowed-tools: []
metadata:
  author: nmart
  version: "1.0.0"
  status: "beta"
---

# Block FP&A Reporting — Global Recipe

## Role
Populate Block financial reports with facts sourced from governed data.
Report numbers only. Do not explain, interpret, or assign drivers.

---

## Data
- Source: governed Google Sheets master table (rows = metrics, columns = time periods)
- Never estimate or infer a value
- If data is missing: `[DATA MISSING: {metric} | {period}]`

---

## Comparison Point
Always compare to the latest forecast for the quarter in scope:

| Quarter | Comparison Point |
|---------|-----------------|
| Q1      | AP              |
| Q2      | Q2OL            |
| Q3      | Q3OL            |
| Q4      | Q4OL            |

Use `[Forecast]` as a placeholder in the format templates below — substitute the correct label at runtime.

---

## Metric Format

**Pacing / forward-looking:**
```
[Metric] is pacing to [Value] in [Period] ([+/-Delta]% YoY), [+/-Delta]% ([+/-$Delta]) [above/below] [Forecast]
```
→ gross profit is pacing to $1.05B in March (+25% YoY), +1.6% (+$17M) above AP

**Actuals:**
```
[Metric] landed at [Value] ([+/-Delta]% YoY), [+/-Delta]% ([+/-$Delta]) [above/below] [Forecast]
```
→ gross profit landed at $940M (+29% YoY), +5.2% (+$47M) above AP

---

## Style Rules (FP&A Standard)

See [references/fpa-style-guide.md](references/fpa-style-guide.md) for the full style guide. Key rules:

**Numbers**
- Dollars: $M, $B, $K — no space between symbol and number ($17M, $1.05B)
- Units (actives, GPV): M or B — no space (58.5M actives, $23.3B GPV)
- Basis points: space before bps (+5 bps, (5 bps))
- Percentages: no space (25%, +3.0%)

**Rounding**
- Percentages: one decimal if < 10% (e.g., 9.8%), no decimal if ≥ 10% (e.g., 15%)
- Dollars in millions: one decimal if absolute value < $10M (e.g., $4.2M, -$7.8M), no decimal if ≥ $10M (e.g., $45M, -$38M)
- Dollars in billions: always two decimals (e.g., $1.26B)
- Actives: always one decimal (e.g., 58.5M)

**Signs**
- Always include +/- on variances and YoY growth rates, even alongside directional words
- Text negatives: hyphen, e.g., -$38M, -1.6% below AP
- Charts/tables negatives: parentheses, e.g., ($38M), (5.4 bps)

**Time Periods**
- Text: Q1 2026, March 2026
- Charts/tables: Q1'26, Mar'26

**Capitalization**
- "gross profit" and "opex" — lowercase in body text
- Standalone headers: capitalize all major words
- In-line headers (bold label + colon): capitalize first word only

**Comparisons**
- Abbreviate YoY, QoQ, WoW in body copy and always in charts/tables
- "vs." (with period) for versus

---

## Deviations
For any metric with a meaningful deviation from [Forecast], consensus, or prior period:
- Populate the quantitative fact line as normal
- On the next line, insert the text **Nick to fill out** formatted in red (hex #ea4335) in the Google Doc
- Do NOT fill in the reason yourself

---

## Sub-Agent Inheritance
Sub-skills must load this recipe first, then apply their specific deliverable instructions.
These standards may not be overridden.
