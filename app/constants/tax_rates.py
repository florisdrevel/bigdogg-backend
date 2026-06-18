"""
Centralised Dutch tax constants + the conservative income-tax reserve estimate
used by the annual overview ("Reserveer voor de belasting").

============================================================================
⚠️  VERIFY EVERY VALUE BELOW AGAINST THE BELASTINGDIENST EACH TAX YEAR.  ⚠️
============================================================================
These figures change annually (usually announced on Prinsjesdag, effective
1 January). The zelfstandigenaftrek in particular is on a scheduled multi-year
decline. When a new tax year starts, add/confirm its entry in EVERY map below.
Last verified for tax year: 2026.

Design note — the reserve is deliberately CONSERVATIVE:
  • It DOES apply the ondernemersaftrek (zelfstandigenaftrek + MKB-
    winstvrijstelling) so the taxable base is realistic, BUT
  • it does NOT credit any heffingskortingen (algemene heffingskorting /
    arbeidskorting). Those are intentionally left out so the estimate errs on
    the high side and protects users who ALSO have loondienst income — whose
    kortingen are already consumed against that salary — from under-reserving.

This produces a GUIDELINE, never a tax assessment. Always present it as such.
"""

# ── Urencriterium — hours that unlock the zelfstandigenaftrek ─────────────────
URENCRITERIUM_HOURS = 1225  # verify yearly

# ── Zelfstandigenaftrek (self-employed deduction), per tax year ───────────────
# Flat amount, granted only if the urencriterium is met. On a scheduled decline.
ZELFSTANDIGENAFTREK_BY_YEAR = {
    2023: 5030.0,
    2024: 3750.0,
    2025: 2470.0,
    2026: 1200.0,  # verify yearly
}
DEFAULT_ZELFSTANDIGENAFTREK = 1200.0  # latest known; used if the year is missing

# ── MKB-winstvrijstelling (SME profit exemption), per tax year ────────────────
# A percentage of the profit AFTER the ondernemersaftrek.
MKB_WINSTVRIJSTELLING_BY_YEAR = {
    2024: 0.1331,
    2025: 0.127,
    2026: 0.127,  # verify yearly
}
DEFAULT_MKB_WINSTVRIJSTELLING = 0.127

# ── Box 1 income-tax brackets, per tax year ───────────────────────────────────
# Each bracket is (upper_bound_of_band_or_None, marginal_rate), low → high.
# 2026: 35,7% up to €38.883 · 37,56% up to €79.137 · 49,5% above.
BOX1_BRACKETS_BY_YEAR = {
    2026: [
        (38883.0, 0.357),
        (79137.0, 0.3756),
        (None, 0.495),
    ],
}
DEFAULT_BOX1_BRACKETS = [
    (38883.0, 0.357),
    (79137.0, 0.3756),
    (None, 0.495),
]


def zelfstandigenaftrek_for_year(year: int) -> float:
    return ZELFSTANDIGENAFTREK_BY_YEAR.get(year, DEFAULT_ZELFSTANDIGENAFTREK)


def mkb_vrijstelling_for_year(year: int) -> float:
    return MKB_WINSTVRIJSTELLING_BY_YEAR.get(year, DEFAULT_MKB_WINSTVRIJSTELLING)


def box1_brackets_for_year(year: int):
    return BOX1_BRACKETS_BY_YEAR.get(year, DEFAULT_BOX1_BRACKETS)


def _box1_tax(taxable: float, brackets) -> float:
    """Progressive box-1 tax over `taxable`, NO heffingskortingen (by design)."""
    if taxable <= 0:
        return 0.0
    tax = 0.0
    lower = 0.0
    for upper, rate in brackets:
        if upper is None:
            tax += (taxable - lower) * rate
            break
        if taxable > upper:
            tax += (upper - lower) * rate
            lower = upper
        else:
            tax += (taxable - lower) * rate
            break
    return tax


def estimate_income_tax_reserve(
    total_profit: float,
    total_depreciation: float = 0.0,
    km_deduction: float = 0.0,
    urencriterium_met: bool = False,
    year: int = 2026,
) -> dict:
    """
    Conservative estimate of the box-1 income tax to set aside on self-employment
    profit, based only on data we already hold. Returns the full breakdown so
    callers can show their work. See the module docstring for why this errs high
    (no heffingskortingen).

    Chain:
      winst_onderneming        = profit − depreciation − km_deduction
      − zelfstandigenaftrek    (only if urencriterium met; capped at the winst)
      = winst_na_ondernemersaftrek
      − MKB-winstvrijstelling  (% of winst_na_ondernemersaftrek)
      = belastbare_winst
      → box-1 brackets (NO heffingskortingen) = reserve
    """
    winst_onderneming = round(
        (total_profit or 0.0) - (total_depreciation or 0.0) - (km_deduction or 0.0), 2
    )

    zelfstandigenaftrek = 0.0
    if urencriterium_met and winst_onderneming > 0:
        # In this estimate the zelfstandigenaftrek cannot create/deepen a loss;
        # any surplus carries forward in reality, but we conservatively cap it.
        zelfstandigenaftrek = min(zelfstandigenaftrek_for_year(year), winst_onderneming)

    winst_na_aftrek = max(0.0, round(winst_onderneming - zelfstandigenaftrek, 2))

    mkb_rate = mkb_vrijstelling_for_year(year)
    mkb_vrijstelling = round(winst_na_aftrek * mkb_rate, 2)
    belastbare_winst = round(winst_na_aftrek - mkb_vrijstelling, 2)

    reserve = round(_box1_tax(belastbare_winst, box1_brackets_for_year(year)), 2)
    effective_rate = round(reserve / belastbare_winst, 4) if belastbare_winst > 0 else 0.0

    return {
        "year": year,
        "winst_onderneming": winst_onderneming,
        "km_deduction": round(km_deduction or 0.0, 2),
        "urencriterium_met": bool(urencriterium_met),
        "zelfstandigenaftrek": round(zelfstandigenaftrek, 2),
        "winst_na_ondernemersaftrek": winst_na_aftrek,
        "mkb_winstvrijstelling_rate": mkb_rate,
        "mkb_winstvrijstelling": mkb_vrijstelling,
        "belastbare_winst": belastbare_winst,
        "reserve": reserve,
        "effective_rate": effective_rate,
    }
