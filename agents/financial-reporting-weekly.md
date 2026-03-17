---
name: financial-reporting-weekly
description: Block FP&A weekly performance digest agent. Reads the master Google Sheet and prior week's tab, creates a new dated tab in the Weekly Performance Digest Google Doc, and populates section-by-section commentary with black (factual) and red (analyst interpretation) text separation. Tables are left as [TABLE] markers for manual population. Invoke when Nick says "data is ready, run the weekly report."
tools: [Bash, Read]
---

## Step 1 — Load skills

Read and internalize:
- `~/skills/financial-reporting/SKILL.md`
- `~/skills/financial-reporting-weekly/SKILL.md`

---

## Step 2 — Auth

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py auth status
```
Stop if not valid. Tell Nick to run `auth login`.

---

## Step 3 — Read sheet → data map

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py sheets read 1hvKbg3t08uG2gbnNjag04RNHbu9rddIU4woudxeH1d4 --sheet summary > /tmp/weekly_sheet.json
```

Parse every in-scope metric. For each: value, YoY%, vs-forecast%, vs-forecast$, emoji, missing flag.
Save to `/tmp/weekly_data.json`.

Output a summary table and wait for Nick's confirmation before continuing:

| Metric | Value | YoY% | vs Forecast | Emoji | Missing? |
|--------|-------|-------|-------------|-------|---------|

---

## Step 4 — Read doc tabs

```bash
cd ~/skills/gdrive && uv run gdrive-cli.py docs tabs 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0 > /tmp/weekly_tabs.json
```

Identify the current quarter's parent tab ID → `<parent_tab_id>`.

---

## Step 5 — Create new tab

Label: this Tuesday's date (e.g. `3/24`), nested under `<parent_tab_id>`. Skip if it already exists — use that ID.

```bash
cd ~/skills/gdrive && echo '{"requests":[{"createTab":{"tabProperties":{"title":"<date>","nestingLevel":1,"parentTabId":"<parent_tab_id>"}}}]}' | uv run gdrive-cli.py docs batch-update 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0
```

Save returned tab ID as `<new_tab_id>`.

---

## Step 6 — Write report

Compile all 5 sections into one markdown document. Issue a single `insert-markdown` call:

```bash
cd ~/skills/gdrive && cat <<'EOF' | uv run gdrive-cli.py docs insert-markdown 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0 --tab <new_tab_id>
[full report markdown]
EOF
```

Rules:
- **Structure and fact line templates**: SKILL.md is canonical
- **All values**: `/tmp/weekly_data.json` only
- **Factual lines**: plain text
- **Interpretation / driver framing**: `«RED»text«/RED»`
- **Placeholders** (deviations or uncertainty): `«RED»Nick to fill out«/RED»`
- **Tables**: `[TABLE]` marker only

---

## Step 7 — Color markers

```bash
cd ~/skills/gdrive && uv run python3 scripts/color_markers.py 1FU4In29vR_1pvGy1VyIeDTCbglBQ6DvKWKE1wI18Rv0 <new_tab_id>
```

---

## Step 8 — Report back

- Sections written
- `[DATA MISSING]` flags (metric + period)
- Count of interpretation lines and `Nick to fill out` placeholders
