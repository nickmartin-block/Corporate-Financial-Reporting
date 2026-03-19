---
name: monthly-validate
description: Validate the published Block Monthly Topline Flash Google Doc against the MRP Charts & Tables source sheet. Compares every metric value-by-value. Run after /monthly-flash completes or independently to re-check after manual edits.
allowed-tools:
  - Bash(cd ~/skills/gdrive && uv run gdrive-cli.py:*)
  - Read
  - Write
metadata:
  author: nmart
  version: "1.0"
  status: active
---

# Monthly Flash — Data Validation

Your job: confirm that every number in the published Doc matches the source sheet. Flag every mismatch. Do not write to the Doc. Do not fix errors.

**Dependencies:** Load `~/skills/weekly-reporting/skills/financial-reporting.md` for formatting standards and rounding rules.

---

## Configuration

| Parameter | Value |
|---|---|
| Source Sheet | `15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0` |
| Source Tab | `MRP Charts & Tables` |
| Source Range | `L11:Y90` |
| Target Doc | `1S--3vA6obl4hBF2Nw2jqD1M4sjEkD8FcpC073-OlAUY` |
| Target Tab | `t.mkykw9vq4coc` |
| Validation Path | `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md` |

---

## Step 1 — Auth

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py auth status
```

Stop if not valid.

---

## Step 2 — Read both sources in parallel

**Sheet** (source of truth):

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L11:Y90"
```

**Doc text** (what we're validating):

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py read 1S--3vA6obl4hBF2Nw2jqD1M4sjEkD8FcpC073-OlAUY --tab t.mkykw9vq4coc
```

---

## Step 3 — Build ground truth from the sheet

### Column mapping

| Index | Content |
|---|---|
| 0 | Row label |
| 1 | Actual |
| 4 | vs. AP $ |
| 5 | vs. AP % |
| 6 | YoY % |
| 7 | Jan YoY % |

### Row mapping (0-indexed from values array)

**Main Summary:**

| Row | Metric | Doc Label |
|---|---|---|
| 2 | Cash App Actives | Cash App Actives |
| 3 | Cash App Inflows per Active | Cash App Inflows per Active |
| 4 | Commerce GMV | Commerce GMV |
| 5 | Square GPV | Global GPV |
| 6 | Square US GPV | US GPV |
| 7 | Square INTL GPV | INTL GPV |
| 8 | Square INTL GPV (CC) | INTL GPV (CC reference) |
| 10 | Block GP | Block gross profit |
| 11 | Cash App GP | Cash App gross profit |
| 17 | Square GP | Square gross profit |
| 23 | TIDAL GP | TIDAL gross profit |
| 24 | Proto GP | Proto gross profit |
| 25 | Adjusted Opex | Adjusted Opex |
| 26 | Adjusted OI | Adjusted Operating Income |
| 27 | Rule of 40 | Rule of 40 |

**Cash App sub-products (vs AP $ only, for outperformance line):**

| Row | Metric |
|---|---|
| 12 | Commerce GP |
| 13 | Borrow GP |
| 14 | Cash App Card GP |
| 15 | Instant Deposit GP |
| 16 | Post-Purchase BNPL GP |

**Square sub-products (vs AP $ only, for outperformance line):**

| Row | Metric |
|---|---|
| 18 | US Payments GP |
| 19 | INTL Payments GP |
| 20 | Banking GP |
| 21 | SaaS GP |
| 22 | Hardware GP |

**Cash App ex. Commerce section:**

| Row | Metric | Doc Label |
|---|---|---|
| 32 | Cash App ex. Commerce GP | Cash App ex. Commerce gross profit |
| 35 | Monetization Rate | Cash App Monetization Rate |

**Opex Summary & Breakdown:**

| Row | Metric | Doc Label |
|---|---|---|
| 74 | Variable Profit | Variable Profit |
| 77 | Variable costs | Variable costs |
| 78 | Acquisition costs | Acquisition costs |
| 79 | Fixed costs | Fixed costs |

For each metric row, extract: Actual (index 1), vs AP $ (index 4), vs AP % (index 5), YoY % (index 6), Jan YoY % (index 7). Skip cells containing `#REF!`, `#DIV/0!`, `n/a`, or empty values.

---

## Step 4 — Compare every value

For each metric in the ground truth, find its label in the doc text and verify each value.

### What to check per metric

| Value Type | Where it appears in the doc |
|---|---|
| Actual | Dollar amount or percentage immediately after the metric label |
| vs AP $ | Dollar amount near "vs. AP" or "above/below AP" |
| vs AP % | Percentage near "vs. AP" or "above/below AP" |
| YoY % | Percentage immediately before "YoY" |
| Jan YoY % | Percentage in parentheses near "in January" or "in [Prior Month]" |

### Also check

- **Sub-product deltas:** Cash App outperformance line lists 5 sub-products with AP $ deltas. Square outperformance line lists 5 sub-products. Verify each delta.
- **Brand bridge:** Block GP headline includes contributions from Cash App, Square, and Other Brands. Verify each. Other Brands = TIDAL vs AP $ + Proto vs AP $.

### Normalization rules

Strip both doc and sheet values to raw numbers before comparing:

- **Dollars:** Strip `$`, `M`, `B`, `K`, commas. Convert $B to $M (×1000). Parentheses → negative.
- **Percentages:** Strip `%`, `+`, `-`. Parentheses → negative.
- **Points:** Strip `pts`, `+`, `-`.
- **Actives:** Strip `M`.
- **Special values:** `n/a`, `--`, empty → treat as equivalent (skip comparison).

### Rounding tolerance

| Display format | Tolerance |
|---|---|
| Percentages (no decimal, e.g., "28%") | ±0.5 pp |
| Percentages (1 decimal, e.g., "4.3%") | ±0.05 pp |
| Dollar values in $B (2 decimals) | ±$5M |
| Dollar values in $M (no decimal) | ±$0.5M |
| Dollar values in $M (1 decimal) | ±$0.05M |
| Points (no decimal) | ±0.5 pts |

**PASS** if within tolerance. **FAIL** if outside tolerance or expected value not found in doc.

### Special cases

- **Rule of 40:** Actual is a percentage; deltas are in pts, not dollars or percentages
- **Monetization Rate:** Actual is a percentage; delta is in pts
- **Actives:** Actual is in M; delta is in M (not dollars)
- **Proto/Hardware:** May have negative actuals — verify sign matches
- **"n/a" YoY:** Skip the YoY comparison for that metric

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
