"""Small, conservative provenance adapter around Docling's public serializers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import platform
import re
import sys
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import pypdfium2 as pdfium
from markdown_it import MarkdownIt
from pypdf import PdfReader

from . import __version__

SCHEMA = 2
PROLOGUE = ("<!-- cntrace:generated -->\n"
            "本文件由本地解析器导出。来源见同目录 provenance.json；"
            "页序与印刷页码分开记录，哈希仅用于一致性核验。\n\n")
BLOCK = re.compile(r"<!-- cntrace:([a-f0-9]{24}) -->\n(.*?)\n<!-- /cntrace:\1 -->", re.S)
_offline_depth = 0


def _network_audit(event, args):
    if _offline_depth and event in {"socket.connect", "socket.getaddrinfo", "socket.bind"}:
        raise RuntimeError("cntrace: network access denied during local processing")


sys.addaudithook(_network_audit)


@contextmanager
def offline_guard():
    """Reject Python socket operations, including attempts from model loaders.

    This is defense in depth, not an OS firewall for arbitrary native extensions.
    """
    global _offline_depth
    _offline_depth += 1
    try:
        yield
    finally:
        _offline_depth -= 1


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def source_binding(sources: list[dict]) -> str:
    """Checksum the source description, excluding its derived verification flag."""
    return digest(canonical([{k: v for k, v in s.items() if k != "verification"}
                             for s in sources]).encode())


def normalize(text: str) -> str:
    """Only remove whitespace. Never normalize amounts, punctuation, or digits."""
    return re.sub(r"\s+", "", text)


def check_serialization(markdown: str, sources: list[dict]) -> dict:
    """Compare visible Markdown text with the associated parser fragments.

    No second PDF-wide search is used. Unsupported embedded HTML/images/code
    are explicit; we do not silently strip arbitrary constructs to get a match.
    """
    text = []
    for token in MarkdownIt("commonmark").enable("table").parse(markdown):
        if token.type in {"html_block", "fence", "code_block"}:
            return {"status": "unsupported", "reason": "unsupported_markdown_construct"}
        if token.type != "inline":
            continue
        for child in token.children or []:
            if child.type in {"text", "code_inline"}:
                text.append(child.content)
            elif child.type in {"softbreak", "hardbreak"}:
                text.append("\n")
            elif child.type == "html_inline" and child.content.lower() in {"<br>", "<br/>", "<br />"}:
                text.append("\n")
            elif child.type in {"html_inline", "image"}:
                return {"status": "unsupported", "reason": "unsupported_markdown_construct"}
    expected = "".join(s["text"] for s in sources)
    if not sources or normalize("".join(text)) != normalize(expected):
        return {"status": "unresolved", "reason": "export_source_text_mismatch"}
    return {"status": "matched", "method": "markdown_visible_text_exact_except_whitespace"}


def local_pdf(path: Path) -> Path:
    # Existing local PDFs only. A URL cannot be treated as a download request.
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise ValueError("输入必须是已经存在的本地 PDF 文件")
    return path.resolve()


class PdfEvidence:
    """Independent PDFium native text and geometry checks; no OCR."""

    def __init__(self, path: Path):
        self.doc = pdfium.PdfDocument(str(path))
        self.pages = []
        reader = PdfReader(path)
        labels = reader.page_labels if "/PageLabels" in reader.trailer["/Root"] else None
        for i in range(len(self.doc)):
            page = self.doc[i]
            w, h = page.get_size()
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            footer = textpage.get_text_bounded(left=0, bottom=0, right=w, top=h*.12)
            matches = list(re.finditer(r"第\s*([0-9一二三四五六七八九十百零〇]+)\s*页", footer))
            self.pages.append({
                "pdf_page": i+1, "width": w, "height": h, "units": "pt",
                "printed_page_label": matches[0].group(1) if len(matches) == 1 else None,
                "printed_label_status": "recognized" if len(matches) == 1 else
                                        "ambiguous" if matches else "not_found",
                "printed_label_candidates": [m.group(1) for m in matches],
                "printed_label_method": "native_footer_text_explicit_di_ye_pattern",
                "pdf_page_label": labels[i] if labels else None,
                "native_text_available": bool(normalize(text)),
            })
            textpage.close()
            page.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.doc.close()

    def region_text(self, loc: dict) -> str:
        p = loc["pdf_page"]
        if not isinstance(p, int) or isinstance(p, bool) or not 1 <= p <= len(self.pages):
            raise ValueError("page_out_of_range")
        if loc.get("coord_origin") != "TOPLEFT" or loc.get("units") != "pt":
            raise ValueError("unsupported_coordinate_system")
        box = loc.get("bbox")
        if not isinstance(box, list) or len(box) != 4:
            raise ValueError("invalid_bbox")
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in box):
            raise ValueError("invalid_bbox")
        left, top, right, bottom = box
        meta = self.pages[p-1]
        w, h = meta["width"], meta["height"]
        if not (0 <= left < right <= w+0.1 and 0 <= top < bottom <= h+0.1):
            raise ValueError("bbox_out_of_range")
        page = self.doc[p-1]
        text = page.get_textpage()
        try:
            # PDFium uses bottom-left PDF coordinates. Expansion only tolerates
            # subpoint font/rounding differences, not a search of the whole page.
            return text.get_text_bounded(left=max(0, left-1), bottom=max(0, h-bottom-1),
                                         right=min(w, right+1), top=min(h, h-top+1))
        finally:
            text.close()
            page.close()

    def check_fragment(self, frag: dict) -> dict:
        if not frag.get("locations"):
            return {"status": "unresolved", "reason": frag.get("reason", "missing_provenance")}
        if not normalize(frag.get("text", "")):
            return {"status": "unsupported", "reason": "empty_text"}
        texts = []
        try:
            for loc in frag["locations"]:
                texts.append(self.region_text(loc))
        except (KeyError, ValueError, TypeError) as exc:
            return {"status": "unresolved", "reason": str(exc)}
        if frag.get("text_origin") == "ocr":
            return {"status": "needs_review", "reason": "ocr_region_requires_visual_review",
                    "method": "parser_ocr_geometry_only_not_independent_text_verification"}
        if normalize("".join(texts)) != normalize(frag["text"]):
            return {"status": "unresolved", "reason": "native_region_text_mismatch",
                    "region_text": "\n".join(texts)}
        return {"status": "verified", "method": "native_region_exact_except_whitespace",
                "region_text": "\n".join(texts)}

    def uncovered_native_text(self, sources: list[dict]) -> list[dict]:
        """Detect native glyphs silently omitted by parsing/serialization.

        This uses the PDF, not a known-answer fixture. Covered but mismatching
        regions are handled separately by check_fragment.
        """
        by_page = {}
        for source in sources:
            for loc in source.get("locations", []):
                try:
                    self.region_text(loc)  # validate before using the rectangle
                except (ValueError, KeyError, TypeError):
                    continue
                by_page.setdefault(loc["pdf_page"], []).append(loc["bbox"])
        missing = []
        for number, meta in enumerate(self.pages, 1):
            page = self.doc[number-1]
            text = page.get_textpage()
            run = []
            boxes = []

            def flush():
                if run:
                    missing.append({"pdf_page": number, "text": "".join(run),
                                    "bbox": [min(b[0] for b in boxes), min(b[1] for b in boxes),
                                             max(b[2] for b in boxes), max(b[3] for b in boxes)],
                                    "coord_origin": "TOPLEFT", "units": "pt"})
                    run.clear()
                    boxes.clear()

            for i in range(text.count_chars()):
                value = text.get_text_range(i, 1)
                if not normalize(value):
                    continue
                left, bottom, right, top = text.get_charbox(i)
                box = [left, meta["height"]-top, right, meta["height"]-bottom]
                x, y = (box[0]+box[2])/2, (box[1]+box[3])/2
                if any(b[0]-1 <= x <= b[2]+1 and b[1]-1 <= y <= b[3]+1
                       for b in by_page.get(number, [])):
                    flush()
                else:
                    run.append(value)
                    boxes.append(box)
            flush()
            text.close()
            page.close()
        return missing


def check_models(model_dir: Path) -> tuple[dict, str]:
    manifest = model_dir / "manifest.json"
    if not manifest.is_file():
        raise ValueError("缺少本地模型清单；先执行 scripts/prepare_assets.py")
    data = json.loads(manifest.read_text())
    if not data.get("files"):
        raise ValueError("empty_model_manifest")
    root = model_dir.resolve()
    for entry in data["files"]:
        path = (root / entry["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("missing_model_file")
        if file_digest(path) != entry["sha256"]:
            raise ValueError("model_hash_mismatch")
    return data, digest(canonical(data).encode())


def build_converter(model_dir: Path, *, ocr="off"):
    # Imports deliberately deferred: verification needs no model or torch import.
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import OcrMacOptions, PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    if ocr not in {"off", "mac"}:
        raise ValueError("unsupported_ocr_engine")
    if ocr == "mac" and sys.platform != "darwin":
        raise ValueError("mac_ocr_requires_macos")
    opts = PdfPipelineOptions(artifacts_path=model_dir.resolve(), do_ocr=ocr != "off",
                              do_table_structure=True, enable_remote_services=False,
                              enable_external_plugins=False)
    if ocr == "mac":
        opts.ocr_options = OcrMacOptions(lang=["zh-Hans", "en-US"], recognition="accurate",
                                         framework="vision")
    opts.table_structure_options.mode = TableFormerMode.ACCURATE
    opts.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU, num_threads=2)
    return DocumentConverter(allowed_formats=[InputFormat.PDF], format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})


def _loc(prov, doc, *, bbox=None, granularity="text_block"):
    page = doc.pages.get(prov.page_no)
    if page is None:
        return None
    box = (bbox or prov.bbox).to_top_left_origin(page_height=page.size.height)
    return {"pdf_page": prov.page_no,
            "bbox": [round(box.l, 5), round(box.t, 5), round(box.r, 5), round(box.b, 5)],
            "coord_origin": "TOPLEFT", "units": "pt", "granularity": granularity,
            "parser_charspan": list(prov.charspan)}


def item_fragments(item, doc) -> list[dict]:
    from docling_core.types.doc import TableItem, TextItem

    base = {"docling_ref": item.self_ref, "label": item.label.value,
            "text_origin": "native_pdf_text"}
    fragments = []
    if isinstance(item, TableItem):
        # A cell bbox carries no page number of its own. Only a single-page
        # table lets us attach it without guessing.
        pages = {p.page_no for p in item.prov}
        for i, cell in enumerate(item.data.table_cells):
            if not normalize(cell.text):
                continue
            locs = []
            if len(pages) == 1 and cell.bbox is not None:
                loc = _loc(item.prov[0], doc, bbox=cell.bbox, granularity="table_cell")
                if loc:
                    locs.append(loc)
            fragments.append({**base, "source_id": f"{item.self_ref}/cells/{i}",
                              "text": cell.text, "raw_parser_text": cell.text,
                              "row": cell.start_row_offset_idx,
                              "col": cell.start_col_offset_idx,
                              "row_span": cell.row_span, "col_span": cell.col_span,
                              "locations": locs,
                              "reason": "missing_or_ambiguous_cell_geometry" if not locs else None})
    elif isinstance(item, TextItem):
        for i, prov in enumerate(item.prov):
            start, end = prov.charspan
            loc = _loc(prov, doc)
            valid_span = 0 <= start < end <= len(item.text)
            fragments.append({**base, "source_id": f"{item.self_ref}/prov/{i}",
                              "text": item.text[start:end] if valid_span else item.text,
                              "raw_parser_text": item.orig,
                              "locations": [loc] if loc and valid_span else [],
                              "reason": "invalid_charspan" if not valid_span else None})
        if not item.prov:
            fragments.append({**base, "source_id": item.self_ref, "text": item.text,
                              "raw_parser_text": item.orig, "locations": [],
                              "reason": "missing_provenance"})
    else:
        fragments.append({**base, "source_id": item.self_ref, "text": "",
                          "locations": [], "reason": "unsupported_item_type"})
    return fragments


def convert(pdf: Path, output: Path, models: Path, *, converter=None, ocr="off") -> dict:
    pdf = local_pdf(pdf)
    if output.resolve() == pdf.parent and pdf.name in {"document.md", "provenance.json"}:
        raise ValueError("output_conflicts_with_input")
    output.mkdir(parents=True, exist_ok=True)
    manifest, model_hash = check_models(models)
    versions = {p: importlib.metadata.version(p) for p in
                ("docling-slim", "docling-core", "docling-parse", "docling-ibm-models",
                 "torch", "transformers", "pypdfium2", "markdown-it-py", "opencv-python-headless")}
    if ocr == "mac":
        versions.update({p: importlib.metadata.version(p) for p in
                         ("ocrmac", "pyobjc-framework-Vision")})
    config = {"tool_version": __version__, "versions": versions,
              "models_sha256": model_hash, "ocr": ocr, "device": "cpu",
              "threads": 2, "table_mode": "accurate", "remote_services": False,
              "external_plugins": False, "normalization": "remove_whitespace_only"}
    config["export_labels"] = "all_including_page_furniture"
    config["export_layers"] = "all"
    config["ocr_options"] = {"framework": "vision", "recognition": "accurate",
                             "languages": ["zh-Hans", "en-US"], "mode": "auto",
                             "macos_version": platform.mac_ver()[0]} if ocr == "mac" else None
    config_hash = digest(canonical(config).encode())
    pdf_hash = file_digest(pdf)
    start = time.perf_counter()
    with offline_guard():
        converter = converter or build_converter(models, ocr=ocr)
        from docling.datamodel.base_models import InputFormat
        actual = converter.format_to_options[InputFormat.PDF].pipeline_options
        if actual.do_ocr != (ocr != "off") or (ocr == "mac" and actual.ocr_options.kind != "ocrmac"):
            raise ValueError("converter_configuration_mismatch")
        result = converter.convert(pdf, raises_on_error=False)
        doc = result.document
        from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams
        from docling_core.types.doc import ContentLayer, DocItemLabel
        serializer = MarkdownDocSerializer(doc=doc, params=MarkdownParams(
            labels=set(DocItemLabel), layers=set(ContentLayer)))
        parts = serializer.get_parts()
        with PdfEvidence(pdf) as evidence:
            records = []
            markdown = PROLOGUE
            for index, part in enumerate(parts):
                text = part.text.strip()
                if not text:
                    continue
                sources = []
                for item in part.get_unique_doc_items():
                    sources.extend(item_fragments(item, doc))
                for source in sources:
                    # A scan page must never inherit the native-text success flag.
                    pages = {loc["pdf_page"] for loc in source["locations"]}
                    if pages and any(not evidence.pages[p-1]["native_text_available"] for p in pages):
                        source["text_origin"] = "ocr" if ocr != "off" else "unknown"
                    source["verification"] = evidence.check_fragment(source)
                statuses = [s["verification"]["status"] for s in sources]
                serialization = check_serialization(text, sources)
                status = "verified" if statuses and all(x == "verified" for x in statuses) else \
                         "needs_review" if statuses and all(x in {"verified", "needs_review"}
                                                           for x in statuses) else \
                         "unsupported" if not statuses or all(x == "unsupported" for x in statuses) \
                         else "unresolved"
                if serialization["status"] != "matched":
                    status = serialization["status"]
                key = {"pdf": pdf_hash, "config": config_hash, "part": index,
                       "sources": [s["source_id"] for s in sources], "text": text}
                rid = digest(canonical(key).encode())[:24]
                opening = f"<!-- cntrace:{rid} -->\n"
                begin = len(markdown)+len(opening)
                markdown += opening+text+f"\n<!-- /cntrace:{rid} -->\n\n"
                records.append({"id": rid, "ordinal": len(records)+1, "markdown_text": text,
                                "markdown_sha256": digest(text.encode()),
                                "source_binding_sha256": source_binding(sources),
                                "markdown_range": [begin, begin+len(text)],
                                "range_unit": "unicode_codepoint_start_inclusive_end_exclusive",
                                "status": status, "serialization_check": serialization,
                                "sources": sources})
            ledger = {
                "schema_version": SCHEMA,
                "document": {"filename": pdf.name, "sha256": pdf_hash,
                             "hash_purpose": "byte_consistency_only_not_judicial_authenticity",
                             "page_count": len(evidence.pages)},
                "parser": config, "config_sha256": config_hash,
                "models": manifest["models"], "pages": evidence.pages,
                "markdown_sha256": digest(markdown.encode()),
                "records": records,
                "conversion": {"status": result.status.value,
                               "errors": [str(e) for e in result.errors],
                               "elapsed_seconds": round(time.perf_counter()-start, 3)},
                "limitations": ["ocr_candidates_require_visual_review", "no_automatic_table_stitching",
                                "printed_labels_only_explicit_footer_pattern",
                                "region_geometry_not_character_geometry",
                                "ids_stable_only_for_identical_input_and_locked_environment",
                                "hashes_are_not_signatures_or_authenticity_proof"],
            }
            for page in ledger["pages"]:
                if not page["native_text_available"] and ocr != "off":
                    candidates = []
                    for record in records:
                        for source in record["sources"]:
                            if any(loc["pdf_page"] == page["pdf_page"] and
                                   loc["bbox"][1] > page["height"]*.88
                                   for loc in source["locations"]):
                                candidates += re.findall(r"第\s*([0-9一二三四五六七八九十百零〇]+)\s*页",
                                                         source["text"])
                    page["ocr_printed_page_candidates"] = candidates
                    page["ocr_printed_label_status"] = "needs_review" if candidates else "not_found"
    # File bytes must still match the input that was parsed.
    if file_digest(pdf) != pdf_hash:
        raise ValueError("source_changed_during_conversion")
    (output/"document.md").write_bytes(markdown.encode())
    (output/"provenance.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+"\n")
    report = verify(pdf, output)
    write_report(report, output/"check-report.md")
    return ledger


def locate_quote(ledger: dict, quote: str) -> dict:
    needle = normalize(quote)
    if not needle:
        return {"status": "unsupported", "reason": "empty_quote", "candidates": []}
    candidates = []
    seen = set()
    for record in ledger["records"]:
        for source in record["sources"]:
            # Duplicate serialization of the same source is not another occurrence.
            if source["source_id"] in seen:
                continue
            seen.add(source["source_id"])
            for m in re.finditer("(?="+re.escape(needle)+")", normalize(source["text"])):
                candidates.append({"record_id": record["id"], "source_id": source["source_id"],
                                   "normalized_offset": m.start(),
                                   "locations": source["locations"],
                                   "verification": source["verification"]["status"]})
    if len(candidates) > 1:
        status = "ambiguous"
    elif candidates and candidates[0]["verification"] == "verified":
        status = "located_in_region"
    elif candidates and candidates[0]["verification"] == "needs_review":
        status = "needs_review"
    else:
        status = "unresolved"
    return {"status": status, "quote": quote, "candidates": candidates,
            "precision": "source_region_only_not_exact_quote_bbox"}


def verify(pdf: Path, bundle: Path, *, quote: str | None = None) -> dict:
    pdf = local_pdf(pdf)
    ledger = json.loads((bundle/"provenance.json").read_text())
    if ledger.get("schema_version") not in {1, SCHEMA}:
        raise ValueError("unsupported_schema_version")
    markdown_bytes = (bundle/"document.md").read_bytes()
    markdown = markdown_bytes.decode("utf-8")
    findings = []

    def finding(kind, rid=None, **detail):
        findings.append({"kind": kind, "record_id": rid, **detail})

    changed = file_digest(pdf) != ledger["document"]["sha256"]
    if changed:
        finding("source_changed", message="文件字节已变化，旧位置暂停认定有效；未判断内容变化范围")
    if digest(markdown_bytes) != ledger["markdown_sha256"]:
        finding("markdown_changed")
    if ledger["conversion"]["status"] != "success":
        finding("parser_conversion_not_success", conversion=ledger["conversion"])
    matches = list(BLOCK.finditer(markdown))
    grouped = {}
    for match in matches:
        grouped.setdefault(match[1], []).append(match)
    expected_ids = [r["id"] for r in ledger["records"]]
    if len(set(expected_ids)) != len(expected_ids):
        finding("duplicate_ledger_ids")
    for rid in grouped.keys()-set(expected_ids):
        finding("unknown_anchor", rid)
    remainder = BLOCK.sub("", markdown)
    if remainder != PROLOGUE+"\n\n"*len(matches):
        finding("untracked_markdown_or_broken_anchor")
    counts = Counter()
    with offline_guard(), PdfEvidence(pdf) as evidence:
        if len(evidence.pages) != ledger["document"]["page_count"]:
            finding("page_count_changed")
        for page in evidence.pages:
            if not page["native_text_available"]:
                ocr_on = ledger["parser"].get("ocr") in {"mac", True}
                finding("ocr_page_requires_review" if ocr_on else "unsupported_no_text_layer",
                        pdf_page=page["pdf_page"])
        native_page_meta = [{k: v for k, v in p.items() if not k.startswith("ocr_")}
                            for p in ledger["pages"]]
        if evidence.pages != native_page_meta and not changed:
            finding("page_metadata_changed")
        for gap in evidence.uncovered_native_text([
            s for r in ledger["records"] for s in r["sources"]
        ]):
            finding("native_text_not_covered", **gap)
        for page in evidence.pages:
            if page["printed_label_status"] == "ambiguous":
                finding("printed_page_label_ambiguous", pdf_page=page["pdf_page"],
                        candidates=page["printed_label_candidates"])
        if not ledger["records"]:
            finding("no_exported_records")
        for record in ledger["records"]:
            rid = record["id"]
            occurrences = grouped.get(rid, [])
            problems = []
            pending_review = False
            if source_binding(record["sources"]) != record.get("source_binding_sha256"):
                problems.append("provenance_changed")
            if digest(record["markdown_text"].encode()) != record["markdown_sha256"]:
                problems.append("excerpt_baseline_corrupt")
            if not occurrences:
                problems.append("anchor_missing")
            elif len(occurrences) != 1:
                problems.append("duplicate_anchor")
            else:
                actual = occurrences[0][2]
                if digest(actual.encode()) != record["markdown_sha256"]:
                    problems.append("excerpt_changed")
                export_check = check_serialization(actual, record["sources"])
                if export_check["status"] != "matched":
                    problems.append("export_source_text_mismatch")
                if occurrences[0].span(2) != tuple(record["markdown_range"]):
                    finding("markdown_range_shifted", rid)
            # Re-check the source geometry on the actual PDF; do not trust the
            # stored 'verified' flag. A changed source never inherits that flag.
            if not changed:
                if not record["sources"]:
                    problems.append("missing_provenance")
                for source in record["sources"]:
                    check = evidence.check_fragment(source)
                    if check["status"] == "needs_review":
                        finding("source_needs_review", rid, source_id=source["source_id"], check=check)
                        pending_review = True
                    elif check["status"] != "verified":
                        finding("source_unresolved", rid, source_id=source["source_id"], check=check)
                        problems.append("source_unresolved")
            else:
                problems.append("stale_source")
            for problem in dict.fromkeys(problems):
                finding(problem, rid)
            counts["invalid" if problems else "needs_review" if pending_review else "verified"] += 1
        duplicate_texts = {}
        for record in ledger["records"]:
            for source in record["sources"]:
                key = normalize(source["text"])
                if key:
                    duplicate_texts.setdefault(key, set()).add(source["source_id"])
        for text, refs in duplicate_texts.items():
            if len(refs) > 1:
                finding("repeated_source_text", text=text, occurrences=len(refs))
        query = None
        if quote is not None:
            query = locate_quote(ledger, quote)
            if changed:
                query["status"] = "stale_source"
            else:
                by_id = {s["source_id"]: s for r in ledger["records"] for s in r["sources"]}
                for candidate in query["candidates"]:
                    candidate["verification"] = evidence.check_fragment(
                        by_id[candidate["source_id"]])["status"]
                if len(query["candidates"]) == 1:
                    current = query["candidates"][0]["verification"]
                    query["status"] = {"verified": "located_in_region",
                                       "needs_review": "needs_review"}.get(current, "unresolved")
    if query is not None and query["status"] != "located_in_region":
        finding("query_"+query["status"])
    warning_only = {"repeated_source_text"}
    status = "issues_found" if any(f["kind"] not in warning_only for f in findings) else "ok"
    return {"schema_version": 1, "status": status, "document": ledger["document"]["filename"],
            "records_total": len(ledger["records"]), "counts": dict(counts),
            "source_changed": changed, "findings": findings, "query": query}


def write_report(report: dict, path: Path):
    lines = ["# 原文定位核对报告", "", f"文件：{report['document']}",
             f"核对状态：{report['status']}",
             f"摘录总数：{report['records_total']}；当前核验通过：{report['counts'].get('verified', 0)}；"
             f"待人工核对：{report['counts'].get('needs_review', 0)}；"
             f"失配或不支持：{report['counts'].get('invalid', 0)}。", "",
             "核验通过表示摘录关联区域的原生文字层通过核对，不证明司法真实性，也不等于扫描图像文字已核实。",
             "重复来源提示不否定已有直接关联；脱离关联的文字查询仍须检查全部候选。", "",
             "## 检查记录", ""]
    if not report["findings"]:
        lines.append("未发现本次检查范围内的问题。")
    for item in report["findings"]:
        lines.append("- "+json.dumps(item, ensure_ascii=False))
    if report.get("query") is not None:
        lines += ["", "## 摘录查询", "", "```json",
                  json.dumps(report["query"], ensure_ascii=False, indent=2), "```"]
    lines += ["", "## 检查范围", "",
              "原生文字层可独立核对；启用本地OCR的扫描内容仅保留待核对候选，不计为已核验。",
              "不自动拼接跨页表格。印刷页码只识别页脚中明确的“第…页”；扫描页码另列OCR候选。",
              "正文匹配仅忽略空白，不改写数字、标点或金额。位置可能为文本块或表格单元格，不伪称单字坐标。",
              "PDF 字节变化后须重新转换；无法仅凭文件哈希确定哪些摘录改变。",
              "本报告不检查签章、图像遮挡、隐藏文字层与可见图像一致性，也不提供防篡改签名。", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
