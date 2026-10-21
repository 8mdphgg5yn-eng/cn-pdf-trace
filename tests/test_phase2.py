import json
import shutil

import pytest

from cntrace.core import BLOCK, PdfEvidence, digest, verify


def load(outputs, stem):
    return json.loads((outputs[stem]/"provenance.json").read_text())


def test_exactly_ten_self_created_pdfs(root, gold, outputs):
    assert len(gold["documents"]) == len(outputs) == 10
    assert {p.name for p in (root/"fixtures").glob("*.pdf")} == {
        d["pdf"] for d in gold["documents"]}
    assert sum(len(d["pages"]) for d in gold["documents"]) == 21
    for stem, bundle in outputs.items():
        assert sorted(p.name for p in bundle.iterdir()) == [
            "check-report.md", "document.md", "provenance.json"]


@pytest.mark.parametrize("stem", ["scan_contract", "scan_degraded"])
def test_scans_never_gain_verified_status(root, outputs, stem):
    ledger = load(outputs, stem)
    assert ledger["parser"]["ocr"] == "mac"
    assert ledger["parser"]["ocr_options"]["framework"] == "vision"
    with PdfEvidence(root/f"fixtures/{stem}.pdf") as evidence:
        assert all(not p["native_text_available"] for p in evidence.pages)
    assert ledger["records"]  # OCR actually ran; this is not a skip-only test.
    assert all(r["status"] != "verified" for r in ledger["records"])
    assert all(s["text_origin"] == "ocr" and s["verification"]["status"] != "verified"
               for r in ledger["records"] for s in r["sources"])
    report = verify(root/f"fixtures/{stem}.pdf", outputs[stem])
    assert report["status"] == "issues_found"
    assert report["counts"].get("verified", 0) == 0
    assert "ocr_page_requires_review" in {f["kind"] for f in report["findings"]}


def test_hybrid_source_status_and_ambiguous_amount(root, outputs):
    ledger = load(outputs, "hybrid")
    for record in ledger["records"]:
        for source in record["sources"]:
            page = source["locations"][0]["pdf_page"]
            assert source["verification"]["status"] == ("verified" if page == 1 else "needs_review")
    report = verify(root/"fixtures/hybrid.pdf", outputs["hybrid"], quote="30,000.00")
    assert report["query"]["status"] == "ambiguous"
    assert len(report["query"]["candidates"]) == 2
    assert {c["verification"] for c in report["query"]["candidates"]} == {"verified", "needs_review"}


def test_unique_ocr_quote_is_only_candidate(root, outputs):
    report = verify(root/"fixtures/hybrid.pdf", outputs["hybrid"], quote="HX-02")
    assert report["query"]["status"] == "needs_review"
    assert report["status"] == "issues_found"
    assert report["query"]["candidates"][0]["locations"][0]["pdf_page"] == 2


def test_ocr_printed_page_labels_are_candidates(outputs):
    for p in load(outputs, "scan_contract")["pages"]:
        assert p["printed_page_label"] is None
        assert p["ocr_printed_label_status"] == "needs_review"
        assert p["ocr_printed_page_candidates"] == [str(50+p["pdf_page"])]


def test_three_distinct_page_number_concepts(root, outputs):
    ledger = load(outputs, "page_labels")
    assert [p["pdf_page"] for p in ledger["pages"]] == [1, 2, 3]
    assert [p["pdf_page_label"] for p in ledger["pages"]] == ["i", "A-10", "A-11"]
    assert [p["printed_page_label"] for p in ledger["pages"]] == [None, "21", None]
    page = ledger["pages"][2]
    assert page["printed_label_status"] == "ambiguous"
    assert page["printed_label_candidates"] == ["22", "99"]
    assert "printed_page_label_ambiguous" in {
        f["kind"] for f in verify(root/"fixtures/page_labels.pdf", outputs["page_labels"])["findings"]}


@pytest.mark.parametrize(("stem", "count"), [("table_three_pages", 3), ("table_no_header", 2)])
def test_complex_tables_are_not_silently_stitched(outputs, stem, count):
    ledger = load(outputs, stem)
    tables = [r for r in ledger["records"] if any(s["label"] == "table" for s in r["sources"])]
    assert len(tables) == count
    assert [{loc["pdf_page"] for s in r["sources"] for loc in s["locations"]}
            for r in tables] == [{i} for i in range(1, count+1)]


def test_merged_header_transformation_is_not_called_verbatim(root, outputs):
    ledger = load(outputs, "creditors_merged")
    table = next(r for r in ledger["records"] if any(s["label"] == "table" for s in r["sources"]))
    assert any(s["col_span"] > 1 for s in table["sources"])
    assert table["serialization_check"]["status"] == "unresolved"
    assert table["status"] == "unresolved"
    assert "export_source_text_mismatch" in {
        f["kind"] for f in verify(root/"fixtures/creditors_merged.pdf",
                                 outputs["creditors_merged"])["findings"]}


def test_silently_deleted_native_paragraph_is_reported(root, outputs, tmp_path):
    bundle = tmp_path/"dropped"
    shutil.copytree(outputs["contract"], bundle)
    path = bundle/"provenance.json"
    ledger = json.loads(path.read_text())
    removed = ledger["records"].pop(0)
    md = (bundle/"document.md").read_text()
    match = next(m for m in BLOCK.finditer(md) if m[1] == removed["id"])
    md = md[:match.start()]+md[match.end():]
    (bundle/"document.md").write_text(md)
    ledger["markdown_sha256"] = digest(md.encode())
    path.write_text(json.dumps(ledger))
    report = verify(root/"fixtures/contract.pdf", bundle)
    gaps = [f for f in report["findings"] if f["kind"] == "native_text_not_covered"]
    assert gaps and any("设备采购合同" in f["text"] for f in gaps)


@pytest.mark.parametrize("stem", ["creditors", "table_three_pages", "scan_contract", "scan_degraded"])
def test_pdf_change_invalidates_native_and_ocr_locations(root, outputs, tmp_path, stem):
    path = tmp_path/f"{stem}.pdf"
    path.write_bytes((root/f"fixtures/{stem}.pdf").read_bytes()+b"\n% phase2 mutation\n")
    report = verify(path, outputs[stem], quote="30,000.00")
    assert report["source_changed"]
    assert report["counts"].get("verified", 0) == 0
    assert report["counts"].get("needs_review", 0) == 0
    assert report["query"]["status"] == "stale_source"
