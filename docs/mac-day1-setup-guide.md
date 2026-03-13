# Mac Day 1 Setup Guide

Step-by-step instructions to go from a fresh Mac to a fully connected Claude Code environment with Google Workspace MCP — ready to run the weekly report agent.

---

## Overview

Four phases, done in order:
1. **Mac environment** — Install the tools Claude Code needs
2. **Clone the repo** — Get the workspace on your Mac
3. **Google Cloud + MCP** — Connect Claude to Google Drive, Sheets, and Docs
4. **Test run** — Verify everything works end-to-end

Total time: ~45–60 minutes (most of it is waiting for installs and OAuth)

---

## Phase 1 — Mac Environment Setup

### Step 1: Install Homebrew (if not already installed)
Homebrew is the standard Mac package manager. Check if it's there:
```bash
brew --version
```
If not found, install it:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Follow the prompts. When done, run the two `export PATH` commands it outputs at the end (copy/paste them into Terminal).

---

### Step 2: Install Node.js
Node.js is required to run the Google Workspace MCP server.
```bash
brew install node
```
Verify:
```bash
node --version   # should show v18 or higher
npm --version
```

---

### Step 3: Install Claude Code
```bash
npm install -g @anthropic-ai/claude-code
```
Verify:
```bash
claude --version
```
If the `claude` command isn't found after install, you may need to add npm's global bin to your PATH:
```bash
echo 'export PATH="$(npm prefix -g)/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```

---

### Step 4: Install VS Code (if not already installed)
Download from https://code.visualstudio.com and drag to Applications.

Install the Claude Code VS Code extension from the Extensions panel (search "Claude Code").

---

## Phase 2 — Clone the Repo

### Step 5: Clone the Financial Reporting repo
```bash
git clone https://github.com/nickmartin-block/Financial-Reporting.git
cd Financial-Reporting
```

### Step 6: Open in Claude Code
```bash
claude
```
Or open VS Code in that folder:
```bash
code .
```
Then use the Claude Code extension from the sidebar.

---

## Phase 3 — Google Cloud + MCP Setup

This is a one-time setup. The goal is to give Claude Code read/write access to your Google Drive, Sheets, and Docs.

### Step 7: Create a Google Cloud Project

1. Go to https://console.cloud.google.com
2. Click the project dropdown at the top → **New Project**
3. Name it something like `Claude MCP` → **Create**
4. Make sure the new project is selected in the dropdown before continuing

---

### Step 8: Enable the required APIs

1. In the left sidebar, go to **APIs & Services > Library**
2. Search for and enable each of these (one at a time):
   - **Google Drive API** → Enable
   - **Google Sheets API** → Enable
   - **Google Docs API** → Enable

---

### Step 9: Create OAuth 2.0 credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted to configure the consent screen first:
   - Choose **External**
   - Fill in App name (e.g., `Claude MCP`), your email for support and developer contact
   - Click Save and Continue through all screens (no need to add scopes manually here)
   - On the final screen, click **Back to Dashboard**
4. Back at Credentials → **+ Create Credentials > OAuth client ID**
5. Application type: **Desktop app**
6. Name: `Claude MCP Desktop`
7. Click **Create**
8. Click **Download JSON** — this is your `credentials.json`

---

### Step 10: Store credentials.json

Move the downloaded file to a safe location:
```bash
mkdir -p ~/.config/google-workspace-mcp
mv ~/Downloads/client_secret_*.json ~/.config/google-workspace-mcp/credentials.json
```

Set an environment variable so the MCP server can find it:
```bash
echo 'export GOOGLE_CREDENTIALS_PATH="$HOME/.config/google-workspace-mcp/credentials.json"' >> ~/.zshrc
source ~/.zshrc
```

---

### Step 11: Add the MCP server to Claude Code

Make sure you're in the Financial-Reporting project folder, then run:
```bash
claude mcp add google-workspace \
  --transport stdio \
  -- npx -y @presto-ai/google-workspace-mcp
```

This adds the MCP server to your project-scoped config. It will be active whenever you open this project in Claude Code.

---

### Step 12: Complete Google OAuth (first-run auth)

Start a Claude Code session in the project folder:
```bash
claude
```

A browser window will open asking you to authorize access to your Google account.
- Sign in with your Block Google account
- Grant the requested permissions (Drive, Sheets, Docs read/write)
- You'll see a confirmation screen — close the browser tab and return to the terminal

OAuth tokens are saved automatically. You won't need to re-auth unless you revoke access or switch machines.

---

### Step 13: Verify MCP is connected

In the Claude Code session, run:
```
/mcp
```
You should see `google-workspace` listed as an active server with a green status.

If it's not showing, troubleshoot:
```bash
# Check that npx can run the MCP server manually
npx -y @presto-ai/google-workspace-mcp --help
```

---

## Phase 4 — Test Run

### Step 14: Gather your file IDs

Before running the agent, have these ready:
- **Master Sheet file ID** — open the Google Sheet in your browser; the ID is the string between `/d/` and `/edit` in the URL
  ```
  docs.google.com/spreadsheets/d/[THIS_IS_THE_FILE_ID]/edit
  ```
- **Weekly report Doc file ID** — same pattern from the Google Doc URL
  ```
  docs.google.com/document/d/[THIS_IS_THE_FILE_ID]/edit
  ```
- **Which Sheet tab** has the clean summary data (vs. model build-up tabs)

---

### Step 15: Run the weekly report kickoff prompt

Open `docs/weekly-report-plan.md` in this repo. Copy the kickoff prompt from the **Mac Day 1 Kickoff Prompt** section.

Replace the two placeholders before pasting:
- `[SHEET_FILE_ID]` → your master Sheet file ID
- `[DOC_FILE_ID]` → your weekly report Doc file ID

Paste the full prompt into Claude Code and send it.

Claude will:
1. Load the global recipe (`SKILL.md`)
2. Read the master Sheet
3. Read the weekly report Doc (reviewing prior week tabs for reference)
4. Create a new tab for this week
5. Populate tables and fact lines
6. Report back what's populated and what's missing

---

### Step 16: Review the output

Open the Google Doc in your browser and check:
- [ ] New tab created with today's Tuesday date (e.g., '3/18')
- [ ] Tables match the Sheet values exactly
- [ ] Fact lines follow the format: `"[Metric] is pacing to $X (+Y% YoY), +Z% (+$A) above AP"`
- [ ] `[DRI to include context]` placeholders appear after any line needing drivers
- [ ] `[DATA MISSING: {metric} | {period}]` appears for any gaps
- [ ] No narrative or driver text was generated by the agent

If anything looks off, note what's wrong and share the example with Claude in the same session — it can self-correct.

---

## Ongoing Weekly Workflow (Every Tuesday)

Once the setup is done, every week is just three steps:

1. **Finalize data** — compile and validate the master Google Sheet as usual
2. **Trigger the agent** — tell Claude: *"data is ready, run the weekly report"*
3. **Review and complete** — open the Doc, fill in the `[DRI to include context]` placeholders, then share the link via Slack

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `claude` command not found | Add npm global bin to PATH (see Step 3) |
| MCP server not listed in `/mcp` | Re-run the `claude mcp add` command from Step 11 |
| OAuth browser window doesn't open | Run `npx -y @presto-ai/google-workspace-mcp` manually to trigger auth |
| Agent can't read the Sheet | Confirm the file ID is correct; confirm your Google account has access to the file |
| Agent creates wrong tab name | Verify Tuesday's date format — should be M/DD (e.g., '3/18', not '03/18') |
| `credentials.json` not found | Confirm the `GOOGLE_CREDENTIALS_PATH` env var is set correctly (`echo $GOOGLE_CREDENTIALS_PATH`) |
