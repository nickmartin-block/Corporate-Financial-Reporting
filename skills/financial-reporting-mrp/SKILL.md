---
name: financial-reporting-mrp
description: Monthly Reporting Pack (MRP) sub-agent for Block FP&A. Pulls metric data from the Block Data MCP, creates a new monthly Google Doc, populates the full P&L table, product-level GP breakdowns, brand fact lines, and structured narrative placeholders. Runs a coverage check first (Phase A), then populates after Nick confirms (Phase B). Use when Nick says "data is ready, run the MRP." Must be loaded with the financial-reporting skill (global recipe).
depends-on: [financial-reporting, gdrive]
allowed-tools: [Bash(uv:*), Read]
metadata:
  author: nmart
  version: "1.0.0"
  status: "beta"
---

# Monthly Reporting Pack (MRP) Sub-Agent

## Prerequisites
Before running any step, verify auth: `cd ~/skills/gdrive && uv run gdrive-cli.py auth status`
If not authenticated, run `uv run gdrive-cli.py auth login` and stop.

## Trigger
Manual only. Nick will say: **"data is ready, run the MRP."**
Never self-initiate. Never run on a schedule.

## Reference Document
Prior month's MRP: `1Fusutm1sHO5zNhKR31XWywQaUSeYR2R25Ozmm4PqqnM`
Use this doc as the structural reference for section order, table layouts, and fact line style.

## Two-Phase Workflow

This agent runs in two phases. **Phase A must complete and Nick must confirm before Phase B begins.**

---

## Phase A — Coverage Check

**Purpose:** Map every metric needed for the MRP against what's available in the Block Data MCP. Surface gaps before attempting to populate the report.

**Step A1 — Read the reference MRP Doc**
```bash
cd ~/skills/gdrive && uv run gdrive-cli.py docs get 1Fusutm1sHO5zNhKR31XWywQaUSeYR2R25Ozmm4PqqnM
```
Extract every metric name, time period, and required field (Actual, YoY%, versus AP, QTD Pace).

**Step A2 — Search Block Data MCP for each metric**
For each metric, run `mcp__blockdata__metric_store_search` with the metric name and appropriate brand filter.

**Step A3 — Produce the coverage report**
Return a structured table:

```
## MRP Metric Coverage Report — [Run Date]

✅ Available in Block Data MCP (X metrics):
| Metric | MCP Metric ID | Brand |
|--------|--------------|-------|
| ...    | ...          | ...   |

❌ Not found in Block Data MCP (Y metrics):
| Metric | Suggested action |
|--------|-----------------|
| ...    | Request via: https://linear.app/squareup/new?template=bab7e06f-2599-4298-ab5b-fddcd4af9914 |

X of Z metrics covered. Proceed with population for available metrics, or pause to request missing ones first?
```

**Stop here. Wait for Nick's confirmation before continuing to Phase B.**

---

## Phase B — Population

Runs only after Nick confirms. For all uncovered metrics, insert `[DATA MISSING: {metric} | {period}]`.

**Step B1 — Determine comparison point**

| Quarter | Forecast Label |
|---------|---------------|
| Q1      | AP             |
| Q2      | Q2OL           |
| Q3      | Q3OL           |
| Q4      | Q4OL           |

**Step B2 — Pull data from Block Data MCP**
For each covered metric, use `mcp__blockdata__fetch_metric_data`:
- Month actuals (closed periods)
- QTD pace
- versus AP (delta % and $ amount)
- Prior year actuals (for YoY)
- Consensus and guidance where available

**Step B3 — Determine emoji per metric**
Apply to each metric's delta vs. [Forecast]:

| Delta vs. [Forecast] | Emoji |
|----------------------|-------|
| > +0.5%              | 🟢    |
| −0.5% to +0.5%       | 🟡    |
| < −0.5%              | 🔴    |

- Monthly closed metrics: use monthly delta
- Quarter-level metrics: use QTD delta
- bps metrics (monetization rate): same threshold in bps
- YoY is NOT used for emoji determination

**Step B4 — Create new Google Doc**
```bash
cd ~/skills/gdrive && uv run gdrive-cli.py docs create --title "[Month YYYY] — Monthly Management Reporting Pack"
```
Title format example: `March 2026 — Monthly Management Reporting Pack`

**Step B5 — Populate sections in order**
See "Section Structure" below.

**Step B6 — Report back**
Return:
- Sections populated successfully
- `[DATA MISSING]` flags — metric and period
- **Nick to fill out** placeholders — count by section
- Coverage gaps carried forward from Phase A

---

## Section Structure

### Section 1: Block Financial Overview
- Heading 1: `Block Financial Overview`
- Rule of 40 fact line (see special format below)
- GP headline fact line
- AOI headline fact line
- Heading 2: `Watchpoints`
- Placeholder: `[Nick to fill out — Watchpoints (key risks, opportunities, notable items)]` → red (#ea4335)

### Section 2: Gross Profit
- Heading 2: `Gross Profit`
- Block GP fact line
- Cash App GP fact line + sub-bullets (Actives, Inflows per active, Monetization rate)
  - Placeholder: `[Nick to fill out — Cash App gross profit drivers]` → red (#ea4335)
- Square GP fact line + sub-bullets (Global GPV, US GPV, International GPV)
  - Placeholder: `[Nick to fill out — Square gross profit drivers]` → red (#ea4335)
- Block Variable Profit fact line
  - Placeholder: `[Nick to fill out — Variable profit commentary]` → red (#ea4335)
- Heading 2: `Block P&L` → Block P&L table
- Heading 2: `People by Function` → People by Function table
- Heading 3: `Variable Profit & Acquisition Spend` → Variable Profit table

### Section 3: Topline Trends by Brand
- Heading 1: `Topline Trends by Brand`

**Cash App** (Heading 2):
- Cash App GP fact line
- Product fact lines: Borrow, Cash App Card, Actives, Inflows, Monetization rate
- Placeholder: `[Nick to fill out — Cash App topline narrative and product drivers]` → red (#ea4335)
- Cash App product GP table

**Square** (Heading 2):
- Global GPV, US GPV, International GPV fact lines
- Square GP fact line + product sub-bullets
- Placeholder: `[Nick to fill out — Square topline narrative and GPV drivers]` → red (#ea4335)
- Square GPV/GP table

**Other Brands** (Heading 2):
- TIDAL fact line
- Proto fact line
- Bitkey fact line
- Placeholder: `[Nick to fill out — Other Brands commentary]` → red (#ea4335)
- Other Brands table

### Section 4: Appendix
- Heading 1: `Appendix`
- Heading 2: `Appendix I: Standardized P&L Double Click View` → detailed cost breakdown table
- Heading 2: `Appendix II: Gross Profit Breakdown` → product-level GP comparison table

---

## Fact Line Formats

All formats inherit from the global recipe. MRP-specific additions:

**Monthly actuals (closed):**
```
[emoji][Metric] landed at [Value] in [Month] ([+/-]% YoY), [+/-Delta]% ([+/-$Delta]) [above/below] [Forecast]
```

**QTD pacing:**
```
[emoji][Metric] is pacing to [Value] in Q[N] ([+/-]% YoY), [+/-Delta]% ([+/-$Delta]) [above/below] [Forecast]
```

**Rule of 40 (special format):**
```
[emoji]Block achieved Rule of [X]% ([Y]% growth, [Z]% margin) in [Month], [+/-N] pts above/below the previous year and [+/-N] pts above/below [Forecast], with growth [+/-N] pts and margin [+/-N] pts above/below forecast. Based on [Month] QTD actuals and latest pacing for [next month], we now expect to achieve Rule of [X]% ([Y]% growth, [Z]% margin) in Q[N].
```

**GP headline (pacing for quarter):**
```
[emoji]Gross profit is expected to land at [QTD Value], [+/-Delta]% ([+/-$Delta]) [above/below] [Forecast], [+/-Delta]% ([+/-$Delta]) [above/below] consensus, and [+/-Delta]% ([+/-$Delta]) [above/below] our external guidance.
```
Omit consensus/guidance lines if data is unavailable. Do not estimate.

---

## Table Column Structures

**Block P&L Table**
Columns: `[Month YYYY]` header spanning; sub-columns: `Actual` | `YoY %` | `versus AP` | `QTD Pace¹` | `YoY %` | `versus AP`
Table negatives: parentheses — ($38M)

**People by Function Table**
Columns: `Actual [Prior Month]` | `Actual [Current Month]`

**Variable Profit & Acquisition Spend Table**
Columns: `[Month YYYY]` | `Actual` | `YoY Growth` | `versus AP`
Grouped by brand: Cash App → Square → Block Overall

**Cash App Product GP Table**
Columns: `[Month YYYY]` | `Actual` | `$ versus AP` | `% versus AP` | `YoY % Growth`

**Square GPV/GP Table**
Columns: `[Month YYYY]` | `Actual` | `$ vs. AP` | `% vs. AP` | `YoY % Growth`

**Appendix II: GP Breakdown Table**
Columns: `Actual [Prior Year Month]` | `Actual [Current Month]` | `AP [Current Month]` | `versus AP ($)`

---

## Metrics in Scope

**Block-level:** Block GP, AOI + margin, EBITDA + margin, Rule of 40 (growth + margin components), GAAP OI, Variable Operational Costs (total + P2P, risk loss, CS people, other variable), Acquisition Costs, Fixed Costs (total + product dev people, G&A people, software & cloud, other fixed), GAAP OpEx, Total FTEs

**Cash App:** Cash App GP, Monthly Actives, Inflows per active (ex Commerce), Monetization rate (incl. CAP), Variable Profit + margin, Acquisition costs; product GP: Core Cash App, Cash App Card, Instant Deposit, Borrow, Bitcoin Buy/Sell, Commerce (total + CAP + ex-CAP), Cash App Pay, and others

**Square:** Square GP, Global GPV, US GPV, International GPV, Variable Profit + margin, Acquisition costs; product GP: US Payments, International Payments, SaaS, Banking (Loans + Business Banking), Hardware

**Other Brands:** TIDAL GP, Proto GP, Bitkey GP

**People:** Total FTEs, FTEs by function (Business, Customer Operations, Design, Engineering, Foundational, Hardware, Risk, Risk Operations, Sales)

---

## What This Agent Does NOT Do
- Fill in drivers, narrative, watchpoints, or explanations — that is Nick's job
- Estimate or infer missing data
- Override any global recipe rule
- Proceed to Phase B without Nick's explicit confirmation
- Self-trigger or run automatically
