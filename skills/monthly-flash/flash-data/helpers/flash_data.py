#!/usr/bin/env python3
"""Flash-data derivations + formatting helper.

Consumed by /flash-data. Claude pulls raw values from BDM + Snowflake via MCP
and passes them in as a JSON dict. This helper computes derived rows
(Adj OpEx, Rule of 40, Inflows/Active, V/A/F bucket totals + deltas), applies
the nm rule for >1000% variances, and returns two value matrices ready to be
written to the brand reporting model sheet:

  - Flash table at MRP Charts & Tables!L400:S427
  - Standardized P&L at MRP Charts & Tables!L432:R468

Usage:
  python3 flash_data.py --input raw_apr26.json --period "Apr'26"
"""

from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any

NM_THRESHOLD = 10.0  # 1000%
EMPTY = ""


# -------------------- formatting --------------------

def fmt_actual(v: float | None, scale: str = "auto") -> str:
    """Currency/count formatter matching Flash convention.
       auto: scales to B/M based on magnitude
       count: actives in M (e.g., 58.3M)
       per_active: $XXX (no scaling)
       pct: percent with sign in parens for negatives
       rate: rate metric like "50%"
    """
    if v is None or v == EMPTY:
        return EMPTY
    if scale == "count":
        return f"{v / 1_000_000:.1f}M"
    if scale == "per_active":
        return f"${round(v):.0f}"
    if scale == "pct":
        return f"{v*100:.1f}%"
    # auto $ scaling
    abs_v = abs(v)
    if abs_v >= 1_000_000_000:
        out = f"${v/1_000_000_000:.2f}B"
    elif abs_v >= 10_000_000:
        out = f"${round(v/1_000_000):.0f}M"
    elif abs_v >= 100_000:
        out = f"${v/1_000_000:.1f}M"
    else:
        out = f"${v:,.0f}"
    if v < 0:
        out = "(" + out.replace("-", "") + ")"
    return out


def fmt_delta_dollar(v: float | None, with_dollar: bool = True) -> str:
    if v is None or v == EMPTY:
        return EMPTY
    abs_v = abs(v)
    prefix = "$" if with_dollar else ""
    if abs_v >= 1_000_000_000:
        s = f"{prefix}{abs_v/1_000_000_000:.2f}B"
    elif abs_v >= 10_000_000:
        s = f"{prefix}{abs_v/1_000_000:.0f}M"
    elif abs_v >= 100_000:
        s = f"{prefix}{abs_v/1_000_000:.1f}M"
    else:
        s = f"{prefix}{abs_v:,.0f}"
    return f"({s})" if v < 0 else s


def fmt_pct(v: float | None, *, apply_nm: bool = True) -> str:
    """Percent display. v is a decimal (0.058 -> 5.8%).
       Negative wrapped in parens. nm applied when |v| > 10.
    """
    if v is None or v == EMPTY:
        return EMPTY
    if apply_nm and abs(v) > NM_THRESHOLD:
        return "nm"
    pct = abs(v) * 100
    s = f"{pct:.1f}%"
    return f"({s})" if v < 0 else s


def fmt_pts(v: float | None) -> str:
    """Rule of 40 delta in points (e.g., +5.8 pts)."""
    if v is None or v == EMPTY:
        return EMPTY
    pts = v * 100
    sign = "+" if pts >= 0 else ""
    return f"{sign}{pts:.1f} pts"


# -------------------- derivation core --------------------

def safe_div(num, den):
    if num is None or den is None or den == 0:
        return None
    return num / den


def yoy(curr, prior):
    """YoY decimal (0.226 = 22.6%)"""
    if curr is None or prior is None or prior == 0:
        return None
    return curr / prior - 1


def variance(actual, plan):
    """Actual − Plan in $."""
    if actual is None or plan is None:
        return None
    return actual - plan


def variance_pct(actual, plan):
    """(Actual − Plan) / Plan decimal."""
    if actual is None or plan is None or plan == 0:
        return None
    return (actual - plan) / plan


def rule_of_40(gp, oi, gp_prior):
    """R40 = GP YoY + OI margin. All inputs raw values."""
    g = yoy(gp, gp_prior)
    m = safe_div(oi, gp)
    if g is None or m is None:
        return None
    return g + m


# -------------------- Flash table rows --------------------

@dataclass
class FlashRow:
    """A single Flash table row.
    Plan columns: 7 data cols (Actual, vs OL $, vs OL %, vs AP $, vs AP %, YoY %, prior-month YoY %)
    """
    label: str
    actual: Any  # number or None
    ol: Any
    ap: Any
    yoy_prior: Any  # prior-year value for YoY denom
    prior_month_actual: Any  # prior month actual (e.g., Mar'26 for Apr report)
    prior_month_yoy_prior: Any  # prior-year of prior month (e.g., Mar'25 for Apr report)
    actual_scale: str = "auto"  # 'auto' | 'count' | 'per_active' | 'pct' | 'rate'

    def to_cells(self) -> list[str]:
        """Return 7 formatted cells: [Actual, vs OL $, vs OL %, vs AP $, vs AP %, YoY %, prior-month YoY %]"""
        a = fmt_actual(self.actual, self.actual_scale)
        # Count metrics drop the $ from dollar-delta columns
        with_dollar = self.actual_scale != "count"
        ol_d = fmt_delta_dollar(variance(self.actual, self.ol), with_dollar=with_dollar)
        ol_p = fmt_pct(variance_pct(self.actual, self.ol))
        ap_d = fmt_delta_dollar(variance(self.actual, self.ap), with_dollar=with_dollar)
        ap_p = fmt_pct(variance_pct(self.actual, self.ap))
        yoy_v = fmt_pct(yoy(self.actual, self.yoy_prior))
        pm_yoy = fmt_pct(yoy(self.prior_month_actual, self.prior_month_yoy_prior))
        return [a, ol_d, ol_p, ap_d, ap_p, yoy_v, pm_yoy]


def _none_to_empty(v):
    return EMPTY if v is None else v


def build_flash_table(raw: dict, period_label: str, formatted: bool = True) -> list[list[Any]]:
    """Build the 28-row Flash table for L400:S427.
       formatted=True: returns formatted strings ($1.02B style) — for doc output
       formatted=False: returns raw numbers / decimals — for sheet writes (testing)
    """
    rows: list[list[Any]] = []

    # Row 400: period header
    rows.append([EMPTY, period_label, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY])
    # Row 401: column headers
    rows.append([EMPTY, "Actual", "vs. OL $", "vs. OL %", "vs. AP $", "vs. AP %", "YoY %", "Prior-mo YoY %"])

    def add(label: str, key_prefix: str, scale: str = "auto"):
        actual = raw.get(f"{key_prefix}_actual")
        ol = raw.get(f"{key_prefix}_ol")
        ap = raw.get(f"{key_prefix}_ap")
        yoy_prior = raw.get(f"{key_prefix}_yoy_prior")
        pm_actual = raw.get(f"{key_prefix}_prior_month_actual")
        pm_yoy_prior = raw.get(f"{key_prefix}_prior_month_yoy_prior")

        if formatted:
            r = FlashRow(label=label, actual=actual, ol=ol, ap=ap,
                         yoy_prior=yoy_prior, prior_month_actual=pm_actual,
                         prior_month_yoy_prior=pm_yoy_prior, actual_scale=scale)
            rows.append([label] + r.to_cells())
        else:
            # Raw: numbers and decimals. nm rule applied only to %.
            ol_pct = variance_pct(actual, ol)
            ap_pct = variance_pct(actual, ap)
            yoy_v = yoy(actual, yoy_prior)
            pm_yoy = yoy(pm_actual, pm_yoy_prior)

            def nm_or(v):
                if v is None:
                    return EMPTY
                return "nm" if abs(v) > NM_THRESHOLD else v

            rows.append([
                label,
                _none_to_empty(actual),
                _none_to_empty(variance(actual, ol)),
                nm_or(ol_pct),
                _none_to_empty(variance(actual, ap)),
                nm_or(ap_pct),
                nm_or(yoy_v),
                nm_or(pm_yoy),
            ])

    def add_blank(label: str):
        rows.append([label] + [EMPTY] * 7)

    add("Cash App Actives", "cash_app_actives", "count")
    add("Cash App Inflows per Active", "cash_app_inflows_per_active", "per_active")
    add("Commerce GMV", "commerce_gmv")
    add("Square GPV", "square_gpv")
    add("    Square US GPV", "square_us_gpv")
    add("    Square INTL GPV", "square_intl_gpv")
    add_blank("        Square INTL GPV (CC)")  # constant currency — Flash scope: skip
    add_blank("Gross Profit")  # section header

    add("    Block", "block_gp")
    add("        Cash App", "cash_app_gp")
    add("            Commerce", "commerce_gp")
    add("            Borrow", "borrow_gp")
    add("            Cash App Card", "cash_app_card_gp")
    add("            Instant Deposit", "instant_deposit_gp")
    add("            Post-Purchase BNPL", "post_purchase_bnpl_gp")
    add("        Square", "square_gp")
    add("            US Payments", "us_payments_gp")
    add("            INTL Payments", "intl_payments_gp")
    add("            Banking", "banking_gp")
    add("            SaaS", "saas_gp")
    add("            Hardware", "hardware_gp")
    add("        TIDAL", "tidal_gp")
    add("        Proto", "proto_gp")

    add("Adjusted Opex", "adj_opex")
    add("Adjusted OI", "adj_oi")

    # Rule of 40: actual is a rate, deltas in points
    r40_actual = rule_of_40(raw.get("block_gp_actual"), raw.get("adj_oi_actual"), raw.get("block_gp_yoy_prior"))
    r40_ol = rule_of_40(raw.get("block_gp_ol"), raw.get("adj_oi_ol"), raw.get("block_gp_yoy_prior"))
    r40_ap = rule_of_40(raw.get("block_gp_ap"), raw.get("adj_oi_ap"), raw.get("block_gp_yoy_prior"))
    r40_prior_year = rule_of_40(raw.get("block_gp_yoy_prior"), raw.get("adj_oi_yoy_prior"), raw.get("block_gp_yoy_prior_prior"))
    r40_prior_month = rule_of_40(raw.get("block_gp_prior_month_actual"), raw.get("adj_oi_prior_month_actual"), raw.get("block_gp_prior_month_yoy_prior"))
    r40_prior_month_prior_year = rule_of_40(raw.get("block_gp_prior_month_yoy_prior"), raw.get("adj_oi_prior_month_yoy_prior"), raw.get("block_gp_prior_month_yoy_prior_prior"))

    def delta(a, b):
        return None if a is None or b is None else a - b

    if formatted:
        rows.append([
            "Rule of 40",
            fmt_actual(r40_actual, scale="pct") if r40_actual is not None else EMPTY,
            EMPTY,
            fmt_pts(delta(r40_actual, r40_ol)),
            EMPTY,
            fmt_pts(delta(r40_actual, r40_ap)),
            fmt_pts(delta(r40_actual, r40_prior_year)),
            fmt_pts(delta(r40_prior_month, r40_prior_month_prior_year)),
        ])
    else:
        # Raw R40: actual as decimal (0.501 → renders "50.1%" with % cell format).
        # Deltas scaled to points (0.058 × 100 = 5.8 → renders "+5.8 pts" with custom format).
        # Reason: Sheets format syntax can't multiply by 100 without also rendering "%".
        def pts(a, b):
            d = delta(a, b)
            return EMPTY if d is None else d * 100
        rows.append([
            "Rule of 40",
            _none_to_empty(r40_actual),
            EMPTY,
            pts(r40_actual, r40_ol),
            EMPTY,
            pts(r40_actual, r40_ap),
            pts(r40_actual, r40_prior_year),
            pts(r40_prior_month, r40_prior_month_prior_year),
        ])

    return rows


# -------------------- Standardized P&L --------------------

PNL_LAYOUT = [
    # (label, key_prefix or None for section header / blank, is_total)
    ("Variable Operational Costs", None, False),  # section header
    ("P2P", "opex_p2p", False),
    ("Risk Loss", "opex_risk_loss", False),
    ("Card Issuance", "opex_card_issuance", False),
    ("Warehouse Financing", "opex_warehouse_financing", False),
    ("Other", "opex_other_variable", False),  # derived: HW Logistics + Bad Debt + Customer Reimbursements
    ("   Hardware Logistics", "opex_hw_logistics", False),
    ("   Bad Debt Expense", "opex_bad_debt", False),
    ("   Customer Reimbursements", "opex_customer_reimbursements", False),
    ("Total Variable Operational Costs", "opex_total_variable", True),
    ("Acquisition Costs", None, False),  # section header
    ("Marketing (Non-People)", "opex_marketing_non_people", False),  # derived
    ("   Marketing", "opex_marketing", False),
    ("   Onboarding Costs", "opex_onboarding", False),
    ("   Partnership Fees", "opex_partnership_fees", False),
    ("   Reader Expense", "opex_reader_expense", False),
    ("Sales & Marketing (People)", "opex_sales_marketing_people", False),
    ("Total Acquisition Costs", "opex_total_acquisition", True),
    ("Fixed Costs", None, False),  # section header
    ("Product Development People", "opex_prod_dev_people", False),
    ("G&A People", "opex_ga_people_total", False),  # derived
    ("   G&A People (ex. CS)", "opex_ga_people_ex_cs", False),
    ("   Customer Support People", "opex_customer_support_people", False),
    ("Software & Cloud", "opex_software_cloud", False),
    ("   Software", "opex_software", False),
    ("   Cloud fees", "opex_cloud_fees", False),
    ("Taxes, Insurance & Other Corp", "opex_taxes_insurance", False),
    ("Litigation & Professional Services", "opex_litigation_prof_services", False),  # derived
    ("   Legal fees", "opex_legal_fees", False),
    ("   Other Professional Services", "opex_other_prof_services", False),
    ("Rent, Facilities, Equipment", "opex_rent_facilities", False),
    ("Travel & Entertainment", "opex_travel_entertainment", False),
    ("Hardware Production Costs", "opex_hw_production", False),
    ("Non-Cash expenses (ex. SBC)", "opex_non_cash_ex_sbc", False),
    ("Total Fixed Costs", "opex_total_fixed", True),  # derived: total opex − var − acq
    ("Total Block GAAP OpEx", "opex_total_gaap", True),
]


def build_pnl_table(raw: dict, formatted: bool = True) -> list[list[Any]]:
    """Build the Standardized P&L for L432:R468.
       formatted=True: formatted strings for doc; False: raw numbers for sheet writes.
    """
    rows: list[list[Any]] = []

    # Row 432: column headers
    rows.append([EMPTY, "Actual", "vs. OL $", "vs. OL %", "vs. AP $", "vs. AP %", "YoY %"])

    for label, key, _is_total in PNL_LAYOUT:
        if key is None:
            rows.append([label, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY])
            continue

        a = raw.get(f"{key}_actual")
        ol = raw.get(f"{key}_ol")
        ap = raw.get(f"{key}_ap")
        yoy_prior = raw.get(f"{key}_yoy_prior")

        ol_pct = variance_pct(a, ol)
        ap_pct = variance_pct(a, ap)
        yoy_v = yoy(a, yoy_prior)

        if formatted:
            rows.append([
                label,
                fmt_actual(a),
                fmt_delta_dollar(variance(a, ol)),
                fmt_pct(ol_pct),
                fmt_delta_dollar(variance(a, ap)),
                fmt_pct(ap_pct),
                fmt_pct(yoy_v),
            ])
        else:
            def nm_or(v):
                if v is None:
                    return EMPTY
                return "nm" if abs(v) > NM_THRESHOLD else v
            rows.append([
                label,
                _none_to_empty(a),
                _none_to_empty(variance(a, ol)),
                nm_or(ol_pct),
                _none_to_empty(variance(a, ap)),
                nm_or(ap_pct),
                nm_or(yoy_v),
            ])

    return rows


# -------------------- raw value derivations --------------------

def compute_derived_raw(raw: dict) -> dict:
    """Compute derived raw values that downstream formatters need.

    Input raw has keys for BDM/Snowflake-sourced primitives.
    Output adds keys for:
      - cash_app_inflows_per_active_{actual,ol,ap,yoy_prior,prior_month_actual,prior_month_yoy_prior}
      - adj_opex_{actual,ol,ap,yoy_prior,prior_month_actual,prior_month_yoy_prior}
      - opex_other_variable_{...} (sum of HW Logistics + Bad Debt + Customer Reimbursements)
      - opex_marketing_non_people_{...} (sum of 4 marketing line items)
      - opex_ga_people_total_{...} (sum of ex-CS + Customer Support)
      - opex_software_cloud_{...} (sum of Software + Cloud fees)
      - opex_litigation_prof_services_{...} (sum of Legal + Other Prof Services)
      - opex_total_fixed_{...} (total opex − total variable − total acquisition)
    """
    out = dict(raw)

    # Inflows per Active for each period
    for scen in ("actual", "ol", "ap", "yoy_prior", "prior_month_actual", "prior_month_yoy_prior"):
        inflows = raw.get(f"cash_app_inflows_usd_{scen}")
        actives = raw.get(f"cash_app_actives_{scen}")
        out[f"cash_app_inflows_per_active_{scen}"] = safe_div(inflows, actives)

    # Adjusted OpEx = Block GP − Adj OI for each period
    for scen in ("actual", "ol", "ap", "yoy_prior", "prior_month_actual", "prior_month_yoy_prior"):
        gp = raw.get(f"block_gp_{scen}")
        oi = raw.get(f"adj_oi_{scen}")
        out[f"adj_opex_{scen}"] = (gp - oi) if (gp is not None and oi is not None) else None

    # OpEx derived rollups for each period
    for scen in ("actual", "ol", "ap", "yoy_prior"):
        # Other variable
        parts = [raw.get(f"opex_hw_logistics_{scen}"),
                 raw.get(f"opex_bad_debt_{scen}"),
                 raw.get(f"opex_customer_reimbursements_{scen}")]
        out[f"opex_other_variable_{scen}"] = sum(p for p in parts if p is not None) if all(p is not None for p in parts) else None

        # Marketing non-people
        parts = [raw.get(f"opex_marketing_{scen}"),
                 raw.get(f"opex_onboarding_{scen}"),
                 raw.get(f"opex_partnership_fees_{scen}"),
                 raw.get(f"opex_reader_expense_{scen}")]
        out[f"opex_marketing_non_people_{scen}"] = sum(p for p in parts if p is not None) if all(p is not None for p in parts) else None

        # G&A people total
        parts = [raw.get(f"opex_ga_people_ex_cs_{scen}"),
                 raw.get(f"opex_customer_support_people_{scen}")]
        out[f"opex_ga_people_total_{scen}"] = sum(p for p in parts if p is not None) if all(p is not None for p in parts) else None

        # Software & Cloud
        parts = [raw.get(f"opex_software_{scen}"),
                 raw.get(f"opex_cloud_fees_{scen}")]
        out[f"opex_software_cloud_{scen}"] = sum(p for p in parts if p is not None) if all(p is not None for p in parts) else None

        # Litigation & Professional Services
        parts = [raw.get(f"opex_legal_fees_{scen}"),
                 raw.get(f"opex_other_prof_services_{scen}")]
        out[f"opex_litigation_prof_services_{scen}"] = sum(p for p in parts if p is not None) if all(p is not None for p in parts) else None

        # Total Fixed = Total Opex − Total Variable − Total Acquisition
        total = raw.get(f"opex_total_gaap_{scen}")
        var = raw.get(f"opex_total_variable_{scen}")
        acq = raw.get(f"opex_total_acquisition_{scen}")
        if total is not None and var is not None and acq is not None:
            out[f"opex_total_fixed_{scen}"] = total - var - acq
        else:
            out[f"opex_total_fixed_{scen}"] = None

    return out


# -------------------- main --------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to raw values JSON")
    ap.add_argument("--period", required=True, help="Period label e.g. Apr'26")
    ap.add_argument("--output", help="Optional path to write output JSON; default stdout")
    args = ap.parse_args()

    with open(args.input) as f:
        raw = json.load(f)

    raw = compute_derived_raw(raw)

    out = {
        "flash_table_raw": build_flash_table(raw, args.period, formatted=False),
        "flash_table_formatted": build_flash_table(raw, args.period, formatted=True),
        "pnl_table_raw": build_pnl_table(raw, formatted=False),
        "pnl_table_formatted": build_pnl_table(raw, formatted=True),
        "raw_derived": raw,
    }

    js = json.dumps(out, indent=2, default=str)
    if args.output:
        with open(args.output, "w") as f:
            f.write(js)
    else:
        print(js)


if __name__ == "__main__":
    main()
