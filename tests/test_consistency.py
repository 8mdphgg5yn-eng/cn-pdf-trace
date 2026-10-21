import copy
import json
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from pypdf import PdfWriter

from cntrace.core import (
    BLOCK, PdfEvidence, check_serialization, file_digest, local_pdf, locate_quote,
    normalize, offline_guard, verify,
)


def clone(outputs, tmp_path, stem="contract"):
    target = tmp_path/stem
    shutil.copytree(outputs[stem], target)
    return target


def kinds(report):
    return {f["kind"] for f in report["findings"]}


def test_originals_pass_and_three_outputs_exist(root, outputs):
    for stem in ("contract", "settlement"):
        bundle = outputs[stem]
        assert sorted(p.name for p in bundle.iterdir()) == [
            "check-report.md", "document.md", "provenance.json"]
        result = verify(root/f"fixtures/{stem}.pdf", bundle)
        assert result["status"] == "ok", result
        assert result["counts"]["verified"] == result["records_total"] > 0


@pytest.mark.parametrize(("stem", "quote", "pages"), [
    ("contract", "双方应当保存交付记录。", [2, 3]),
    ("contract", "50,000.00", [2, 3]),
    ("settlement", "50,000.00", [1, 1]),
    ("settlement", "项目名称", [1, 2]),
])
def test_duplicate_quote_never_selects_first(root, outputs, stem, quote, pages):
    report = verify(root/f"fixtures/{stem}.pdf", outputs[stem], quote=quote)
    assert report["status"] == "issues_found"
    assert "query_ambiguous" in kinds(report)
    query = report["query"]
    assert query["status"] == "ambiguous"
    assert sorted(c["locations"][0]["pdf_page"] for c in query["candidates"]) == pages


def test_unique_quote_is_region_not_character_precision(root, outputs):
    query = verify(root/"fixtures/contract.pdf", outputs["contract"], quote="保修期限")["query"]
    assert query["status"] == "located_in_region"
    assert len(query["candidates"]) == 1
    assert query["candidates"][0]["locations"][0]["pdf_page"] == 3
    assert "not_exact_quote_bbox" in query["precision"]


@pytest.mark.parametrize("quote", ["不存在的摘录", "伍万元", "50000.00", "", "   "])
def test_no_fuzzy_financial_substitution(outputs, quote):
    ledger = json.loads((outputs["contract"]/"provenance.json").read_text())
    query = locate_quote(ledger, quote)
    assert query["status"] in {"unresolved", "unsupported"}
    assert not query["candidates"]


def test_excerpt_edit_is_reported(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"document.md"
    path.write_text(path.read_text().replace("100,000.00", "900,000.00", 1))
    result = verify(root/"fixtures/contract.pdf", bundle)
    assert {"markdown_changed", "excerpt_changed"} <= kinds(result)
    assert not result["source_changed"]


def test_missing_anchor_is_not_recovered_by_first_text_match(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"document.md"
    text = path.read_text()
    m = next(m for m in BLOCK.finditer(text) if "双方应当保存" in m[2])
    path.write_text(text[:m.start()]+m[2]+text[m.end():])
    result = verify(root/"fixtures/contract.pdf", bundle)
    assert {"anchor_missing", "untracked_markdown_or_broken_anchor"} <= kinds(result)


def test_duplicated_anchor_reported(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"document.md"
    text = path.read_text()
    path.write_text(text+next(BLOCK.finditer(text))[0]+"\n\n")
    assert "duplicate_anchor" in kinds(verify(root/"fixtures/contract.pdf", bundle))


def test_extra_untracked_text_reported(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"document.md"
    path.write_text(path.read_text()+"用户新增且尚无出处的段落。\n")
    assert "untracked_markdown_or_broken_anchor" in kinds(
        verify(root/"fixtures/contract.pdf", bundle))


def test_byte_change_invalidates_all_old_locations(root, outputs, tmp_path):
    source = tmp_path/"changed.pdf"
    source.write_bytes((root/"fixtures/contract.pdf").read_bytes()+b"\n% byte-only test\n")
    result = verify(source, outputs["contract"], quote="保修期限")
    assert result["source_changed"]
    assert result["counts"].get("verified", 0) == 0
    assert result["query"]["status"] == "stale_source"
    assert "source_changed" in kinds(result)


def test_page_deletion_reported(root, outputs, tmp_path):
    source = tmp_path/"short.pdf"
    writer = PdfWriter(clone_from=root/"fixtures/contract.pdf")
    writer.remove_page(2)
    writer.write(source)
    assert "page_count_changed" in kinds(verify(source, outputs["contract"]))


def test_missing_provenance_rejected(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"provenance.json"
    ledger = json.loads(path.read_text())
    ledger["records"][0]["sources"][0]["locations"] = []
    path.write_text(json.dumps(ledger))
    result = verify(root/"fixtures/contract.pdf", bundle)
    assert "source_unresolved" in kinds(result)
    assert result["counts"].get("invalid", 0) >= 1


def test_wrong_region_cannot_trust_stored_verified_flag(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"provenance.json"
    ledger = json.loads(path.read_text())
    source = ledger["records"][0]["sources"][0]
    source["locations"][0]["bbox"] = [0, 0, 20, 20]
    source["verification"] = {"status": "verified"}
    path.write_text(json.dumps(ledger))
    assert "source_unresolved" in kinds(verify(root/"fixtures/contract.pdf", bundle))


@pytest.mark.parametrize("box", [[-1, 0, 5, 5], [0, 0, 9999, 10], [4, 4, 2, 2],
                                 [0, 0, float("nan"), 10]])
def test_invalid_coordinates_rejected(root, box):
    fragment = {"text": "测试", "locations": [{"pdf_page": 1, "bbox": box,
                "coord_origin": "TOPLEFT", "units": "pt"}]}
    with PdfEvidence(root/"fixtures/contract.pdf") as pdf:
        assert pdf.check_fragment(fragment)["status"] == "unresolved"


def test_scan_or_blank_page_is_explicitly_unsupported(root, outputs, tmp_path):
    source = tmp_path/"image-only.pdf"
    # Rasterize the self-created cover. No OCR or third-party source is involved.
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(root/"fixtures/contract.pdf"))
    page = doc[0]
    bitmap = page.render(scale=1)
    im = bitmap.to_pil()
    im.save(source, "PDF")
    bitmap.close()
    page.close()
    doc.close()
    result = verify(source, outputs["contract"])
    assert "unsupported_no_text_layer" in kinds(result)


def test_no_remote_or_nonexistent_input():
    with pytest.raises(ValueError):
        local_pdf(Path("https://example.invalid/customer.pdf"))


def test_network_guard_including_worker_threads():
    errors = []

    def attempt():
        try:
            socket.getaddrinfo("example.invalid", 443)
        except RuntimeError as exc:
            errors.append(str(exc))

    with offline_guard():
        attempt()
        thread = threading.Thread(target=attempt)
        thread.start()
        thread.join()
    assert len(errors) == 2
    assert all("network access denied" in x for x in errors)


def test_normalization_never_changes_digits():
    assert normalize("第 一条\n50,000.00 元") == "第一条50,000.00元"
    assert normalize("50,000.00") != normalize("50000.00")


def test_file_hash_matches_drawing_time_gold(root, gold):
    for document in gold["documents"]:
        assert file_digest(root/"fixtures"/document["pdf"]) == document["sha256"]


def test_cli_ambiguous_exit_and_json(root, outputs):
    result = subprocess.run([sys.executable, "-m", "cntrace.cli", "verify",
                             str(root/"fixtures/contract.pdf"), "--bundle",
                             str(outputs["contract"]), "--quote", "50,000.00"],
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["query"]["status"] == "ambiguous"


def test_schema_unknown_rejected(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"provenance.json"
    ledger = json.loads(path.read_text())
    ledger["schema_version"] = 100
    path.write_text(json.dumps(ledger))
    with pytest.raises(ValueError, match="unsupported_schema"):
        verify(root/"fixtures/contract.pdf", bundle)


def test_two_occurrences_in_same_source_are_ambiguous(outputs):
    ledger = copy.deepcopy(json.loads((outputs["contract"]/"provenance.json").read_text()))
    ledger["records"] = ledger["records"][:1]
    ledger["records"][0]["sources"] = ledger["records"][0]["sources"][:1]
    ledger["records"][0]["sources"][0]["text"] = "同文 同文"
    assert locate_quote(ledger, "同文")["status"] == "ambiguous"


def test_overlapping_occurrences_are_not_reported_unique(outputs):
    ledger = copy.deepcopy(json.loads((outputs["contract"]/"provenance.json").read_text()))
    ledger["records"] = ledger["records"][:1]
    ledger["records"][0]["sources"] = ledger["records"][0]["sources"][:1]
    ledger["records"][0]["sources"][0]["text"] = "甲甲甲"
    query = locate_quote(ledger, "甲甲")
    assert query["status"] == "ambiguous"
    assert [c["normalized_offset"] for c in query["candidates"]] == [0, 1]


def test_serialization_must_preserve_amounts():
    source = [{"text": "合同价款50,000.00元。"}]
    assert check_serialization("## 合同价款50,000.00元。", source)["status"] == "matched"
    assert check_serialization("合同价款50000.00元。", source)["status"] == "unresolved"
    assert check_serialization("<div>合同价款50,000.00元。</div>", source)["status"] == "unsupported"


def test_sidecar_change_to_another_identical_occurrence_detected(root, outputs, tmp_path):
    bundle = clone(outputs, tmp_path)
    path = bundle/"provenance.json"
    ledger = json.loads(path.read_text())
    sources = [s for r in ledger["records"] for s in r["sources"]
               if normalize(s["text"]) == "双方应当保存交付记录。"]
    assert len(sources) == 2
    sources[0]["locations"] = sources[1]["locations"]
    path.write_text(json.dumps(ledger))
    assert "provenance_changed" in kinds(verify(root/"fixtures/contract.pdf", bundle))


def test_fixture_generator_reproduces_original_bytes(root, tmp_path):
    out = tmp_path/"regenerated"
    result = subprocess.run([sys.executable, str(root/"scripts/make_fixtures.py"),
                             "--out", str(out), "--font",
                             str(root/".cache/fonts/NotoSansSC.ttf")],
                            text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr
    for name in [p.name for p in (root/"fixtures").glob("*.pdf")]+["gold.json"]:
        assert (out/name).read_bytes() == (root/"fixtures"/name).read_bytes()
