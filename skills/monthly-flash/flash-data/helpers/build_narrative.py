#!/usr/bin/env python3
"""Build the monthly flash narrative markdown from a /flash-data packet.

Consumes /tmp/flash_out_{month}.json (output of flash_data.py). Produces a
markdown file ready to insert into the Google Doc Claude tab.

Driver attribution rules:
  - Driver inclusion: abs(line_delta vs OL) >= $2M OR >= 5% of bucket total
  - Top 2-3 per bucket by abs delta, ranked desc
  - "Corp to include context" appended when bucket variance >= $20M abs OR >= 10%
  - nm rule passes through from helper formatting (variances > 1000% display as nm)

Usage:
  python3 build_narrative.py --packet /tmp/apr26_out.json --period "Apr'26" \
    --ol-label "Q2OL" --output /path/to/flash_2026_04.md
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import date
from typing import Any

# Shared formatting helper — keep precision rule + table populator in sync.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from populate_flash_table import reformat_variance  # noqa: E402

DRIVER_INCLUSION_DOLLAR_MIN = 2_000_000
DRIVER_INCLUSION_PCT_MIN = 0.05  # 5% of bucket
CORP_CONTEXT_DOLLAR_MIN = 20_000_000
CORP_CONTEXT_PCT_MIN = 0.10  # 10% variance

# Variance precision rule: |magnitude| ≤ 10 → 1 decimal; > 10 → integer.
# Applied to $M / % / pts variances. Mirrors populate_flash_table.reformat_variance.
PRECISION_RULE_THRESHOLD = 10.0


MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def parse_period(period: str) -> tuple[str, str, int, int]:
    """Parse "Apr'26" → (month name, prior month name, month num, year)."""
    parts = period.replace("'", "").strip().split()
    mon_abbr = parts[0][:3]
    year_short = int(parts[0][-2:])
    full_year = 2000 + year_short
    abbr_to_num = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                   "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    mnum = abbr_to_num[mon_abbr]
    prior_num = mnum - 1 if mnum > 1 else 12
    return MONTH_NAMES[mnum], MONTH_NAMES[prior_num], mnum, full_year


def get_row(table: list[list[Any]], row_offset: int) -> list[Any]:
    """Return a row's 7 data cells (skipping the label) from a 28×8 or 37×7 table."""
    return table[row_offset][1:]


def cell(row: list[Any], col: int) -> str:
    """Safe getter for a formatted cell."""
    v = row[col] if col < len(row) else ""
    return str(v) if v not in (None, "") else ""


def to_narrative_sign(s: str) -> str:
    """Convert a reformatted variance to narrative form:
    - "(X)" → "-X"
    - "X" (no leading sign) → "+X"
    - "+X" / "-X" → unchanged
    Empty / neutral tokens pass through.
    """
    s = s.strip()
    if not s or s in ("--", "nm", "N/A", "n/a", "NA"):
        return s
    if s.startswith("(") and s.endswith(")"):
        return "-" + s[1:-1]
    if s.startswith("+") or s.startswith("-"):
        return s
    return "+" + s


def combine(pct: str, dollar: str) -> str:
    """Flash format: % first, $ in parens. "+2.4%" + "+$24M" → "+2.4% (+$24M)".

    Order is pct first (per Nick's saved feedback). Either arg can be empty.
    """
    if not pct and not dollar:
        return ""
    if not dollar:
        return pct
    if not pct:
        return dollar
    return f"{pct} ({dollar})"


def variance_phrase(pct: str, dollar: str, bench: str) -> str:
    """Build "+X% (+$Y) above bench" or "-X% (-$Y) below bench".
    Direction inferred from the sign of pct (falls back to dollar). Empty → "vs. {bench}".
    """
    body = combine(pct, dollar)
    if not body:
        return f"vs. {bench}"
    sign_indicator = pct or dollar
    is_neg = sign_indicator.startswith("-") or sign_indicator.startswith("(")
    direction = "below" if is_neg else "above"
    return f"{body} {direction} {bench}"


# Variable / Acquisition / Fixed leaf line items keyed by display name + raw_derived prefix
VARIABLE_LEAVES = [
    ("P2P", "opex_p2p"),
    ("Risk Loss", "opex_risk_loss"),
    ("Card Issuance", "opex_card_issuance"),
    ("Warehouse Financing", "opex_warehouse_financing"),
    ("Hardware Logistics", "opex_hw_logistics"),
    ("Bad Debt Expense", "opex_bad_debt"),
    ("Customer Reimbursements", "opex_customer_reimbursements"),
]
ACQUISITION_LEAVES = [
    ("Marketing", "opex_marketing"),
    ("Onboarding Costs", "opex_onboarding"),
    ("Partnership Fees", "opex_partnership_fees"),
    ("Reader Expense", "opex_reader_expense"),
    ("Sales & Marketing People", "opex_sales_marketing_people"),
]
FIXED_LEAVES = [
    ("Product Development People", "opex_prod_dev_people"),
    ("G&A People (ex. CS)", "opex_ga_people_ex_cs"),
    ("Customer Support People", "opex_customer_support_people"),
    ("Software", "opex_software"),
    ("Cloud fees", "opex_cloud_fees"),
    ("Taxes, Insurance & Other Corp", "opex_taxes_insurance"),
    ("Legal fees", "opex_legal_fees"),
    ("Other Professional Services", "opex_other_prof_services"),
    ("Rent, Facilities, Equipment", "opex_rent_facilities"),
    ("Travel & Entertainment", "opex_travel_entertainment"),
    ("Hardware Production Costs", "opex_hw_production"),
    ("Non-Cash expenses (ex. SBC)", "opex_non_cash_ex_sbc"),
]


def _half_up(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def fmt_driver_delta(d: float) -> str:
    """Format a $ delta for driver call-out per the ±10 rule.
    Explicit +/- sign, no parens for negatives (per Flash format).
    - |Δ| ≤ $10M → 1 decimal in $M (e.g. "+$5.8M")
    - |Δ| >  $10M → integer in $M  (e.g. "+$18M", "-$26M")
    - |Δ| < $1M  → $K integer      (e.g. "+$199K") — preserves clarity for tiny drivers
    """
    abs_v = abs(d)
    sign = "+" if d >= 0 else "-"
    if abs_v < 1_000_000:
        return f"{sign}${_half_up(abs_v / 1_000)}K"
    millions = abs_v / 1_000_000
    if millions <= PRECISION_RULE_THRESHOLD:
        return f"{sign}${millions:.1f}M"
    return f"{sign}${_half_up(millions)}M"


def fmt_driver_pct(p: float) -> str:
    """Format a % delta per the ±10 rule. Explicit +/- sign.
    - |p| ≤ 10%  → 1 decimal (e.g. "+5.8%")
    - |p| >  10% → integer   (e.g. "+29%", "-26%")
    """
    pct = p * 100.0
    sign = "+" if pct >= 0 else "-"
    abs_pct = abs(pct)
    if abs_pct <= PRECISION_RULE_THRESHOLD:
        return f"{sign}{abs_pct:.1f}%"
    return f"{sign}{_half_up(abs_pct)}%"


def force_signed(s: str) -> str:
    """Force an explicit + prefix on a positive variance/rate (e.g., '22.6%' → '+22.6%').
    Leaves '--' / 'nm' / empty alone. Used on YoY rates which the sheet emits as positive
    bare numbers but Flash format wants signed.
    """
    s = s.strip()
    if not s or s in ("--", "nm", "N/A", "n/a", "NA"):
        return s
    if s.startswith(("+", "-", "(")):
        # parens means negative → convert to -X
        if s.startswith("(") and s.endswith(")"):
            return "-" + s[1:-1]
        return s
    return "+" + s


def margin_pct(numerator: float | None, denominator: float | None) -> str:
    """Compute margin as numerator/denominator, format per ±10 rule. Returns '' if undefined."""
    if numerator is None or denominator in (None, 0):
        return ""
    m = numerator / denominator * 100.0
    abs_m = abs(m)
    sign = "" if m >= 0 else "-"  # margins don't get explicit "+"; negative gets "-"
    if abs_m <= PRECISION_RULE_THRESHOLD:
        return f"{sign}{abs_m:.1f}%"
    return f"{sign}{_half_up(abs_m)}%"


def pick_drivers(raw: dict, bucket_total_actual: float, leaves: list[tuple[str, str]]) -> list[dict]:
    """Compute deltas for each leaf and pick top 2-3 that pass materiality."""
    candidates = []
    for label, prefix in leaves:
        actual = raw.get(f"{prefix}_actual")
        ol = raw.get(f"{prefix}_ol")
        if actual is None or ol is None:
            continue
        delta = actual - ol
        pct = delta / ol if ol else 0
        candidates.append({
            "label": label,
            "delta": delta,
            "pct": pct,
            "abs": abs(delta),
        })
    # Filter by materiality
    filtered = [
        c for c in candidates
        if c["abs"] >= DRIVER_INCLUSION_DOLLAR_MIN
        or (bucket_total_actual and c["abs"] / bucket_total_actual >= DRIVER_INCLUSION_PCT_MIN)
    ]
    filtered.sort(key=lambda c: c["abs"], reverse=True)
    return filtered[:3]


def bucket_commentary(bucket_name: str, raw: dict, actual_key: str, ol_key: str,
                      leaves: list[tuple[str, str]], ol_label: str) -> str:
    """Build the bullet line for one V/A/F bucket including driver commentary."""
    actual = raw.get(actual_key)
    ol = raw.get(ol_key)
    if actual is None:
        return f"- **{bucket_name}** were unavailable for this period."

    bucket_delta = actual - ol if ol is not None else None
    bucket_pct = bucket_delta / ol if (bucket_delta is not None and ol) else None

    # Format the headline. Bucket Actuals are large ($MM+) and aren't variances,
    # so they pass through as integer $M. Variance follows Flash format:
    # "+X% (+$Y) above bench" / "-X% (-$Y) below bench" — pct first, $ in parens.
    actual_fmt = f"${_half_up(actual/1_000_000)}M"
    if bucket_delta is not None:
        delta_fmt = fmt_driver_delta(bucket_delta)
        pct_fmt = fmt_driver_pct(bucket_pct) if bucket_pct is not None else ""
        direction = "below" if bucket_delta < 0 else "above"
        if pct_fmt and delta_fmt:
            variance = f"{pct_fmt} ({delta_fmt})"
        else:
            variance = pct_fmt or delta_fmt
        headline = f"**{bucket_name}** were {actual_fmt}, {variance} {direction} {ol_label}"
    else:
        headline = f"**{bucket_name}** were {actual_fmt}"

    # Driver call-outs
    drivers = pick_drivers(raw, actual, leaves) if actual else []
    if drivers:
        # Separate positive / negative for "partially offset by" framing
        bucket_dir = 1 if bucket_delta and bucket_delta >= 0 else -1
        same_dir = [d for d in drivers if (d["delta"] >= 0) == (bucket_dir > 0)]
        opp_dir = [d for d in drivers if (d["delta"] >= 0) != (bucket_dir > 0)]

        same_strs = [f"{d['label']} ({fmt_driver_delta(d['delta'])} / {fmt_driver_pct(d['pct'])})"
                     for d in same_dir]
        opp_strs = [f"{d['label']} ({fmt_driver_delta(d['delta'])} / {fmt_driver_pct(d['pct'])})"
                    for d in opp_dir]

        parts = []
        if same_strs:
            parts.append("driven by " + ", ".join(same_strs))
        if opp_strs:
            parts.append("partially offset by " + ", ".join(opp_strs))
        driver_phrase = "; ".join(parts) if parts else ""
        if driver_phrase:
            headline += f", {driver_phrase}"

    # Corp-context flag
    if bucket_delta is not None:
        corp_flag = (
            abs(bucket_delta) >= CORP_CONTEXT_DOLLAR_MIN
            or (bucket_pct is not None and abs(bucket_pct) >= CORP_CONTEXT_PCT_MIN)
        )
        if corp_flag:
            headline += ". **Corp to include context.**"
        else:
            headline += "."
    else:
        headline += "."

    return "- " + headline


def format_pct(v: float | None, *, signed: bool = False) -> str:
    if v is None:
        return ""
    pct = v * 100
    if signed:
        return f"{'+' if pct >= 0 else '-'}{abs(pct):.1f}%"
    return f"{abs(pct):.1f}%" + ("" if pct >= 0 else " (negative)")


def build_narrative(packet: dict, period: str, ol_label: str, ol_year: int) -> str:
    """Construct the full markdown narrative."""
    raw = packet["raw_derived"]
    flash_t = packet["flash_table_formatted"]
    month, prior_month, _, year = parse_period(period)

    # Convenience accessors for formatted flash cells (skipping label col)
    # Row offsets (0-indexed in the 28-row table)
    F = {
        "cash_actives": 2, "cash_inflows_pa": 3, "commerce_gmv": 4,
        "sq_gpv": 5, "sq_us": 6, "sq_intl": 7,
        "block_gp": 10, "ca_gp": 11,
        "ca_commerce": 12, "ca_borrow": 13, "ca_card": 14, "ca_id": 15, "ca_bnpl": 16,
        "sq_gp": 17, "sq_us_pmt": 18, "sq_intl_pmt": 19, "sq_banking": 20, "sq_saas": 21, "sq_hw": 22,
        "tidal": 23, "proto": 24,
        "adj_opex": 25, "adj_oi": 26, "r40": 27,
    }
    # Col indices (after stripping label): 0=Actual, 1=vs OL $, 2=vs OL %, 3=vs AP $, 4=vs AP %, 5=YoY, 6=PriorMoYoY
    A, OL_D, OL_P, AP_D, AP_P, YOY, PMYOY = 0, 1, 2, 3, 4, 5, 6

    def f(metric: str, col: int) -> str:
        return cell(get_row(flash_t, F[metric]), col)

    # Variance cols: ±10 precision rule (reformat_variance) THEN convert parens → +/- sign
    # for narrative form. YoY cols: just force "+" prefix on positives.
    VARIANCE_COLS = {OL_D, OL_P, AP_D, AP_P}
    YOY_COLS = {YOY, PMYOY}

    def v(metric: str, col: int) -> str:
        """Narrative-form variance value: signed +/-, precision rule applied."""
        raw_val = f(metric, col)
        if col in VARIANCE_COLS:
            return to_narrative_sign(reformat_variance(raw_val))
        if col in YOY_COLS:
            return force_signed(raw_val)
        return raw_val

    # Brand bridge — short form: "(Cash App +$X, Square -$Y, Other Brands +$Z)"
    def _delta_ap(metric: str) -> float:
        actual = raw.get(f"{metric}_actual")
        ap = raw.get(f"{metric}_ap")
        if actual is None or ap is None:
            return 0.0
        return actual - ap

    ca_ap_d_raw = _delta_ap("cash_app_gp")
    sq_ap_d_raw = _delta_ap("square_gp")
    tidal_ap_d_raw = _delta_ap("tidal_gp")
    proto_ap_d_raw = _delta_ap("proto_gp")
    other_brands_raw = tidal_ap_d_raw + proto_ap_d_raw
    brand_bridge = (
        f"Cash App {fmt_driver_delta(ca_ap_d_raw)}, "
        f"Square {fmt_driver_delta(sq_ap_d_raw)}, "
        f"Other Brands {fmt_driver_delta(other_brands_raw)}"
    )

    # AOI margin (vs Block GP, per Flash convention)
    aoi_margin = margin_pct(raw.get("adj_oi_actual"), raw.get("block_gp_actual"))

    # Cash App sub-product outperformance
    ca_subs = [
        ("Commerce", raw.get("commerce_gp_actual", 0) - raw.get("commerce_gp_ap", 0)),
        ("Borrow", raw.get("borrow_gp_actual", 0) - raw.get("borrow_gp_ap", 0)),
        ("Cash App Card", raw.get("cash_app_card_gp_actual", 0) - raw.get("cash_app_card_gp_ap", 0)),
        ("Instant Deposit", raw.get("instant_deposit_gp_actual", 0) - raw.get("instant_deposit_gp_ap", 0)),
        ("Post-Purchase BNPL", raw.get("post_purchase_bnpl_gp_actual", 0) - raw.get("post_purchase_bnpl_gp_ap", 0)),
    ]
    ca_pos = sorted([s for s in ca_subs if s[1] > 0], key=lambda s: s[1], reverse=True)
    ca_neg = sorted([s for s in ca_subs if s[1] < 0], key=lambda s: s[1])

    def fmt_sub(items):
        return ", ".join(f"{name} ({fmt_driver_delta(d)})" for name, d in items)

    ca_outperf = []
    if ca_pos:
        ca_outperf.append(fmt_sub(ca_pos))
    if ca_neg:
        ca_outperf.append("partially offset by " + fmt_sub(ca_neg))
    ca_outperf_phrase = "; ".join(ca_outperf)

    # Square sub-product outperformance
    sq_subs = [
        ("US Payments", raw.get("us_payments_gp_actual", 0) - raw.get("us_payments_gp_ap", 0)),
        ("INTL Payments", raw.get("intl_payments_gp_actual", 0) - raw.get("intl_payments_gp_ap", 0)),
        ("Banking", raw.get("banking_gp_actual", 0) - raw.get("banking_gp_ap", 0)),
        ("SaaS", raw.get("saas_gp_actual", 0) - raw.get("saas_gp_ap", 0)),
        ("Hardware", raw.get("hardware_gp_actual", 0) - raw.get("hardware_gp_ap", 0)),
    ]
    sq_pos = sorted([s for s in sq_subs if s[1] > 0], key=lambda s: s[1], reverse=True)
    sq_neg = sorted([s for s in sq_subs if s[1] < 0], key=lambda s: s[1])

    sq_outperf = []
    if sq_pos:
        sq_outperf.append(fmt_sub(sq_pos))
    if sq_neg:
        sq_outperf.append("partially offset by " + fmt_sub(sq_neg))
    sq_outperf_phrase = "; ".join(sq_outperf)

    # V/A/F bucket commentary
    var_bullet = bucket_commentary("Variable costs", raw, "opex_total_variable_actual",
                                    "opex_total_variable_ol", VARIABLE_LEAVES, ol_label)
    acq_bullet = bucket_commentary("Acquisition costs", raw, "opex_total_acquisition_actual",
                                    "opex_total_acquisition_ol", ACQUISITION_LEAVES, ol_label)
    # Fixed total is derived from total - var - acq (see flash_data.py)
    fix_bullet = bucket_commentary("Fixed costs", raw, "opex_total_fixed_actual",
                                    "opex_total_fixed_ol", FIXED_LEAVES, ol_label)

    aoi_margin_phrase = f" ({aoi_margin} margin)" if aoi_margin else ""

    md = f"""# Block Topline Flash: {month} {year}

*This flash report provides a preliminary view of month-end close results, with figures subject to further review and potential adjustment. This streamlined report includes minimal commentary, as a more comprehensive analysis of underlying drivers will be provided in the* ***Monthly Management Reporting Pack scheduled for [MRP DATE]***.

*Please note that the flash topline aligns with our externally reported guidelines, which include Cash App Pay Gross Profit within Cash App excluding Commerce. All comparisons reference {year} Annual Plan unless otherwise noted. Variances in charts are not color coded for amounts within +/- 1%, $0.5M, or YoY comparisons.*

## {month} {year} Summary

**Block gross profit** was {f("block_gp", A)} in {month}, growing {v("block_gp", YOY)} YoY ({v("block_gp", PMYOY)} in {prior_month}) and landing {variance_phrase(v("block_gp", AP_P), v("block_gp", AP_D), "AP")} ({brand_bridge}).

- **Cash App gross profit** for {month} was {f("ca_gp", A)}, growing {v("ca_gp", YOY)} YoY ({v("ca_gp", PMYOY)} in {prior_month}) and landing {variance_phrase(v("ca_gp", AP_P), v("ca_gp", AP_D), "AP")}. Outperformance vs. AP: {ca_outperf_phrase}.
    - **Commerce GMV** was {f("commerce_gmv", A)}, {variance_phrase(v("commerce_gmv", AP_P), v("commerce_gmv", AP_D), "AP")} and {v("commerce_gmv", YOY)} YoY ({v("commerce_gmv", PMYOY)} in {prior_month}).
    - **Cash App Actives** landed at {f("cash_actives", A)}, {variance_phrase(v("cash_actives", AP_P), v("cash_actives", AP_D), "AP")} and growing {v("cash_actives", YOY)} YoY ({v("cash_actives", PMYOY)} in {prior_month}).
    - **Cash App Inflows per Active** were {f("cash_inflows_pa", A)}, {variance_phrase(v("cash_inflows_pa", AP_P), v("cash_inflows_pa", AP_D), "AP")} and {v("cash_inflows_pa", YOY)} YoY ({v("cash_inflows_pa", PMYOY)} in {prior_month}).
- **Square gross profit** for {month} was {f("sq_gp", A)}, growing {v("sq_gp", YOY)} YoY ({v("sq_gp", PMYOY)} in {prior_month}) and landing {variance_phrase(v("sq_gp", AP_P), v("sq_gp", AP_D), "AP")}. Drivers: {sq_outperf_phrase}.
    - **Global GPV** was {f("sq_gpv", A)}, {variance_phrase(v("sq_gpv", AP_P), v("sq_gpv", AP_D), "AP")} and {v("sq_gpv", YOY)} YoY ({v("sq_gpv", PMYOY)} in {prior_month}).
    - **US GPV** was {f("sq_us", A)}, {variance_phrase(v("sq_us", AP_P), v("sq_us", AP_D), "AP")} and {v("sq_us", YOY)} YoY ({v("sq_us", PMYOY)} in {prior_month}).
    - **INTL GPV** was {f("sq_intl", A)}, {variance_phrase(v("sq_intl", AP_P), v("sq_intl", AP_D), "AP")} and {v("sq_intl", YOY)} YoY ({v("sq_intl", PMYOY)} in {prior_month}).
- **TIDAL gross profit** for {month} was {f("tidal", A)}, {v("tidal", YOY)} YoY ({v("tidal", PMYOY)} in {prior_month}) and landed {variance_phrase(v("tidal", AP_P), v("tidal", AP_D), "AP")}.
- **Proto gross profit** for {month} was {f("proto", A)}, and landed {variance_phrase(v("proto", AP_P), v("proto", AP_D), "AP")}.

**Adjusted Opex** for {month} was {f("adj_opex", A)}, {variance_phrase(v("adj_opex", OL_P), v("adj_opex", OL_D), ol_label)} and {v("adj_opex", YOY)} YoY ({v("adj_opex", PMYOY)} in {prior_month}).

{var_bullet}
{acq_bullet}
{fix_bullet}

**Adjusted Operating Income** landed at {f("adj_oi", A)} in {month}{aoi_margin_phrase}, {variance_phrase(v("adj_oi", AP_P), v("adj_oi", AP_D), "AP")} and {v("adj_oi", YOY)} YoY ({v("adj_oi", PMYOY)} in {prior_month}).

**{month} Rule of 40** was {f("r40", A)}, {variance_phrase(v("r40", AP_P), "", "AP")} and {v("r40", YOY)} YoY ({v("r40", PMYOY)} in {prior_month}).
"""

    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", required=True, help="Path to flash_out JSON packet")
    ap.add_argument("--period", required=True, help="Period e.g. Apr'26")
    ap.add_argument("--ol-label", required=True, help="Outlook scenario label e.g. Q2OL")
    ap.add_argument("--ol-year", type=int, default=None, help="Year for Annual Plan ref (default: derived from period)")
    ap.add_argument("--output", required=True, help="Path to write markdown")
    args = ap.parse_args()

    with open(args.packet) as f:
        packet = json.load(f)

    _, _, _, year = parse_period(args.period)
    ol_year = args.ol_year or year

    md = build_narrative(packet, args.period, args.ol_label, ol_year)

    with open(args.output, "w") as f:
        f.write(md)

    print(f"Wrote {args.output}")
    print(f"Lines: {md.count(chr(10))}")


if __name__ == "__main__":
    main()
