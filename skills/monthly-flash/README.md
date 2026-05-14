# Block Monthly Topline Flash — Automation

A single command (`/monthly-flash`) that generates, publishes, and validates the Block Monthly Topline Flash using Claude Code. **v2.0** — sources data from BDM + Snowflake (via `/flash-data`), populates the Doc Claude tab table via the Docs API, and uses a persistent template shell rather than wiping + reinserting markdown.

---

## What It Does

Each month after close, Block FP&A publishes a topline flash email with preliminary results for senior management. This system automates the entire pipeline:

1. **Builds the data layer** (`/flash-data`) — pulls every in-scope metric directly from BDM + Snowflake, computes derivations (Rule of 40, Adj OpEx via GP − Adj OI identity, V/A/F bucket totals, etc.), and writes raw values + cell formats into the brand reporting model at `MRP Charts & Tables!L400:S427` (28×8 Flash table) and `L432:R468` (37×7 Standardized P&L). Also emits a JSON packet at `/tmp/flash_out_{month}.json` with formatted strings + raw values + line-item OpEx detail for driver attribution.

2. **Detects monthly vs. quarterly mode** — at quarter-end months (March, June, September, December), the command will switch to quarterly mode (narrative anchored to the full quarter, QTD columns). v2.0 ships monthly-only; quarterly mode is a planned follow-up.

3. **Generates the narrative** — writes a structured flash report with:
   - **Title block**: "Block Topline Flash: [Month] [Year]" + the standard disclaimer with `[MRP DATE]` placeholder.
   - **Summary section**: Block GP headline with brand bridge, followed by Cash App (5 sub-products + Actives + Inflows + Commerce GMV), Square (5 sub-products + Global/US/INTL GPV), TIDAL, Proto, Adjusted OpEx with **GAAP V/A/F bucket commentary + driver attribution**, Adjusted OI, and Rule of 40.
   - **GAAP V/A/F drivers** — each Variable / Acquisition / Fixed bucket shows top 2-3 line items by |Δ| vs OL with the |Δ| ≥ $2M OR ≥ 5% of bucket materiality threshold. Buckets with |Δ| ≥ $20M OR ≥ 10% are flagged with a red-bold "**Corp to include context.**" marker.
   - **Variance precision rule** — narrative variance values (and table columns 2-4) follow the ±10 rule: `|magnitude| ≤ 10` → 1 decimal (`9.5%`, `$9.5M`, `+5.8 pts`); `> 10` → integer (`215%`, `$14M`, `+22 pts`). YoY columns / rates are not reformatted.

4. **Publishes to Google Doc** — the Claude tab is a persistent template (H1, disclaimer, H2 markers, 28×7 table shell). Each run:
   - Replaces `[MONTH]` / `[YEAR]` / `[MRP DATE]` placeholders
   - Inserts the narrative bullets between the H2 "Summary" and H2 "Summary Table" anchors
   - **Populates the Summary Table cells directly from the sheet** via `populate_flash_table.py` (Docs API batch-update). Values pass writes text + Roboto 10pt + CENTER + bold for rows 10/26/27 (Block / Adj OI / R40). Colors pass applies green/red to cols 2-4 above their thresholds (±$0.5M for col 2, ±1% for cols 3-4); YoY cols 5-6 are always black.

5. **Validates the data** — compares every metric value in the published Doc against the source ranges. Reports PASS/FAIL with mismatch details.

The output is a management-ready Google Doc tab, a local markdown file, and a validation report. One `[MRP DATE]` placeholder is left for the Monthly Management Reporting Pack date, which varies each month.

---

## How To Run

Open Claude Code in the project directory and type:

```
/monthly-flash
```

That's it. The command handles everything end-to-end:
- Step 1: Auth check (Google Drive)
- Step 2: Read MRP Charts & Tables sheet + detect monthly vs. quarterly mode
- Step 3: Generate the flash narrative (monthly or quarterly template)
- Step 4: Save markdown file
- Step 5: Publish to Google Doc (with formatting fixes)
- Step 6: Validate every metric against the source sheet
- Step 7: Report results (including which mode was used)

Output files:
- `~/Desktop/Nick's Cursor/Monthly Reporting/monthly_flash_YYYY_MM.md`
- `~/Desktop/Nick's Cursor/Monthly Reporting/validation_YYYY_MM.md`

### Standalone commands

You can also run validation independently:
- `/monthly-validate` — re-run validation on an already-published Doc (useful after manual edits)

---

## Quarter-End Mode

**Status:** v2.0 ships monthly-only. Quarter-end months (March, June, September, December) will get a QTD pull + quarterly-anchored commentary in a follow-up release. Same Doc tab + table shape — different sourcing window + narrative phrasing.

---

## What's In This Directory

```
skills/monthly-flash/
  ├── commands/                          Slash commands (what you type)
  │   ├── monthly-flash.md                Full pipeline: data layer → narrative → publish → validate
  │   └── monthly-validate.md             Standalone validation (re-check without regenerating)
  │
  ├── skills/                            Reference docs (loaded as context)
  │   └── financial-reporting.md          Global formatting recipe (rounding, signs, ±10 rule, etc.)
  │
  └── flash-data/                        Data + narrative + table population layer (v2.0)
      ├── commands/
      │   └── flash-data.md               /flash-data — populates the sheet ranges + emits the JSON packet
      ├── skills/
      │   └── flash-data-sourcing.md      Source-of-truth: BDM metric / Snowflake table per row
      ├── helpers/
      │   ├── flash_data.py               Derivations + sheet-format strings + raw values (input → /tmp/flash_out_*.json)
      │   ├── build_narrative.py          Narrative generator (consumes the packet, applies ±10 rule)
      │   └── populate_flash_table.py     Docs API batch-update: values pass + colors pass for the Claude tab table
      └── test/
          └── apr26_raw.json              Validated Apr'26 fixture (do not commit live data)
```

The monthly flash reuses the same `gdrive-cli.py` tool from `skills/weekly-reporting/gdrive/` for all Google Sheets and Docs operations.

---

## Key Data Sources

| Source | What It Provides |
|--------|-----------------|
| BDM (Block Data Mart) | All headline / sub-product GP, GPV, GMV, Actives, Inflows, Adj OI, GAAP OpEx line items |
| Snowflake — `app_finance_cash.fands.business_metrics_actuals_outlooks` | Cash App actives + inflows (plan + actuals) |
| Snowflake — `AP_CUR_BI_G.CURATED_ANALYTICS_GREEN.CUR_C_M_ORDER_MASTER` | Commerce GMV actuals |
| Snowflake — `app_hexagon.block.operational_metrics_forecast` | Commerce GMV plan scenarios |
| Snowflake — `app_bi.square_fns.vcompany_goals` | Square US/INTL GPV plan scenarios |
| Hyperion — `app_hexagon.schedule2.finstmt_master` | US Payments GP (product=1010 direct; BDM aggregate disagrees by ~$17M) |
| Brand reporting model — `MRP Charts & Tables!L400:S427` | Flash table (28×8): label, Actual, vs. OL $/%, vs. AP $/%, YoY %, Prior-mo YoY % |
| Brand reporting model — `MRP Charts & Tables!L432:R468` | Standardized P&L (37×7): GAAP OpEx by line item, V/A/F bucket totals |

The full source-of-truth mapping lives in `flash-data/skills/flash-data-sourcing.md`.

### Metrics Covered

| Section | Metrics |
|---------|---------|
| Volume | Cash App Actives, Cash App Inflows per Active, Commerce GMV, Square GPV (Global / US / INTL / INTL CC) |
| Gross Profit | Block GP; Cash App GP (Commerce, Borrow, Cash App Card, Instant Deposit, Post-Purchase BNPL); Square GP (US Payments, INTL Payments, Banking, SaaS, Hardware); TIDAL GP; Proto GP |
| Profitability | Adjusted OpEx (GAAP V/A/F line items + bucket totals), Adjusted OI, Rule of 40 |

---

## Comparison Framework

The flash compares to **Annual Plan (AP)** for Q1. For subsequent quarters, the comparison point shifts per the financial-reporting recipe:

| Quarter | Comparison Point |
|---------|-----------------|
| Q1 | AP |
| Q2 | Q2OL |
| Q3 | Q3OL |
| Q4 | Q4OL |

---

## What's Automated vs. Manual

| Automated | Manual |
|-----------|--------|
| Sourcing every metric from BDM + Snowflake (`/flash-data`) | `[MRP DATE]` — Monthly Reporting Pack date placeholder |
| Writing the sheet ranges (Flash + Stnd P&L) with formats | Final review before distribution |
| Narrative generation with ±10 precision rule + driver attribution | Qualitative commentary beyond V/A/F driver call-outs |
| Brand bridge (Cash App + Square + Other Brands) | Sub-product narrative phrasing tweaks |
| Sub-product outperformance ranking | |
| Doc publishing: placeholder fill + narrative insert + table populate + color/bold formatting | |
| Cell-by-cell validation between sheet and Doc | |

---

## Doc Publishing Notes

- **Persistent template tab.** The Claude tab is a permanent template: H1 title, italic disclaimer, H2 section markers, and a 28×7 table shell. Each run mutates the placeholders + narrative space + table cells in place — it does not wipe + reinsert.
- **Table population path.** `populate_flash_table.py` builds Docs API batchUpdate requests targeting each cell's `startIndex` directly. This avoids the multi-table-per-tab limitation in `sq agent-tools docs-edit update_table_cell` (which ignores `table_start_position` / `table_index`).
- **Bullet nesting.** The markdown converter renders parent bullets (Cash App, Square) as paragraphs rather than list items. The command deletes bullets, inserts tab characters at sub-item starts, then recreates bullets with `BULLET_DISC_CIRCLE_SQUARE` for nesting.
- **Italic/bold disclaimer.** The converter doesn't render `*italic **bold** italic*` cleanly. The command strips literal asterisks and applies italic/bold via `updateTextStyle`.
- **Red "Corp to include context" markers.** Bucket-level overruns (≥$20M OR ≥10% vs OL) append a red-bold "Corp to include context." sentinel. Step 5d in the command applies the foreground color post-insert.
