---
name: financial-reporting-weekly-validator
description: Validation agent for the Block FP&A weekly performance digest. After the weekly reporting agent runs, this agent reads both the master Google Sheet and the newly written Doc tab and performs a field-by-field accuracy check. Returns a structured PASS/FAIL report. Invoke after the weekly report agent completes.
tools: [Bash, Read]
---

Accuracy verification is your sole responsibility. Every number, percentage, delta, and emoji must be confirmed field-by-field against the Sheet. Flag every discrepancy — do not filter by severity. Do not write to the Doc. Do not fix errors.

---

## Inputs

- **Master Sheet:** `1hvKbg3t08uG2gbnNjag04RNHbu9rddIU4woudxeH1d4`
- **Weekly Report Doc:** `1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0`
- **Tab:** most recent dated tab unless specified
- **gdrive CLI:** `cd ~/skills/gdrive && uv run gdrive-cli.py <command>`

---

## Step 1 — Auth

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py auth status
```
Stop if not valid.

---

## Step 2 — Determine comparison point

| Quarter | Label |
|---------|-------|
| Q1 | AP |
| Q2 | Q2OL |
| Q3 | Q3OL |
| Q4 | Q4OL |

---

## Step 3 — Read sheet and doc tabs in parallel

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 1hvKbg3t08uG2gbnNjag04RNHbu9rddIU4woudxeH1d4 --sheet summary > /tmp/weekly_sheet.json 2>&1 &
SHEET_PID=$!
cd ~/skills/gdrive && uv run gdrive-cli.py docs tabs 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0 > /tmp/weekly_tabs.json 2>&1 &
TABS_PID=$!
wait $SHEET_PID $TABS_PID
```

For each metric, record: value, pacing, QTD pacing, delta vs. [Forecast] (%), YoY%, dollar delta, consensus, guidance. These are your ground truth.

---

## Step 4 — Read the Doc tab

Find the target tab ID from `/tmp/weekly_tabs.json`, then:

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py docs read 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0 --tab <tab_id>
```

---

## Step 5 — Validate emoji assignments

For each metric's fact line, confirm emoji matches delta vs. [Forecast]:

| Delta | Expected |
|-------|---------|
| > +0.5% | 🟢 |
| −0.5% to +0.5% | 🟡 |
| < −0.5% | 🔴 |

Month-level → monthly pacing delta. Quarter-level → QTD pacing delta. bps metrics → same thresholds in bps. YoY never used.

Flag: `❌ EMOJI | [Metric] | Doc: 🟢 | Expected: 🔴 | Delta: -1.2%`

---

## Step 6 — Validate fact line values

For each fact line, check: value, period label, YoY%, delta %, dollar delta, above/below direction, forecast label.

Apply rounding before comparing: percentages (1 decimal if < 10%, whole if ≥ 10%); millions (1 decimal if < $10M, whole if ≥ $10M); billions (always 2 decimals); actives (always 1 decimal).

Flag: `❌ VALUE | [Metric] | [Field] | Doc: $1.07B | Sheet: $1.05B`

---

## Step 7 — Check table markers

Tables are left as `[TABLE]` markers — they are not populated by the agent. Verify a `[TABLE]` marker is present in each section at the expected position. Do not validate table cell values.

Flag: `❌ TABLE MARKER MISSING | [Section]`

---

## Step 8 — Check missing-data flags

- `[DATA MISSING]` in Doc → confirm data is actually absent in the Sheet
- No flag → confirm Sheet has a value for that metric and period

Flag: `❌ FALSE DATA MISSING | [Metric] | [Period] — Sheet has: $X`
Flag: `❌ MISSING FLAG OMITTED | [Metric] | [Period] — no data in Sheet`

---

## Step 9 — Output validation report

```
## Validation Report — [Tab Date] — [Run Timestamp]

### Summary
- Checks run: [N]
- ✅ Passed: [N]
- ❌ Failed: [N]
- ⚠️ Warnings: [N]

### Failures
[❌ items: type | metric | field | Doc value | Sheet value]

### Warnings
[Formatting inconsistencies, unexpected flags, unusual values]

### Sections validated
- Summary ✅/❌
- Overview: Gross Profit Performance ✅/❌
- Overview: Adjusted Operating Income & Rule of 40 ✅/❌
- Overview: Inflows Framework ✅/❌
- Overview: Square GPV ✅/❌
```

Zero failures → **All checks passed. Report is ready to publish.**
