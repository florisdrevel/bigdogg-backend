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

Design note — the reserve models a ZZP'er whose business profit is their MAIN
income (the typical BigDogg user), so it stays sensible at every income level:
  • applies the ondernemersaftrek (zelfstandigenaftrek when the urencriterium is
    met, + MKB-winstvrijstelling), then
  • applies the box-1 brackets, then
  • SUBTRACTS the standard heffingskortingen (algemene heffingskorting +
    arbeidskorting). At low profit these credits cancel the tax entirely, so a
    €3.550 profit correctly yields a ~€0 reserve — not a nonsensical four-figure
    one (the bug this replaced).

Caveat (must be shown in the UI/PDF): someone who ALSO has loon uit
dienstbetrekking has those heffingskortingen already used against that salary,
so they should reserve MORE than this figure.

This produces a GUIDELINE, never a tax assessment. Always present it as such.
"""

# ── Urencriterium — hours that unlock the zelfstandigenaftrek ─────────────────
URENCRITERIUM_HOURS = 1225  # verify yearly

# ── Reiskostenvergoeding — deductible rate per zakelijke kilometer ────────────
# Belastingdienst flat allowance for business km, per tax year. Was €0,21 in
# 2023, raised to €0,23 from 2024. Verify yearly.
KM_RATE_BY_YEAR = {
    2023: 0.21,
    2024: 0.23,
    2025: 0.23,
    2026: 0.23,  # verify yearly
}
DEFAULT_KM_RATE = 0.23  # latest known; used if the year is missing

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

# ── Heffingskortingen (tax credits), per tax year — under AOW age ─────────────
# Verified against the Belastingdienst for 2026. RE-CHECK EVERY YEAR.
# Algemene heffingskorting: full up to `taper_start`, then linear down to €0.
ALGEMENE_HEFFINGSKORTING_BY_YEAR = {
    2026: {"max": 3115.0, "taper_start": 29736.0, "taper_rate": 0.06398},
}
DEFAULT_AHK = ALGEMENE_HEFFINGSKORTING_BY_YEAR[2026]

# Arbeidskorting: piecewise on arbeidsinkomen. Segments are
# (lower_bound, base_credit_at_lower_bound, marginal_rate_within_segment).
# The final segment phases the credit out (negative rate); floored at €0.
# 2026 (Belastingdienst, niet-AOW): 0–11.965 @8,324%; 11.965–25.845 €996+31,009%;
# 25.845–45.592 €5.300+1,950%; 45.592–132.920 €5.685−6,510%.
ARBEIDSKORTING_SEGMENTS_BY_YEAR = {
    2026: [
        (0.0, 0.0, 0.08324),
        (11965.0, 996.0, 0.31009),
        (25845.0, 5300.0, 0.01950),
        (45592.0, 5685.0, -0.06510),
    ],
}
DEFAULT_ARBEIDSKORTING_SEGMENTS = ARBEIDSKORTING_SEGMENTS_BY_YEAR[2026]


def km_rate_for_year(year: int) -> float:
    return KM_RATE_BY_YEAR.get(year, DEFAULT_KM_RATE)


def zelfstandigenaftrek_for_year(year: int) -> float:
    return ZELFSTANDIGENAFTREK_BY_YEAR.get(year, DEFAULT_ZELFSTANDIGENAFTREK)


def mkb_vrijstelling_for_year(year: int) -> float:
    return MKB_WINSTVRIJSTELLING_BY_YEAR.get(year, DEFAULT_MKB_WINSTVRIJSTELLING)


def box1_brackets_for_year(year: int):
    return BOX1_BRACKETS_BY_YEAR.get(year, DEFAULT_BOX1_BRACKETS)


def algemene_heffingskorting_for_year(income: float, year: int) -> float:
    """Algemene heffingskorting at the given (box-1) income, for `year`."""
    p = ALGEMENE_HEFFINGSKORTING_BY_YEAR.get(year, DEFAULT_AHK)
    income = max(0.0, income or 0.0)
    if income <= p["taper_start"]:
        return p["max"]
    return max(0.0, p["max"] - p["taper_rate"] * (income - p["taper_start"]))


def arbeidskorting_for_year(income: float, year: int) -> float:
    """Arbeidskorting at the given arbeidsinkomen, for `year` (piecewise)."""
    segments = ARBEIDSKORTING_SEGMENTS_BY_YEAR.get(year, DEFAULT_ARBEIDSKORTING_SEGMENTS)
    income = max(0.0, income or 0.0)
    credit = 0.0
    for lower, base, rate in segments:
        if income >= lower:
            credit = base + rate * (income - lower)
        else:
            break
    return max(0.0, credit)


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

    gross_tax = round(_box1_tax(belastbare_winst, box1_brackets_for_year(year)), 2)
    # Heffingskortingen — computed on belastbare winst as a proxy for box-1
    # income, assuming this profit is the user's MAIN income. At low profit
    # these credits cancel the tax (→ €0). The UI/PDF carry a caveat telling
    # users with loondienst income (whose credits are already used) to reserve
    # more. Credits only offset tax due; the unused remainder is not paid out.
    ahk = round(algemene_heffingskorting_for_year(belastbare_winst, year), 2)
    ak = round(arbeidskorting_for_year(belastbare_winst, year), 2)
    heffingskortingen = round(ahk + ak, 2)
    reserve = max(0.0, round(gross_tax - heffingskortingen, 2))
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
        "gross_tax": gross_tax,
        "algemene_heffingskorting": ahk,
        "arbeidskorting": ak,
        "heffingskortingen": heffingskortingen,
        "reserve": reserve,
        "effective_rate": effective_rate,
    }
