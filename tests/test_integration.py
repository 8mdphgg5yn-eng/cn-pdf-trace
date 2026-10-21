import json

import pytest

from cntrace.core import convert
from fixture_metrics import evaluate

pytestmark = pytest.mark.integration


def overlaps(a, b):
    # The drawing-time text center must fall inside the parser's region.
    x, y = (b[0]+b[2])/2, (b[1]+b[3])/2
    return a[0]-2 <= x <= a[2]+2 and a[1]-2 <= y <= a[3]+2


def test_all_successes_and_all_checkpoints_against_independent_gold(outputs, gold):
    for document in gold["documents"]:
        stem = document["pdf"].removesuffix(".pdf")
        ledger = json.loads((outputs[stem]/"provenance.json").read_text())
        metrics = evaluate(document, ledger)
        assert not metrics["false_successes"], metrics
        for name, policy in (("native_region_points", "min_native_verified_coverage"),
                             ("ocr_candidate_points", "min_ocr_candidate_coverage")):
            if metrics[name]["total"]:
                assert metrics[name]["rate"] >= document["acceptance"][policy], metrics


def test_physical_page_and_printed_label_are_separate(outputs, gold):
    for document in gold["documents"]:
        stem = document["pdf"].removesuffix(".pdf")
        ledger = json.loads((outputs[stem]/"provenance.json").read_text())
        for actual, expected in zip(ledger["pages"], document["pages"], strict=True):
            assert actual["pdf_page"] == expected["pdf_page"]
            assert actual["pdf_page_label"] == expected.get("pdf_page_label")
            if expected["text_origin"] == "native":
                assert actual["printed_page_label"] == expected["printed_page_label"]
            else:
                assert actual["printed_page_label"] is None
                assert actual.get("ocr_printed_label_status") in {"needs_review", "not_found"}


def test_cross_page_table_stays_as_two_physical_fragments(outputs):
    ledger = json.loads((outputs["settlement"]/"provenance.json").read_text())
    tables = [r for r in ledger["records"] if any(
        s["label"] == "table" for s in r["sources"])]
    assert len(tables) == 2
    assert [{loc["pdf_page"] for s in r["sources"] for loc in s["locations"]}
            for r in tables] == [{1}, {2}]


@pytest.mark.parametrize("stem", ["contract", "settlement", "creditors", "creditors_merged",
    "table_three_pages", "table_no_header", "page_labels", "scan_contract", "scan_degraded", "hybrid"])
def test_three_runs_identical_core_mapping(root, outputs, converters, gold, tmp_path, stem):
    original = json.loads((outputs[stem]/"provenance.json").read_text())
    expected_md = (outputs[stem]/"document.md").read_bytes()
    mode = next(d["ocr"] for d in gold["documents"] if d["pdf"] == stem+".pdf")
    for run in (2, 3):
        out = tmp_path/f"run{run}"
        current = convert(root/f"fixtures/{stem}.pdf", out, root/".cache/models",
                          converter=converters[mode], ocr=mode)
        assert (out/"document.md").read_bytes() == expected_md
        for key in ("records", "pages", "config_sha256", "markdown_sha256"):
            assert current[key] == original[key]


def test_actual_image_only_conversion_is_not_reported_verified(root, converter, tmp_path):
    import pypdfium2 as pdfium
    from cntrace.core import verify

    source = tmp_path/"image-only.pdf"
    doc = pdfium.PdfDocument(str(root/"fixtures/contract.pdf"))
    page = doc[0]
    bitmap = page.render(scale=1)
    bitmap.to_pil().save(source, "PDF")
    bitmap.close()
    page.close()
    doc.close()
    out = tmp_path/"unsupported"
    convert(source, out, root/".cache/models", converter=converter)
    report = verify(source, out)
    assert report["status"] == "issues_found"
    assert report["counts"].get("verified", 0) == 0
    assert "unsupported_no_text_layer" in {f["kind"] for f in report["findings"]}
