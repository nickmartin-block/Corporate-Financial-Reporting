---
name: monthly-flash
description: Generate, publish, and validate the Block Monthly Topline Flash end-to-end. Step 1 invokes /flash-data to populate the Flash table (L400:S427) and Standardized P&L (L432:R468) from BDM + Snowflake. Step 2-3 read those ranges, generate the narrative with GAAP V/A/F + driver commentary, publish to the target Doc, and validate. Replaces the old flow that depended on a manually-populated MRP Charts & Tables sheet.
allowed-tools:
  - Bash(cd ~/skills/gdrive && uv run gdrive-cli.py:*)
  - Bash(sq agent-tools google-drive:*)
  - Bash(python3:*)
  - Read
  - Write
  - Edit
metadata:
  author: nmart
  version: "2.0"
  status: active
---

# Block Monthly Topline Flash

Generate, publish, and validate the monthly flash report in one pass. v2.0 sources data from BDM + Snowflake (via `/flash-data`) instead of the manual MRP Charts & Tables sheet.

**Dependencies:**
- `~/Corporate-Financial-Reporting/skills/monthly-flash/flash-data/commands/flash-data.md` — Step 1 invokes this
- `~/Corporate-Financial-Reporting/skills/monthly-flash/flash-data/skills/flash-data-sourcing.md` — source-of-truth mapping
- `~/Corporate-Financial-Reporting/skills/monthly-flash/skills/financial-reporting.md` — global formatting recipe

**Scope:** v2.0 is monthly-only (intra-quarter months). Quarter-end months (Mar, Jun, Sep, Dec) — quarterly mode — will ship in a follow-up.

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
| Output Path | `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md` |
| Validation Path | `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md` |
| Helper data packet | `/tmp/flash_out_{month}.json` (produced by Step 1) |

---

## Step 1 — Build the data layer

Invoke `/flash-data` to populate `L400:S427` and `L432:R468`, and emit the helper JSON packet `/tmp/flash_out_{month}.json`. See `flash-data.md` for the full sourcing reference.

If the user has already run `/flash-data` recently for this month, the JSON packet at `/tmp/flash_out_{month}.json` is sufficient — re-run is optional. Otherwise, run it now.

After flash-data completes, the brand reporting model holds raw values formatted by sheet cell formats. The `/tmp/flash_out_{month}.json` packet has:
- `flash_table_raw` / `flash_table_formatted` — 28 rows × 8 cols
- `pnl_table_raw` / `pnl_table_formatted` — 37 rows × 7 cols
- `raw_derived` — all derived values (Adj OpEx, R40 components, V/A/F bucket totals, every OpEx line item delta) needed for driver attribution

---

## Step 2 — Read the populated data layer

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L400:S427"
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 --range "MRP Charts & Tables\!L432:R468"
```

Equivalent — load the formatted tables directly from the JSON packet (`flash_table_formatted` + `pnl_table_formatted`).

### Flash table row mapping (L400:S427, 1-indexed from row 400)

| Row offset | Metric |
|---|---|
| 0 | Period header (e.g., `Apr'26`) |
| 1 | Column headers |
| 2 | Cash App Actives |
| 3 | Cash App Inflows per Active |
| 4 | Commerce GMV |
| 5 | Square GPV |
| 6 | Square US GPV |
| 7 | Square INTL GPV |
| 8 | Square INTL GPV (CC) — blank in v1 |
| 9 | "Gross Profit" section header |
| 10 | Block GP |
| 11 | Cash App GP |
| 12 | Commerce GP |
| 13 | Borrow GP |
| 14 | Cash App Card GP |
| 15 | Instant Deposit GP |
| 16 | Post-Purchase BNPL GP |
| 17 | Square GP |
| 18 | US Payments GP |
| 19 | INTL Payments GP |
| 20 | Banking GP |
| 21 | SaaS GP |
| 22 | Hardware GP |
| 23 | TIDAL GP |
| 24 | Proto GP |
| 25 | Adjusted Opex |
| 26 | Adjusted OI |
| 27 | Rule of 40 |

### Column mapping (Flash table)

| Col offset | Content |
|---|---|
| 0 | Row label |
| 1 | Actual |
| 2 | vs. OL $ |
| 3 | vs. OL % |
| 4 | vs. AP $ |
| 5 | vs. AP % |
| 6 | YoY % |
| 7 | Prior-month YoY % |

### Standardized P&L row mapping (L432:R468)

| Row offset | Section / Metric |
|---|---|
| 0 | Column headers |
| 1 | "Variable Operational Costs" (section) |
| 2 | P2P |
| 3 | Risk Loss |
| 4 | Card Issuance |
| 5 | Warehouse Financing |
| 6 | Other (parent) |
| 7 | Hardware Logistics (child) |
| 8 | Bad Debt Expense (child) |
| 9 | Customer Reimbursements (child) |
| 10 | **Total Variable Operational Costs** |
| 11 | "Acquisition Costs" (section) |
| 12 | Marketing (Non-People) (parent) |
| 13-16 | Marketing, Onboarding, Partnership Fees, Reader Expense (children) |
| 17 | Sales & Marketing (People) |
| 18 | **Total Acquisition Costs** |
| 19 | "Fixed Costs" (section) |
| 20 | Product Development People |
| 21 | G&A People (parent) |
| 22-23 | G&A People (ex. CS), Customer Support People (children) |
| 24 | Software & Cloud (parent) |
| 25-26 | Software, Cloud fees (children) |
| 27 | Taxes, Insurance & Other Corp |
| 28 | Litigation & Professional Services (parent) |
| 29-30 | Legal fees, Other Professional Services (children) |
| 31 | Rent, Facilities, Equipment |
| 32 | Travel & Entertainment |
| 33 | Hardware Production Costs |
| 34 | Non-Cash expenses (ex. SBC) |
| 35 | **Total Fixed Costs** |
| 36 | **Total Block GAAP OpEx** |

### Comparison point detection

The Outlook scenario depends on the report quarter: Q1 → Q1OL, Q2 → Q2OL, Q3 → Q3OL, Q4 → Q4OL. Flash-data already wrote the correct scenario into the "vs. OL" columns — narrative just references "Q2OL" (or whichever) per the financial-reporting recipe.

---

## Step 3 — Generate the flash narrative

Determine report month and year from the period header (row 0, col 1 in L400:S427 — e.g., `Apr'26` → April 2026, prior month = March 2026).

Pull driver attribution from `raw_derived` (in `/tmp/flash_out_{month}.json`) for the V/A/F commentary. Use these thresholds:

- **Driver inclusion:** abs(line item Δ vs OL) ≥ $2M OR ≥ 5% of bucket total. Rank by abs Δ desc. Top 2-3 per bucket. Use discretion on what's notable — sometimes the largest 3 are all small and noise, in which case mention 1-2 or skip.
- **Corp-context flag:** bucket-level variance ≥ $20M abs OR ≥ 10% vs OL → append "**Corp to include context.**" (this phrase gets red text via Step 5d post-insert).

### Monthly narrative structure

Every **bold label** below must be bold in the output. Apply all formatting from the financial-reporting recipe.

```
# Block Topline Flash: [Full Month] [Full Year]

*This flash report provides a preliminary view of month-end close results, with figures subject to further review and potential adjustment. This streamlined report includes minimal commentary, as a more comprehensive analysis of underlying drivers will be provided in the* ***Monthly Management Reporting Pack scheduled for [MRP DATE]***.

*Please note that the flash topline aligns with our externally reported guidelines, which include Cash App Pay Gross Profit within Cash App excluding Commerce. All comparisons reference [Year] Annual Plan unless otherwise noted. Variances in charts are not color coded for amounts within +/- 1%, $0.5M, or YoY comparisons.*

## [Full Month] Summary

**Block gross profit** was [Actual] in [Month], growing [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]) and landing [vs AP $] ([vs AP %]) vs. AP ([CA contribution] from Cash App, [SQ contribution] from Square, and [Other contribution] from Other Brands).

- **Cash App** gross profit for [Month] was [Actual], growing [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]) and landing [vs AP $] or [vs AP %] above AP. Outperformance vs. AP: [positive sub-products sorted by $ desc], partially offset by [negative sub-products].
    - **Commerce GMV** was [Actual], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
    - **Cash App Actives** landed at [Actual], [vs AP $] below AP, growing [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
    - **Cash App Inflows per Active** were [Actual], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
- **Square** gross profit for [Month] was [Actual], growing [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]) and landing [vs AP $] or [vs AP %] vs. AP. Outperformance vs. AP: [positive sub-products sorted by $ desc], partially offset by [negative sub-products].
    - **Global GPV** was [Actual], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
    - **US GPV** was [Actual], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
    - **INTL GPV** was [Actual], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).
- **TIDAL** gross profit for [Month] was [Actual], [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]) and landed [vs AP $] or [vs AP %] vs. AP.
- **Proto** gross profit for [Month] was [Actual], and landed [vs AP $] vs. AP.

**Adjusted Opex** for [Month] was [Actual], [vs OL $] ([vs OL %]) vs. [OL scenario] and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).

- **Variable costs** were [Actual] ([YoY]% YoY), [vs OL $] ([vs OL %]) vs. [OL scenario]. Top drivers: [driver 1 name +/- $X (X%)], [driver 2 name +/- $X (X%)], [driver 3 name if material]. [**Corp to include context.** if bucket variance ≥ $20M OR ≥ 10%]
- **Acquisition costs** were [Actual] ([YoY]% YoY), [vs OL $] ([vs OL %]) vs. [OL scenario]. Top drivers: [driver 1], [driver 2], [driver 3 if material]. [**Corp to include context.** if material]
- **Fixed costs** were [Actual] ([YoY]% YoY), [vs OL $] ([vs OL %]) vs. [OL scenario]. Top drivers: [driver 1], [driver 2], [driver 3 if material]. [**Corp to include context.** if material]

**Adjusted Operating Income** landed at [Actual] in [Month], [vs AP $] ([vs AP %]) vs. AP and [YoY]% YoY ([Prior-mo YoY]% in [Prior Month]).

**[Month] Rule of 40** was [Actual], [vs AP pts] above AP and [YoY pts] YoY ([Prior-mo YoY pts] in [Prior Month]).
```

### Value formatting rules

- Use values from the formatted table (`flash_table_formatted` + `pnl_table_formatted`) — they already match Flash convention
- Signs: `+` for positive variances, `-` for negative. Parentheses in source = negative in text (e.g., `($56M)` → `-$56M`)
- "nm" in YoY → use it as-is (the variance is too large to be meaningful)
- `[MRP DATE]` → placeholder; do not fill in

### Sub-product outperformance lines

For Cash App and Square, list sub-products by AP $ delta descending (positive first, then "partially offset by" negatives). Omit sub-products with zero or negligible delta.

### Other Brands bridge

Other Brands contribution = TIDAL vs AP $ + Proto vs AP $.

### Driver commentary construction (V/A/F buckets)

For each bucket (Variable / Acquisition / Fixed), pull line-item deltas from `raw_derived`:

1. Compute `(line_item_actual - line_item_ol)` for every leaf line item in the bucket
2. Rank by absolute delta, descending
3. Filter: only keep line items where `abs(delta) >= 2,000,000` OR `abs(delta) / bucket_total >= 0.05`
4. Take top 2-3 from the filtered list
5. Format each as: `[line item name] [+/-$X.XM] ([+/-X.X%])`
6. Compose the bullet: "Top drivers: [d1], [d2]" or "Top drivers: [d1], [d2], partially offset by [d3]" if d3 is opposite sign

If no line items pass the filter, drop the "Top drivers" clause entirely — just report the bucket total + variance.

If `abs(bucket_delta) >= 20,000,000` OR `abs(bucket_delta) / bucket_total >= 0.10`, append " **Corp to include context.**" (note the leading space and the bold marker — this phrase gets red-colored in Step 5d).

---

## Step 4 — Save the MD

Write to `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md`.

---

## Step 5 — Publish to Google Doc

### 5a — Clear the target tab (`Claude`)

Use tab ID `t.6lmbmhs5p561`. Get the content end index via `docs-inspect`, delete content range `[1, endIndex-1]` with `tabId`.

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
    - **Cash App sub-items:** Commerce GMV, Cash App Actives, Cash App Inflows per Active
    - **Square sub-items:** Global GPV, US GPV, INTL GPV
5. `createParagraphBullets` with `BULLET_DISC_CIRCLE_SQUARE` preset on the full GP section range
6. Include `tabId` in every range/location object

### 5d — Apply red color to "Corp to include context" phrases

For each `**Corp to include context.**` occurrence in the rendered doc (under V/A/F bullets):

1. Find the paragraph index containing the phrase
2. Compute the text range for "Corp to include context." within that paragraph
3. Apply `updateTextStyle` with `foregroundColor: { red: 0.85, green: 0.16, blue: 0.16 }` (Block red, slightly darker than pure red)
4. Apply `bold: true` if not already bold (the markdown asterisks should have made it bold via the converter — verify)
5. Process matches in reverse paragraph order to preserve indices

### 5e — Fix italic/bold on disclaimer

After insertion, check the first disclaimer paragraph. If it contains literal `*` characters (markdown not rendered):

1. Delete the literal asterisk characters via `deleteContentRange`
2. Apply `italic: true` via `updateTextStyle` to the entire first disclaimer paragraph
3. Apply `bold: true` via `updateTextStyle` to "Monthly Management Reporting Pack scheduled for [MRP DATE]"

Process deletions in reverse index order to preserve earlier indices.

### 5f — Populate the Summary Table

The Claude tab has a persistent 28×7 table shell (heading "Summary Table"). The narrative markdown inserted in 5b does NOT include this table — it's populated directly from the sheet via a separate Docs API batch-update. Two passes: values, then colors.

```bash
# Values pass
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read \
    15j9tou-7OmLxvk41cmkJkYTAQLXXLl08slX9p8RsVL0 \
    --range "'MRP Charts & Tables'!L400:S427" > /tmp/flash_sheet.json
cd ~/skills/gdrive && uv run gdrive-cli.py docs get \
    1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA --include-tabs > /tmp/flash_doc.json
python3 ~/Desktop/Nick\'s\ Cursor/Corporate-Financial-Reporting/skills/monthly-flash/flash-data/helpers/populate_flash_table.py \
    /tmp/flash_sheet.json /tmp/flash_doc.json t.6lmbmhs5p561 --pass values \
    | (cd ~/skills/gdrive && uv run gdrive-cli.py docs batch-update \
          1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA)

# Colors pass — re-read the doc first so indices are fresh
cd ~/skills/gdrive && uv run gdrive-cli.py docs get \
    1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA --include-tabs > /tmp/flash_doc_v2.json
python3 ~/Desktop/Nick\'s\ Cursor/Corporate-Financial-Reporting/skills/monthly-flash/flash-data/helpers/populate_flash_table.py \
    /tmp/flash_sheet.json /tmp/flash_doc_v2.json t.6lmbmhs5p561 --pass colors \
    | (cd ~/skills/gdrive && uv run gdrive-cli.py docs batch-update \
          1faTUvm5CYK-W4J7JeKezbi1aEvRbSJ95vkjMtzc_sJA)
```

What this does:
- **Values pass:** clears every data cell in rows 2-27, inserts the formatted sheet value, applies Roboto 10pt + CENTER. Sheet col mapping: doc col 1 ← sheet col M (Actual), col 2 ← N (vs. OL $), col 3 ← O (vs. OL %), col 4 ← Q (vs. AP %), col 5 ← R (YoY %), col 6 ← S (Prior-mo YoY %). The `vs. AP $` column in the sheet (col P) is intentionally not used — the doc table only carries the % delta. Row 8 "Square INTL GPV (CC)" is left blank until CC sourcing lands in flash-data.
- **Bold rows (label + all 6 data cells):** rows 10 (Block GP), 26 (Adjusted OI), 27 (Rule of 40). Controlled by the `BOLD_ROWS` constant in `populate_flash_table.py`. The values pass writes bold:true for these rows and bold:false for every other row, so the state is deterministic across runs (no stale bold survives a removal from the set).
- **Variance precision rule (cols 2-4 only):** values with `|magnitude| ≤ 10` keep 1 decimal (`9.5%`, `$9.5M`, `+5.8 pts`); values with `|magnitude| > 10` become integer (`215%`, `$14M`, `+22 pts`). Half-up rounding. Applied in `populate_flash_table.py` (`reformat_variance`). YoY columns (5 + 6) are not reformatted — they pass through from the sheet as-is.
- **Colors pass (cols 2-4 only):** green for positive, red for negative, black for everything else — `|Δ|` must exceed the column's threshold:
  - col 2 (vs. Q2OL $) → $0.5M (inclusive: `≤ $0.5M` stays black)
  - col 3 (vs. Q2OL %) → 1.0% (inclusive: `≤ 1.0%` stays black)
  - col 4 (vs. AP %) → 1.0% (inclusive)
  - cols 5 + 6 (YoY %, Mar YoY %) → always black, never colored
  - `nm` / `--` / empty cells stay black.
  Coloring is sign-based on the displayed value: `(X)` or `-X` → red; `+X` or `X` → green. OpEx-direction inversion (favorable-when-negative) is NOT applied — future enhancement if desired.

The populator assumes the table shell exists. If the shell is destroyed (e.g., 5a clears it), Step 5f will fail. Steps 5a-5e should be revised when this command moves to a fully template-based publish flow.

### 5g — Verify

Read back the doc structure and confirm:
- H1: "Block Topline Flash: [Month] [Year]"
- Italic disclaimer paragraphs (first with bold MRP reference)
- H2: "[Month] Summary"
- Bullet nesting: Cash App / Square at level 0, sub-items at level 1
- All metric labels bold
- "Corp to include context" phrases in red wherever they appear
- Summary Table populated with sheet values, % cols color-coded

---

## Step 6 — Validate

Run `~/Corporate-Financial-Reporting/skills/monthly-flash/commands/monthly-validate.md`.

Execute its Steps 1–7. The validation re-reads the populated ranges (`L400:S427` + `L432:R468`) and the published Doc, compares every metric value, and saves a validation report to:

```
~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md
```

---

## Step 7 — Report back

Tell Nick:
- **File:** path to the saved .md
- **Doc:** link to the Google Doc with tab
- **Data layer refresh time:** when `/flash-data` last populated the ranges
- **Validation:** PASS or FAIL (N values compared, N failures). Include failure details if any.
- **Corp-context flags:** which V/A/F buckets are flagged for context
- **Placeholders:** count of `[MRP DATE]` items remaining
- If PASS → "Data is clean."

---

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| L400:S427 is empty or stale | `/flash-data` didn't run for this month, or wrote to a different period | Re-run Step 1. Check the period header in row 400 col M. |
| Driver attribution misses obvious lines | Threshold too strict (e.g. all line items under $2M for a small bucket) | Lower threshold in this run, or report top 3 unconditionally. Use discretion. |
| Red text didn't apply | Phrase string mismatch (extra punctuation / spaces) | Step 5d find-string must match exactly — adjust if narrative text drifted. |
| Validation fails on a sub-product GP | Source convention change since flash-data last ran | Re-run /flash-data; if persistent, check flash-data-sourcing.md mapping for the row. |
