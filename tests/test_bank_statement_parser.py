"""Smoke tests for the MT940 and CAMT.053 parsers. Synthetic but
realistic samples — derived from minimal versions of what NL banks
actually emit (ING / Rabobank for MT940, ABN AMRO for CAMT.053)."""

from app.services.bank_statement_parser import (
    detect_format,
    parse_camt053,
    parse_mt940,
    parse_statement,
)

# ─── MT940 sample (ING-style) ──────────────────────────────────
MT940_SAMPLE = (
    ":20:STATEMENT0001\r\n"
    ":25:NL12INGB0001234567EUR\r\n"
    ":28C:1\r\n"
    ":60F:C260501EUR1000,00\r\n"
    ":61:2605030503D33,58NOVBNL00\r\n"
    ":86:Hellofresh weekbox week 18\r\n"
    ":61:2605040504C2111,95NMSCREF12345\r\n"
    ":86:SALARIS WERKGEVER BV\r\n"
    ":62F:C260504EUR3078,37\r\n"
).encode("latin-1")


# ─── CAMT.053 sample (minimal but valid) ──────────────────────
CAMT053_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <Stmt>
      <Id>STMT-1</Id>
      <Acct><Id><IBAN>NL12ABNA0000123456</IBAN></Id></Acct>
      <Ntry>
        <Amt Ccy="EUR">33.58</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt><Dt>2026-05-03</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <RltdPties><Cdtr><Nm>HELLOFRESH NL</Nm></Cdtr></RltdPties>
            <RmtInf><Ustrd>Weekbox week 18</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">2111.95</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-05-04</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <RltdPties><Dbtr><Nm>WERKGEVER BV</Nm></Dbtr></RltdPties>
            <RmtInf><Ustrd>Salaris mei</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
""".encode("utf-8")


# ═══════════════════════════════════════════════════════════════
# detect_format
# ═══════════════════════════════════════════════════════════════
def test_detect_format_recognises_mt940():
    assert detect_format(MT940_SAMPLE) == "mt940"


def test_detect_format_recognises_camt053():
    assert detect_format(CAMT053_SAMPLE) == "camt053"


def test_detect_format_unknown_for_garbage():
    assert detect_format(b"this is not a bank statement") == "unknown"


# ═══════════════════════════════════════════════════════════════
# parse_mt940
# ═══════════════════════════════════════════════════════════════
def test_mt940_parses_two_transactions():
    txs = parse_mt940(MT940_SAMPLE)
    assert len(txs) == 2


def test_mt940_extracts_signs_correctly():
    txs = parse_mt940(MT940_SAMPLE)
    # Outgoing first, incoming second.
    outgoing = txs[0]
    incoming = txs[1]
    assert outgoing["amount"] < 0
    assert abs(outgoing["amount"]) == 33.58
    assert incoming["amount"] > 0
    assert incoming["amount"] == 2111.95


def test_mt940_dates_are_iso():
    txs = parse_mt940(MT940_SAMPLE)
    for t in txs:
        # Either YYYY-MM-DD or None; never a python date object.
        assert t["date"] is None or len(t["date"]) == 10


# ═══════════════════════════════════════════════════════════════
# parse_camt053
# ═══════════════════════════════════════════════════════════════
def test_camt053_parses_two_transactions():
    txs = parse_camt053(CAMT053_SAMPLE)
    assert len(txs) == 2


def test_camt053_extracts_signs_correctly():
    txs = parse_camt053(CAMT053_SAMPLE)
    by_amount = {abs(t["amount"]): t for t in txs}
    assert by_amount[33.58]["amount"] < 0
    assert by_amount[2111.95]["amount"] > 0


def test_camt053_extracts_merchant():
    txs = parse_camt053(CAMT053_SAMPLE)
    merchants = sorted([t["merchant"] for t in txs])
    assert merchants == ["HELLOFRESH NL", "WERKGEVER BV"]


def test_camt053_extracts_descriptions():
    txs = parse_camt053(CAMT053_SAMPLE)
    descriptions = sorted([t["description"] for t in txs])
    assert "Weekbox week 18" in descriptions
    assert "Salaris mei" in descriptions


def test_camt053_dates_are_iso_strings():
    txs = parse_camt053(CAMT053_SAMPLE)
    for t in txs:
        assert t["date"] in ("2026-05-03", "2026-05-04")


# ═══════════════════════════════════════════════════════════════
# parse_statement (auto-detect)
# ═══════════════════════════════════════════════════════════════
def test_parse_statement_auto_routes_mt940():
    fmt, txs = parse_statement(MT940_SAMPLE)
    assert fmt == "mt940"
    assert len(txs) == 2


def test_parse_statement_auto_routes_camt053():
    fmt, txs = parse_statement(CAMT053_SAMPLE)
    assert fmt == "camt053"
    assert len(txs) == 2


def test_parse_statement_returns_empty_for_unknown():
    fmt, txs = parse_statement(b"random bytes")
    assert fmt == "unknown"
    assert txs == []
