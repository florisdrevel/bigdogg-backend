"""Side-effect tests for `_enrich_transaction_with_link`.

Where test_banking_match.py exercises the pure scoring helpers, this
file exercises the orchestration: when a transaction matches an
invoice with high enough confidence, the matcher must

  * call `_persist_link` to write a row in bank_transaction_links
  * call `_mark_invoice_paid` to flip the invoice status
  * call `_notify_match` so the user sees a bell entry

We monkeypatch those three helpers so we can run the whole pipeline
in-process without Supabase. Each test asserts both the returned
`tx["link"]` shape AND the side-effect calls that should (or should
not) have happened.
"""

from datetime import date, timedelta
from app.routers import banking

TODAY = date(2026, 5, 5)
USER_ID = "user_under_test"


def tx(amount, *, description="", merchant="", days_ago=0):
    return {
        "id": "tx_xyz",
        "amount": amount,
        "description": description,
        "merchant": merchant,
        "date": (TODAY - timedelta(days=days_ago)).isoformat(),
        "currency": "EUR",
    }


def invoice(*, number="INV-2026-0042", total=100.0, status="sent",
            client_name="", client_company="", days_ago=0, _id="inv_1"):
    return {
        "id": _id,
        "invoice_number": number,
        "total_incl_btw": total,
        "status": status,
        "client_name": client_name,
        "client_company": client_company,
        "invoice_date": (TODAY - timedelta(days=days_ago)).isoformat(),
    }


def expense(*, description="", amount_ex_btw=0, btw_amount=0,
            days_ago=0, _id="exp_1"):
    return {
        "id": _id,
        "description": description,
        "amount_ex_btw": amount_ex_btw,
        "btw_amount": btw_amount,
        "expense_date": (TODAY - timedelta(days=days_ago)).isoformat(),
    }


class _Recorder:
    """Captures every call so the test can assert exactly what fired."""

    def __init__(self):
        self.persist_calls = []
        self.mark_paid_calls = []
        self.notify_calls = []

    def install(self, monkeypatch):
        monkeypatch.setattr(banking, "_persist_link",
                            lambda *a, **kw: self.persist_calls.append((a, kw)))
        monkeypatch.setattr(banking, "_mark_invoice_paid",
                            lambda iid, uid: self.mark_paid_calls.append(iid))
        monkeypatch.setattr(banking, "_notify_match",
                            lambda *a, **kw: self.notify_calls.append((a, kw)))


# ═══════════════════════════════════════════════════════════════
# Auto-link income → invoice
# ═══════════════════════════════════════════════════════════════
def test_auto_match_invoice_persists_marks_paid_and_notifies(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    inv = invoice(total=121.00, client_name="ACME BV", days_ago=2)
    out = banking._enrich_transaction_with_link(
        tx=tx(121.00, description="ideal acme bv INV-2026-0042", days_ago=2),
        existing_links={},
        invoices=[inv],
        expenses=[],
        investments=[],
        user_id=USER_ID,
    )

    assert out["link"]["type"] == "invoice"
    assert out["link"]["linked_id"] == inv["id"]
    assert out["link"]["auto"] is True

    # Persisted with link_type='invoice' (firm), not 'suggested_invoice'.
    assert len(rec.persist_calls) == 1
    args, kwargs = rec.persist_calls[0]
    # _persist_link is called with (user_id, tx_id, link_type, linked_id) +
    # auto as a kwarg.
    assert args[0] == USER_ID
    assert args[1] == "tx_xyz"
    assert args[2] == "invoice"
    assert args[3] == inv["id"]
    assert kwargs.get("auto") is True

    # Invoice marked paid.
    assert rec.mark_paid_calls == [inv["id"]]

    # Bell notification of kind='auto'.
    assert len(rec.notify_calls) == 1
    _, nkw = rec.notify_calls[0]
    assert nkw.get("kind") == "auto"
    assert nkw.get("link_type") == "invoice"


# ═══════════════════════════════════════════════════════════════
# Suggest income → invoice (must NOT flip status)
# ═══════════════════════════════════════════════════════════════
def test_suggest_invoice_persists_suggested_does_not_mark_paid(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    inv = invoice(total=75.00, client_name="ACME BV", days_ago=1)
    out = banking._enrich_transaction_with_link(
        tx=tx(75.00, description="ideal anonymous"),
        existing_links={},
        invoices=[inv],
        expenses=[],
        investments=[],
        user_id=USER_ID,
    )

    assert out["link"]["type"] == "suggested_invoice"

    assert len(rec.persist_calls) == 1
    args, _ = rec.persist_calls[0]
    assert args[2] == "suggested_invoice"

    # CRITICAL: a suggestion must never auto-flip the invoice to paid.
    assert rec.mark_paid_calls == []

    # Bell entry of kind='suggest'.
    assert len(rec.notify_calls) == 1
    _, nkw = rec.notify_calls[0]
    assert nkw.get("kind") == "suggest"


# ═══════════════════════════════════════════════════════════════
# Below threshold — no link, no side effects
# ═══════════════════════════════════════════════════════════════
def test_no_match_persists_nothing_and_does_not_notify(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    out = banking._enrich_transaction_with_link(
        tx=tx(33.58, description="hellofresh weekly box"),
        existing_links={},
        invoices=[invoice(total=121.00, client_name="ACME BV")],
        expenses=[],
        investments=[],
        user_id=USER_ID,
    )

    assert out["link"] is None
    assert rec.persist_calls == []
    assert rec.mark_paid_calls == []
    assert rec.notify_calls == []


# ═══════════════════════════════════════════════════════════════
# Outgoing → expense (auto): persists, notifies, NO invoice mark
# ═══════════════════════════════════════════════════════════════
def test_auto_match_expense_persists_and_notifies(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    ex = expense(description="Hellofresh", amount_ex_btw=27.75,
                 btw_amount=5.83, days_ago=1)
    out = banking._enrich_transaction_with_link(
        tx=tx(-33.58, description="hellofresh", merchant="Hellofresh"),
        existing_links={},
        invoices=[],
        expenses=[ex],
        investments=[],
        user_id=USER_ID,
    )

    assert out["link"]["type"] == "expense"
    assert out["link"]["linked_id"] == ex["id"]
    assert len(rec.persist_calls) == 1
    args, _ = rec.persist_calls[0]
    assert args[2] == "expense"
    # Expenses never trigger _mark_invoice_paid.
    assert rec.mark_paid_calls == []
    assert len(rec.notify_calls) == 1


# ═══════════════════════════════════════════════════════════════
# An existing manual link short-circuits the matcher entirely
# ═══════════════════════════════════════════════════════════════
def test_existing_link_short_circuits_matcher(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    inv = invoice(_id="inv_existing", number="INV-2026-9999")
    existing = {
        "tx_xyz": {
            "tx_id": "tx_xyz",
            "link_type": "invoice",
            "linked_id": inv["id"],
            "auto": False,
        }
    }
    out = banking._enrich_transaction_with_link(
        tx=tx(121.00, description="ideal acme bv"),
        existing_links=existing,
        invoices=[inv],
        expenses=[],
        investments=[],
        user_id=USER_ID,
    )

    # Manual link kept, no rescoring, no fresh side effects.
    assert out["link"]["type"] == "invoice"
    assert out["link"]["linked_id"] == "inv_existing"
    assert rec.persist_calls == []
    assert rec.mark_paid_calls == []
    assert rec.notify_calls == []


# ═══════════════════════════════════════════════════════════════
# Stripe European-card payout — auto-link with invoice→paid
# ═══════════════════════════════════════════════════════════════
def test_stripe_european_card_payout_auto_links_and_marks_paid(monkeypatch):
    rec = _Recorder()
    rec.install(monkeypatch)

    inv = invoice(total=121.00, client_name="ACME BV", days_ago=2,
                  _id="inv_stripe_eu")
    out = banking._enrich_transaction_with_link(
        tx=tx(118.94, description="stripe payments acme bv", days_ago=2),
        existing_links={},
        invoices=[inv],
        expenses=[],
        investments=[],
        user_id=USER_ID,
    )
    assert out["link"]["type"] == "invoice"
    assert rec.mark_paid_calls == [inv["id"]]
    args, _ = rec.persist_calls[0]
    assert args[2] == "invoice"
