"""Parsers for Dutch bank-statement file formats.

Two formats covered:

  * MT940 — legacy SWIFT format still emitted by every NL bank
    (ING, ABN, Rabobank, Knab, SNS, ASN, Triodos, bunq).
    Parsed via the `mt-940` library which handles the bank-specific
    quirks in tag 86 (description) interpretation.

  * CAMT.053 — ISO 20022 XML, the modern replacement. NL banks
    started serving this around 2024-2025 and most have switched the
    default to CAMT by now. Parsed with the stdlib XML library — no
    external dep needed for the entry-level fields BigDogg cares
    about.

Both parsers normalize their output to the SAME dict shape as
`banking._normalize_truelayer_transaction`, so the auto-matcher can chew
on either source without caring where the data came from.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from typing import List

import mt940


# Tx shape matches `banking._normalize_truelayer_transaction`:
#   id, date (YYYY-MM-DD), description, merchant, amount (signed
#   decimal), currency, type, status.
NormalizedTx = dict


def detect_format(raw: bytes) -> str:
    """Return 'mt940' | 'camt053' | 'unknown' based on file head."""
    head = raw[:512].lstrip()
    if head.startswith(b"{1:") or head.startswith(b":20:") or head.startswith(b"{4:"):
        return "mt940"
    if head.startswith(b"<?xml") or b"<Document" in head:
        return "camt053"
    # Some MT940 exports start with a leading space or BOM.
    text = head.decode("latin-1", errors="ignore").lstrip("﻿").strip()
    if text.startswith(":20:") or text.startswith("{1:"):
        return "mt940"
    if text.startswith("<?xml") or "<Document" in text:
        return "camt053"
    return "unknown"


# ─── MT940 ─────────────────────────────────────────────────────
def parse_mt940(raw: bytes) -> List[NormalizedTx]:
    text = raw.decode("latin-1", errors="ignore")
    transactions: List[NormalizedTx] = []
    parsed = mt940.models.Transactions()
    parsed.parse(text)

    for tx in parsed:
        data = tx.data or {}
        amount = data.get("amount")
        # mt940's Amount type carries a Decimal + status (D/C). Negative
        # for debits, positive for credits in our normalized shape.
        if amount is not None:
            amt_value = float(amount.amount)
        else:
            amt_value = 0.0

        booking_date = data.get("date")
        date_str = booking_date.isoformat() if booking_date else None

        # Tag 86 is free-text description. The mt-940 lib already merges
        # multi-line tag 86 plus parses common bank-specific subfields
        # ("/REMI/", "/NAME/", etc) into separate keys when present.
        description = (
            data.get("transaction_details")
            or data.get("purpose")
            or data.get("non_swift_text")
            or ""
        ).strip()
        merchant = (
            data.get("applicant_name")
            or data.get("counter_party_name")
            or data.get("recipient_name")
            or ""
        ).strip()

        # External_id: prefer transaction_reference, fall back to a
        # synthetic key combining account + date + amount + counter so
        # repeat imports of the same file dedupe cleanly.
        ext_id = (
            data.get("transaction_reference")
            or data.get("bank_reference")
            or data.get("customer_reference")
            or ""
        ).strip()
        if not ext_id:
            ext_id = f"mt940:{date_str}:{amt_value}:{(description or '')[:40]}"

        transactions.append({
            "id": ext_id,
            "date": date_str,
            "amount": amt_value,
            "currency": (str(amount.currency) if amount and amount.currency else "EUR"),
            "description": description,
            "merchant": merchant,
            "type": "BOOKING",
            "status": "BOOKED",
        })
    return transactions


# ─── CAMT.053 (ISO 20022) ──────────────────────────────────────
_CAMT_NS_RE = re.compile(r"\{[^}]+\}")


def _strip_ns(tag: str) -> str:
    return _CAMT_NS_RE.sub("", tag)


def _findtext_local(elem, *names: str) -> str:
    """Find the first descendant whose local-name matches any of the
    given names, return its text. Avoids the namespace verbosity of
    ElementTree."""
    target = set(names)
    for child in elem.iter():
        if _strip_ns(child.tag) in target and child.text:
            return child.text.strip()
    return ""


def _entry_amount(entry) -> tuple[float, str]:
    amount_elem = None
    cdtdbt = ""
    for child in entry.iter():
        local = _strip_ns(child.tag)
        if local == "Amt" and amount_elem is None:
            amount_elem = child
        elif local == "CdtDbtInd" and not cdtdbt:
            cdtdbt = (child.text or "").strip().upper()
        if amount_elem is not None and cdtdbt:
            break
    if amount_elem is None:
        return 0.0, "EUR"
    try:
        value = float(amount_elem.text)
    except (TypeError, ValueError):
        value = 0.0
    currency = amount_elem.attrib.get("Ccy", "EUR")
    if cdtdbt == "DBIT":
        value = -abs(value)
    else:
        value = abs(value)
    return value, currency


def parse_camt053(raw: bytes) -> List[NormalizedTx]:
    transactions: List[NormalizedTx] = []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return transactions

    # We don't know the exact namespace prefix (versioned), so iterate
    # generically. Statements can contain multiple <Stmt> blocks, each
    # with multiple <Ntry> entries.
    for entry in root.iter():
        if _strip_ns(entry.tag) != "Ntry":
            continue

        amount, currency = _entry_amount(entry)

        booking_date = ""
        for child in entry.iter():
            if _strip_ns(child.tag) == "BookgDt":
                booking_date = _findtext_local(child, "Dt", "DtTm")[:10]
                break
        if not booking_date:
            for child in entry.iter():
                if _strip_ns(child.tag) == "ValDt":
                    booking_date = _findtext_local(child, "Dt", "DtTm")[:10]
                    break

        description = _findtext_local(entry, "Ustrd", "AddtlNtryInf", "AddtlTxInf")
        # Counterparty: for an outgoing tx the creditor is the merchant;
        # for incoming, the debtor is the payer. We fish out either.
        merchant = ""
        for child in entry.iter():
            local = _strip_ns(child.tag)
            if local in ("Cdtr", "Dbtr"):
                name = _findtext_local(child, "Nm")
                if name:
                    merchant = name
                    break

        ext_id = (
            _findtext_local(entry, "AcctSvcrRef", "EndToEndId", "TxId")
            or f"camt053:{booking_date}:{amount}:{(description or '')[:40]}"
        )

        transactions.append({
            "id": ext_id,
            "date": booking_date or None,
            "amount": amount,
            "currency": currency,
            "description": description,
            "merchant": merchant,
            "type": "BOOKING",
            "status": "BOOKED",
        })
    return transactions


def parse_statement(raw: bytes) -> tuple[str, List[NormalizedTx]]:
    """Auto-detect format and parse. Returns (format, transactions)."""
    fmt = detect_format(raw)
    if fmt == "mt940":
        return fmt, parse_mt940(raw)
    if fmt == "camt053":
        return fmt, parse_camt053(raw)
    return fmt, []
