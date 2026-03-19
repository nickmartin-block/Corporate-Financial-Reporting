---
name: monthly-flash
description: Generate, publish, and validate the Block Monthly Topline Flash. Reads the MRP Charts & Tables sheet, generates the flash narrative, publishes to Google Doc with proper formatting, and validates every metric against the source sheet. Single command for end-to-end monthly flash production.
allowed-tools:
  - Bash(cd ~/skills/gdrive && uv run gdrive-cli.py:*)
  - Read
  - Write
  - Edit
metadata:
  author: nmart
  version: "1.0"
  status: active
---

# Block Monthly Topline Flash

Generate, publish, and validate the monthly flash report in one pass.

**Dependencies:** Load `~/skills/weekly-reporting/skills/financial-reporting.md` for global formatting standards (rounding, signs, comparison framework).

---

## Configuration

| Parameter | Value |
|---|---|
| Source Sheet | `15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0` |
| Source Tab | `MRP Charts & Tables` |
| Source Range | `L11:Y90` |
| Target Doc | `1S--3vA6obl4hBF2Nw2jqD1M4sjEkD8FcpC073-OlAUY` |
| Target Tab | `t.mkykw9vq4coc` |
| Output Path | `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md` |
| Validation Path | `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md` |

---

## Step 1 — Auth

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py auth status
```

Stop if not valid.

---

## Step 2 — Read the source sheet

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L11:Y90"
```

### Column mapping (current month — columns M through S)

| Index | Content |
|---|---|
| 0 | Row label |
| 1 | Actual |
| 2 | vs. Q1OL $ |
| 3 | vs. Q1OL % |
| 4 | vs. AP $ |
| 5 | vs. AP % |
| 6 | YoY % |
| 7 | Jan YoY % |

**Comparison point:** Q1 → AP (columns 4-5). For Q2 use Q2OL, Q3 use Q3OL, Q4 use Q4OL per the financial-reporting recipe.

### Row mapping (0-indexed from values array)

**Main Summary (rows 2–27):**

| Row | Metric |
|---|---|
| 2 | Cash App Actives |
| 3 | Cash App Inflows per Active |
| 4 | Commerce GMV |
| 5 | Square GPV |
| 6 | Square US GPV |
| 7 | Square INTL GPV |
| 8 | Square INTL GPV (CC) |
| 10 | Block GP |
| 11 | Cash App GP |
| 12 | Commerce GP (sub-product) |
| 13 | Borrow GP (sub-product) |
| 14 | Cash App Card GP (sub-product) |
| 15 | Instant Deposit GP (sub-product) |
| 16 | Post-Purchase BNPL GP (sub-product) |
| 17 | Square GP |
| 18 | US Payments GP (sub-product) |
| 19 | INTL Payments GP (sub-product) |
| 20 | Banking GP (sub-product) |
| 21 | SaaS GP (sub-product) |
| 22 | Hardware GP (sub-product) |
| 23 | TIDAL GP |
| 24 | Proto GP |
| 25 | Adjusted Opex |
| 26 | Adjusted OI |
| 27 | Rule of 40 |

**Cash App ex. Commerce (rows 32, 35):**

| Row | Metric |
|---|---|
| 32 | Cash App ex. Commerce GP |
| 35 | Monetization Rate (ex. Commerce) |

**Opex Summary (row 74) and OpEx Breakdown (rows 77–79):**

| Row | Metric |
|---|---|
| 74 | Variable Profit |
| 77 | Variable costs |
| 78 | Acquisition costs |
| 79 | Fixed costs |

---

## Step 3 — Generate the monthly flash

Determine month and year from the sheet header (row 0, index 1 — e.g., "Feb'26"). Prior month = one month back.

### Narrative structure

Generate markdown following this exact structure. Every **bold label** below must be bold in the output. Apply all formatting from the financial-reporting recipe.

```
# Block Topline Flash: [Full Month] [Full Year]

*This flash report provides a preliminary view of month-end close results, with figures subject to further review and potential adjustment. This streamlined report includes minimal commentary, as a more comprehensive analysis of underlying drivers will be provided in the* ***Monthly Management Reporting Pack scheduled for [MRP DATE]***.

*Please note that the flash topline aligns with our externally reported guidelines, which include Cash App Pay Gross Profit within Cash App excluding Commerce. All comparisons reference [Year] Annual Plan unless otherwise noted. Variances in charts are not color coded for amounts within +/- 1%, $0.5M, or YoY comparisons.*

## [Full Month] Summary

**Block gross profit** was [Actual] in [Month], growing [YoY]% YoY ([Jan YoY]% in [Prior Month]) and landing [vs AP $] ([vs AP %]%) vs. AP ([CA contribution] from Cash App, [SQ contribution] from Square, and [Other contribution] from Other Brands).

- **Cash App** gross profit for [Month] was [Actual], growing [YoY]% YoY ([Jan YoY]% in [Prior Month]) and landing [vs AP $] or [vs AP %]% above AP. Outperformance vs. AP: [positive sub-products sorted by $ desc], partially offset by [negative sub-products].
    - **Cash App ex. Commerce gross profit** was [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).
    - **Cash App Actives** landed at [Actual], [vs AP $] below AP, growing [YoY]% YoY ([Jan YoY]% in [Prior Month]).
    - **Cash App Inflows per Active** were [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).
    - **Cash App Monetization Rate (ex. Commerce)** was [Actual], [vs AP] pts vs. AP.
    - **Commerce GMV** was [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).
- **Square** gross profit for [Month] was [Actual], growing [YoY]% YoY ([Jan YoY]% in [Prior Month]) and landing [vs AP $] or [vs AP %]% above AP. Outperformance vs. AP: [positive sub-products sorted by $ desc], partially offset by [negative sub-products].
    - **Global GPV** was [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).
    - **US GPV** was [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).
    - **INTL GPV** was [Actual], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]). On a constant-currency basis, **INTL GPV** was [CC Actual], [CC vs AP $] ([CC vs AP %]%) vs. AP and [CC YoY]% YoY.
- **TIDAL** gross profit for [Month] was [Actual], [YoY]% YoY ([Jan YoY]% in [Prior Month]) and landed [vs AP $] or [vs AP %]% vs. AP.
- **Proto** gross profit for [Month] was [Actual], and landed [vs AP $] vs. AP.

**Variable Profit** landed at [Actual] in [Month], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).

**Adjusted Opex** for [Month] was [Actual], [vs AP $] ([vs AP %]%) below AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).

- **Variable costs** were [Actual] ([YoY]% YoY), [vs AP $] ([vs AP %]%) below AP.
- **Acquisition costs** were [Actual] ([YoY]% YoY), [vs AP $] ([vs AP %]%) above AP.
- **Fixed costs** were [Actual] ([YoY]% YoY), [vs AP $] ([vs AP %]%) above AP.

**Adjusted Operating Income** landed at [Actual] in [Month], [vs AP $] ([vs AP %]%) vs. AP and [YoY]% YoY ([Jan YoY]% in [Prior Month]).

**[Month] Rule of 40** was [Actual], [vs AP] pts above AP and [YoY] pts YoY ([Jan YoY] pts in [Prior Month]).
```

### Value formatting rules

- Use source values from the sheet as-is for dollar amounts and percentages
- Round per recipe: ≥$10M → no decimal ($87M), <$10M → 1 decimal ($4.8M), $B → 2 decimals ($2.79B)
- Percentages from sheet: keep as-is (sheet already applies rounding)
- Signs: `+` for positive variances, `-` for negative. Sheet parentheses = negative in text (e.g., `($56M)` → `-$56M`)
- "n/a" in YoY → omit the YoY comparison for that metric
- `[MRP DATE]` → placeholder; do not fill in

### Sub-product outperformance lines

For Cash App and Square, list sub-products by AP $ delta descending (positive first, then "partially offset by" negatives). Omit sub-products with zero or negligible delta.

### Other Brands bridge

Other Brands contribution = TIDAL vs AP $ + Proto vs AP $.

---

## Step 4 — Save the MD

Write to `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md`.

---

## Step 5 — Publish to Google Doc

### 5a — Clear the target tab

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py docs get DOC_ID
```

Find the target tab, get the content end index, delete content range `[1, endIndex-1]` with `tabId`.

### 5b — Insert markdown

```bash
cat "FILEPATH" | (cd ~/skills/gdrive && uv run gdrive-cli.py docs insert-markdown DOC_ID --tab TAB_ID)
```

### 5c — Fix bullet nesting

The markdown converter does not handle nested bullet lists. After insertion:

1. Get paragraph indices from `docs get`
2. Identify the GP bullet section (Cash App through Proto)
3. `deleteParagraphBullets` on the entire GP section range
4. `insertText` a `\t` at the start of each sub-item paragraph (process in reverse index order):
   - **Cash App sub-items:** Cash App ex. Commerce GP, Actives, Inflows per Active, Monetization Rate, Commerce GMV
   - **Square sub-items:** Global GPV, US GPV, INTL GPV
5. `createParagraphBullets` with `BULLET_DISC_CIRCLE_SQUARE` preset on the full GP section range
6. Include `tabId` in every range/location object

### 5d — Fix italic/bold on disclaimer

After insertion, check the first disclaimer paragraph. If it contains literal `*` characters (markdown not rendered):

1. Delete the literal asterisk characters via `deleteContentRange`
2. Apply `italic: true` via `updateTextStyle` to the entire first disclaimer paragraph
3. Apply `bold: true` via `updateTextStyle` to "Monthly Management Reporting Pack scheduled for [MRP DATE]"

Process deletions in reverse index order to preserve earlier indices.

### 5e — Verify

Read back the doc structure and confirm:
- H1: "Block Topline Flash: [Month] [Year]"
- Italic disclaimer paragraphs (first with bold MRP reference)
- H2: "[Month] Summary"
- Bullet nesting: Cash App/Square at level 0, sub-items at level 1
- All metric labels bold

---

## Step 6 — Validate

### 6a — Read sources

Re-use sheet data from Step 2 if still in context. Read the doc text:

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py read DOC_ID --tab TAB_ID
```

### 6b — Build ground truth

For every metric in the row mapping, extract from the sheet:
- Actual (index 1)
- vs AP $ (index 4)
- vs AP % (index 5)
- YoY % (index 6)
- Jan YoY % (index 7)

Skip rows with `#REF!`, `#DIV/0!`, or empty values. Normalize all values:
- Strip `$`, `M`, `B`, `K`, `%`, `(`, `)`, `+`, `-`, spaces, commas
- Parentheses → negative
- $B → multiply by 1000 (to $M)
- Store as raw float

### 6c — Compare against doc

For each metric in the ground truth, search the doc text for the metric's bold label. Then verify each value type appears in the same paragraph:

| Value Type | What to check |
|---|---|
| Actual | The dollar amount or percentage immediately after the metric label |
| vs AP $ | Dollar amount near "vs. AP" or "above/below AP" |
| vs AP % | Percentage near "vs. AP" or "above/below AP" |
| YoY % | Percentage near "YoY" |
| Jan YoY % | Percentage in parentheses near "in [Prior Month]" |

**Normalization:** Strip both doc and sheet values to raw numbers using the same rules as 6b.

**Rounding tolerance:**
- Percentages (no decimal): ±0.5 pp
- Percentages (1 decimal): ±0.05 pp
- Dollar values in $B (2 decimals): ±$5M
- Dollar values in $M (no decimal): ±$0.5M
- Dollar values in $M (1 decimal): ±$0.05M
- Points: ±0.5 pts

**PASS** if within tolerance. **FAIL** if outside tolerance or value not found.

### 6d — Special cases

- **Rule of 40:** values are in % and pts, not dollars
- **Monetization Rate:** value is a percentage (1.68%), delta is in pts
- **Actives:** value is in M (56.9M), delta is in M
- **Proto/Hardware:** may have negative actuals — verify sign matches
- **"n/a" YoY:** skip YoY comparison for that metric

### 6e — Output report

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
- **File:** path to the saved .md
- **Doc:** link to the Google Doc with tab
- **Validation:** PASS or FAIL (N values compared, N failures). Include failure details if any.
- **Placeholders:** count of `[MRP DATE]` or `[DATA MISSING]` items remaining
- If PASS → "Data is clean."
