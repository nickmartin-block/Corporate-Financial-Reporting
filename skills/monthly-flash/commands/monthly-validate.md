---
name: monthly-validate
description: Validate the published Block Monthly Topline Flash Google Doc against the populated brand reporting model ranges (L400:S427 + L432:R468). Compares every metric value-by-value. Run after /monthly-flash completes or independently to re-check after manual edits.
allowed-tools:
  - Bash(cd ~/skills/gdrive && uv run gdrive-cli.py:*)
  - Bash(sq agent-tools google-drive:*)
  - Read
  - Write
metadata:
  author: nmart
  version: "2.0"
  status: active
---

# Monthly Flash — Data Validation

Your job: confirm every number in the published Doc matches the populated data layer. Flag every mismatch. Do not write to the Doc. Do not fix errors.

**Dependencies:** Load `~/Corporate-Financial-Reporting/skills/monthly-flash/skills/financial-reporting.md` for formatting standards and rounding rules.

---

## Configuration

| Parameter | Value |
|---|---|
| Data workbook | `15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0` |
| Data tab | `MRP Charts & Tables` |
| Flash table range | `L400:S427` |
| Standardized P&L range | `L432:R468` |
| Target Doc | `1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA` (Block April-26 Flash Update) |
| Target Tab | `Claude` (tabId `t.6lmbmhs5p561`) |
| Validation Path | `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md` |

---

## Step 1 — Auth

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py auth status
```

Stop if not valid.

---

## Step 2 — Read both sources in parallel

**Sheet (source of truth):**

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L400:S427"
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L432:R468"
```

**Doc text (what we're validating):**

Find the `claude` tab by name and read its content.

---

## Step 3 — Build ground truth from the sheet

### Flash table column mapping (L400:S427)

| Index (col offset) | Content |
|---|---|
| 0 | Row label |
| 1 | Actual |
| 2 | vs. OL $ |
| 3 | vs. OL % |
| 4 | vs. AP $ |
| 5 | vs. AP % |
| 6 | YoY % |
| 7 | Prior-month YoY % |

### Flash table row mapping (0-indexed from values array, which starts at row 400)

| Row offset | Metric | Doc Label |
|---|---|---|
| 2 | Cash App Actives | Cash App Actives |
| 3 | Cash App Inflows per Active | Cash App Inflows per Active |
| 4 | Commerce GMV | Commerce GMV |
| 5 | Square GPV | Global GPV |
| 6 | Square US GPV | US GPV |
| 7 | Square INTL GPV | INTL GPV |
| 10 | Block GP | Block gross profit |
| 11 | Cash App GP | Cash App gross profit |
| 17 | Square GP | Square gross profit |
| 23 | TIDAL GP | TIDAL gross profit |
| 24 | Proto GP | Proto gross profit |
| 25 | Adjusted Opex | Adjusted Opex |
| 26 | Adjusted OI | Adjusted Operating Income |
| 27 | Rule of 40 | Rule of 40 |

**Cash App sub-products (vs AP $ for outperformance line):**

| Row | Metric |
|---|---|
| 12 | Commerce GP |
| 13 | Borrow GP |
| 14 | Cash App Card GP |
| 15 | Instant Deposit GP |
| 16 | Post-Purchase BNPL GP |

**Square sub-products (vs AP $ for outperformance line):**

| Row | Metric |
|---|---|
| 18 | US Payments GP |
| 19 | INTL Payments GP |
| 20 | Banking GP |
| 21 | SaaS GP |
| 22 | Hardware GP |

### Standardized P&L column mapping (L432:R468)

| Index | Content |
|---|---|
| 0 | Row label |
| 1 | Actual |
| 2 | vs. OL $ |
| 3 | vs. OL % |
| 4 | vs. AP $ |
| 5 | vs. AP % |
| 6 | YoY % |

### V/A/F bucket totals (row offset from row 432)

| Row offset | Metric | Doc Label |
|---|---|---|
| 10 | Total Variable Operational Costs | Variable costs |
| 18 | Total Acquisition Costs | Acquisition costs |
| 35 | Total Fixed Costs | Fixed costs |
| 36 | Total Block GAAP OpEx | (cross-check vs Adjusted Opex headline; should ≈ Adj OpEx + restructuring + amort intangibles) |

For each metric row, extract values from the appropriate columns. Skip cells containing `#REF!`, `#DIV/0!`, `n/a`, `nm`, or empty values.

---

## Step 4 — Compare every value

For each metric in ground truth, find its label in the doc text and verify each value.

### What to check per metric

| Value Type | Where it appears in the doc |
|---|---|
| Actual | Dollar amount / count / percentage immediately after the metric label |
| vs OL $ | Dollar amount near "vs. Q2OL" (or QnOL for the quarter) |
| vs OL % | Percentage near "vs. Q2OL" |
| vs AP $ | Dollar amount near "vs. AP" |
| vs AP % | Percentage near "vs. AP" |
| YoY % | Percentage immediately before "YoY" |
| Prior-month YoY % | Percentage in parentheses near "in [Prior Month]" |
| Rule of 40 deltas | "+X.X pts" with sign, near "vs. AP" / "YoY" |

### Also check

- **Sub-product deltas:** Cash App outperformance line lists sub-products with AP $ deltas. Square outperformance line same. Verify each delta.
- **Brand bridge:** Block GP headline includes contributions from Cash App, Square, and Other Brands. Verify each. Other Brands = TIDAL vs AP $ + Proto vs AP $.
- **V/A/F driver bullets:** the bucket totals + vs OL deltas in the doc must match Stnd P&L totals. Per-line driver call-outs need not be exhaustively validated, but the bucket-level numbers must.

### Normalization rules

Strip both doc and sheet values to raw numbers before comparing:

- **Dollars:** Strip `$`, `M`, `B`, `K`, commas. Convert $B to $M (×1000). Parentheses → negative.
- **Percentages:** Strip `%`, `+`, `-`. Parentheses → negative.
- **Points:** Strip `pts`, `+`, `-`.
- **Actives:** Strip `M`.
- **Special values:** `n/a`, `nm`, `--`, empty → treat as equivalent (skip comparison).

### Rounding tolerance

| Display format | Tolerance |
|---|---|
| Percentages (no decimal) | ±0.5 pp |
| Percentages (1 decimal) | ±0.05 pp |
| Dollar values in $B (2 decimals) | ±$5M |
| Dollar values in $M (no decimal) | ±$0.5M |
| Dollar values in $M (1 decimal) | ±$0.05M |
| Points (no decimal) | ±0.5 pts |
| Points (1 decimal) | ±0.05 pts |

**PASS** if within tolerance. **FAIL** if outside tolerance or expected value not found in doc.

### Special cases

- **Rule of 40:** Actual is a percentage; deltas are in pts, not dollars or percentages
- **Actives:** Actual is in M; delta is in M (not dollars)
- **Proto/Hardware:** May have negative actuals — verify sign matches
- **"nm" YoY:** Skip the YoY comparison for that metric (variance > 1000%)

---

## Step 5 — Tally results

Count:
- Total values compared
- Values passed
- Values failed

---

## Step 6 — Output report

Save to `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md`:

```
# Monthly Flash Validation — [Month] [Year]

## Result: PASS / FAIL

- Metrics validated: [N]
- Values compared: [N]
- ✅ Passed: [N]
- ❌ Failed: [N]

## Failures

[List every failure: ❌ | [Metric] | [Value Type] | Doc: [value] | Sheet: [value]]

(If zero failures: "No mismatches found.")
```

---

## Step 7 — Report back

Tell Nick:
- **PASS** (zero failures) or **FAIL** ([N] failures)
- Total values compared
- Any failures with details
- If PASS → "Data is clean."
