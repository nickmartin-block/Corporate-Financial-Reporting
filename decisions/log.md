# Decision Log

Append-only. When a meaningful decision is made, log it here.

Format: [YYYY-MM-DD] DECISION: ... | REASONING: ... | CONTEXT: ...

---

[2026-03-13] DECISION: Weekly report sub-agent will create a new dated tab in the existing Google Doc each week (e.g., '3/10'), using prior week tabs as structural reference | REASONING: All prior reports live as tabs in the same Doc; reusing that pattern keeps the workflow consistent and gives the agent built-in examples without needing separate reference files | CONTEXT: Architecture planning session; Mac + Google Workspace MCP pending before build can start

[2026-03-13] DECISION: Weekly report agent scope = populate fact lines and tables only; leave `[DRI to include context]` placeholders for drivers and narrative | REASONING: Nick owns the "so what" — agent should never infer or fabricate context; clean separation of automated population vs. human interpretation | CONTEXT: Aligns with global recipe's "report numbers only" mandate

[2026-03-13] DECISION: Start automation with the weekly report (not MRP or board report) | REASONING: Highest frequency, most repetitive — fastest time-to-value and best forcing function to get the data pipeline right before tackling more complex deliverables | CONTEXT: Phase 1 scope decision

[2026-03-16] DECISION: MRP agent uses Block Data MCP as its data source (not a Google Sheet) and runs a two-phase workflow: Phase A = coverage check (map MRP metrics against MCP availability, surface gaps), Phase B = population (after Nick confirms) | REASONING: Block Data MCP provides governed, trusted metrics without requiring Nick to maintain a separate master Sheet; the coverage check surfaces data gaps before population begins so Nick can request missing metrics via the Linear intake form rather than discovering gaps mid-run | CONTEXT: MRP is significantly more complex than the weekly (full P&L, product-level GP breakdowns, headcount by function, brand narratives, two appendix tables); sourcing from MCP also creates a single source of truth across reporting deliverables

[2026-03-16] DECISION: MRP creates a fresh Google Doc each month (not a tab in an existing Doc) | REASONING: MRP is a standalone monthly deliverable with its own distribution — unlike the weekly digest which lives as dated tabs in a shared rolling Doc; a new Doc per month matches the existing MRP convention (confirmed from February 2026 MRP reference doc) | CONTEXT: Consistent with how Nick currently produces MRPs manually
