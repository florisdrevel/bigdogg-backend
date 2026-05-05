"""Pure-function tests for the auto-matching scorer in banking.py.

We exercise `_score_invoice_match`, `_score_expense_match`,
`_stripe_fee_match`, `_looks_like_stripe_payout`, and indirectly the
AUTO/SUGGEST thresholds. No network, no Supabase, no Tink.

Each test models a realistic ZZP scenario:
  - iDEAL transfer with the invoice number in the memo
  - Stripe European-card payout (1.5% + €0.25 net)
  - Stripe non-European-card payout (2.9% + €0.25 net)
  - Wrong amount, right name (or vice versa)
  - Already-paid invoices ignored
  - Expense ↔ existing-expense-entry within tolerance windows
"""

from datetime import date, timedelta

from app.routers.banking import (
    _looks_like_stripe_payout,
    _score_expense_match,
    _score_invoice_match,
    _stripe_fee_match,
    MATCH_AUTO_SCORE,
    MATCH_SUGGEST_SCORE,
)

TODAY = date(2026, 5, 5)


# ─── Fixture builders ──────────────────────────────────────────
def tx(amount: float, *, description: str = "", merchant: str = "", days_ago: int = 0):
    return {
        "id": "tx_test",
        "amount": amount,
        "description": description,
        "merchant": merchant,
        "date": (TODAY - timedelta(days=days_ago)).isoformat(),
        "currency": "EUR",
    }


def invoice(
    *,
    number: str = "INV-2026-0001",
    total: float = 100.0,
    status: str = "sent",
    client_name: str = "",
    client_company: str = "",
    days_ago: int = 0,
):
    return {
        "id": "inv_test",
        "invoice_number": number,
        "total_incl_btw": total,
        "status": status,
        "client_name": client_name,
        "client_company": client_company,
        "invoice_date": (TODAY - timedelta(days=days_ago)).isoformat(),
    }


def expense(
    *,
    description: str = "",
    amount_ex_btw: float = 0,
    btw_amount: float = 0,
    days_ago: int = 0,
):
    return {
        "id": "exp_test",
        "description": description,
        "amount_ex_btw": amount_ex_btw,
        "btw_amount": btw_amount,
        "expense_date": (TODAY - timedelta(days=days_ago)).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════
# _looks_like_stripe_payout
# ═══════════════════════════════════════════════════════════════
def test_stripe_keyword_detected_in_various_strings():
    assert _looks_like_stripe_payout("stripe payments")
    assert _looks_like_stripe_payout("STRIPE PAYMENTS BV")
    assert _looks_like_stripe_payout("payout from stripe.com")
    assert _looks_like_stripe_payout("str.pe/abc")


def test_stripe_keyword_absent_when_unrelated():
    assert not _looks_like_stripe_payout("ideal albert heijn")
    assert not _looks_like_stripe_payout("salaris werkgever bv")
    assert not _looks_like_stripe_payout("")


# ═══════════════════════════════════════════════════════════════
# _stripe_fee_match — predicts post-fee net of an invoice
# ═══════════════════════════════════════════════════════════════
def test_stripe_fee_european_card_net_of_100_eur():
    # 1.5% + €0.25 fee on €100 → net €98.25 lands in the bank.
    diff = _stripe_fee_match(98.25, 100.0)
    assert diff is not None
    assert diff <= 0.10


def test_stripe_fee_non_european_card_net_of_100_eur():
    # 2.9% + €0.25 → net €96.85.
    diff = _stripe_fee_match(96.85, 100.0)
    assert diff is not None
    assert diff <= 0.10


def test_stripe_fee_no_match_when_amount_unrelated():
    # €50 received against a €100 invoice — way off either fee predict.
    assert _stripe_fee_match(50.0, 100.0) is None


def test_stripe_fee_no_match_when_amount_exceeds_invoice():
    # Fees subtract; a received amount > invoice can't be a fee match.
    assert _stripe_fee_match(105.0, 100.0) is None


# ═══════════════════════════════════════════════════════════════
# _score_invoice_match — overall confidence
# ═══════════════════════════════════════════════════════════════
def test_invoice_number_in_description_auto_links():
    """An iDEAL transfer with the exact invoice number in the memo
    should breeze past AUTO regardless of other signals."""
    score = _score_invoice_match(
        tx(121.00, description="ideal betaling INV-2026-0042 acme bv", days_ago=2),
        invoice(number="INV-2026-0042", total=121.00, client_name="ACME BV", days_ago=3),
    )
    assert score >= MATCH_AUTO_SCORE


def test_exact_amount_plus_client_name_auto_links():
    """No invoice number but the amount is exact AND the client name
    appears: high enough confidence to skip user confirmation."""
    score = _score_invoice_match(
        tx(250.00, description="sepa overboeking acme bv", merchant="ACME BV", days_ago=3),
        invoice(total=250.00, client_name="ACME BV", days_ago=3),
    )
    assert score >= MATCH_AUTO_SCORE


def test_stripe_european_card_payout_auto_links_with_client_match():
    """Customer paid €121 via Stripe European card; bank receives
    €118.94 (= 121 × 0.985 − 0.25). Amount is a Stripe-fee match
    (+55), description mentions Stripe (+10), client name (+25), date
    close (+10) → ≥80, auto-link."""
    score = _score_invoice_match(
        tx(118.94, description="stripe payments acme bv", days_ago=2),
        invoice(total=121.00, client_name="ACME BV", days_ago=2),
    )
    assert score >= MATCH_AUTO_SCORE


def test_stripe_non_european_card_payout_auto_links_with_client_match():
    """Stripe non-European card: 2.9% + €0.25 on €121 → net €117.26."""
    score = _score_invoice_match(
        tx(117.26, description="stripe payments contoso ltd", days_ago=1),
        invoice(total=121.00, client_company="Contoso Ltd", days_ago=1),
    )
    assert score >= MATCH_AUTO_SCORE


def test_stripe_fee_match_alone_only_suggests():
    """No client name, no Stripe keyword — just a transaction whose
    amount happens to look like a Stripe-fee net of an open invoice.
    Should suggest, not auto-link."""
    score = _score_invoice_match(
        tx(98.25, description="incoming payment", days_ago=1),
        invoice(total=100.00, client_name="Some Client", days_ago=1),
    )
    assert MATCH_SUGGEST_SCORE <= score < MATCH_AUTO_SCORE


def test_exact_amount_alone_only_suggests():
    """Exact amount with no name match and no invoice number → just
    over the SUGGEST threshold."""
    score = _score_invoice_match(
        tx(75.00, description="ideal anonymous"),
        invoice(total=75.00, client_name="ACME BV"),
    )
    assert MATCH_SUGGEST_SCORE <= score < MATCH_AUTO_SCORE


def test_client_name_alone_does_not_meet_suggest_threshold():
    """Name present but amount way off → below SUGGEST."""
    score = _score_invoice_match(
        tx(12.34, description="acme bv subscription", days_ago=2),
        invoice(total=500.00, client_name="ACME BV", days_ago=2),
    )
    assert score < MATCH_SUGGEST_SCORE


def test_random_unrelated_transaction_scores_zero():
    score = _score_invoice_match(
        tx(33.58, description="hellofresh weekly box"),
        invoice(total=121.00, client_name="ACME BV"),
    )
    # No name overlap, no amount overlap — at most a small date bonus,
    # which itself requires both dates to be present.
    assert score < MATCH_SUGGEST_SCORE


def test_already_paid_invoice_is_ignored():
    score = _score_invoice_match(
        tx(121.00, description="sepa acme bv INV-2026-0042"),
        invoice(number="INV-2026-0042", total=121.00,
                client_name="ACME BV", status="paid"),
    )
    assert score == 0


def test_outgoing_transaction_against_invoice_scores_zero():
    """Negative amount should never match an invoice (those are income only)."""
    score = _score_invoice_match(
        tx(-121.00, description="ACME BV refund"),
        invoice(total=121.00, client_name="ACME BV"),
    )
    assert score == 0


def test_within_half_pct_amount_plus_client_name_auto_links():
    """Bank rounding sometimes nudges by a cent or two — within 0.5%
    + client name should still auto-link."""
    score = _score_invoice_match(
        tx(100.40, description="ideal acme bv", days_ago=1),
        invoice(total=100.00, client_name="ACME BV", days_ago=1),
    )
    assert score >= MATCH_AUTO_SCORE


def test_old_payment_still_matches_with_lower_date_bonus():
    """A 45-day-old invoice that finally gets paid: still matches but
    with the smaller date bonus."""
    score = _score_invoice_match(
        tx(250.00, description="sepa acme bv", days_ago=45),
        invoice(total=250.00, client_name="ACME BV", days_ago=45),
    )
    # Exact amount (60) + name (25) + date 45d (5) = 90 → AUTO.
    assert score >= MATCH_AUTO_SCORE


# ═══════════════════════════════════════════════════════════════
# _score_expense_match — outgoing tx → existing expense entry
# ═══════════════════════════════════════════════════════════════
def test_expense_exact_match_with_description_and_close_date_auto_links():
    """Receipt uploaded yesterday for €33.58 (Hellofresh, 21% BTW),
    today the bank shows the same outgoing tx."""
    score = _score_expense_match(
        tx(-33.58, description="hellofresh", merchant="Hellofresh", days_ago=0),
        expense(description="Hellofresh", amount_ex_btw=27.75,
                btw_amount=5.83, days_ago=1),
    )
    assert score >= MATCH_AUTO_SCORE


def test_expense_exact_amount_no_description_only_suggests():
    score = _score_expense_match(
        tx(-12.34, description="random outgoing", days_ago=0),
        expense(description="Coffee shop", amount_ex_btw=10.20,
                btw_amount=2.14, days_ago=1),
    )
    # Exact amount (60) + 1d date (10) = 70 — below AUTO, above SUGGEST.
    assert MATCH_SUGGEST_SCORE <= score < MATCH_AUTO_SCORE


def test_expense_old_date_penalises_but_doesnt_kill_strong_match():
    """An exact amount + description match 30 days apart should still
    surface as a suggestion (user has the final call), but never as
    an auto-link."""
    score = _score_expense_match(
        tx(-50.00, description="rent", days_ago=0),
        expense(description="rent", amount_ex_btw=41.32,
                btw_amount=8.68, days_ago=30),
    )
    assert MATCH_SUGGEST_SCORE <= score < MATCH_AUTO_SCORE


def test_expense_old_date_with_amount_only_falls_below_suggest():
    """Without a description match, an old expense should drop below
    the SUGGEST threshold."""
    score = _score_expense_match(
        tx(-50.00, description="random outgoing", days_ago=0),
        expense(description="something else", amount_ex_btw=41.32,
                btw_amount=8.68, days_ago=30),
    )
    assert score < MATCH_SUGGEST_SCORE


def test_income_against_expense_scores_zero():
    score = _score_expense_match(
        tx(50.00, description="refund"),
        expense(description="refund", amount_ex_btw=41.32, btw_amount=8.68),
    )
    assert score == 0
