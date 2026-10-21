"""Known-answer evaluation only. Never called by production conversion/verification."""

from collections import Counter

from cntrace.core import normalize


def geometry_matches(loc, cp):
    if loc["pdf_page"] != cp["pdf_page"]:
        return False
    a, b = loc["bbox"], cp["bbox"]
    x, y = (b[0]+b[2])/2, (b[1]+b[3])/2
    return a[0]-2 <= x <= a[2]+2 and a[1]-2 <= y <= a[3]+2


def evaluate(document, ledger):
    sources = {s["source_id"]: s for r in ledger["records"] for s in r["sources"]}
    coverage = []
    false_successes = []
    for source in sources.values():
        if source["verification"]["status"] != "verified":
            continue
        if source["text_origin"] != "native_pdf_text":
            false_successes.append(source["source_id"])
            continue
        if not any(cp["text_origin"] == "native" and
                   (normalize(source["text"]) in normalize(cp["text"]) or
                    normalize(cp["text"]) in normalize(source["text"])) and
                   any(geometry_matches(loc, cp) for loc in source["locations"])
                   for cp in document["checkpoints"]):
            false_successes.append(source["source_id"])
    for cp in document["checkpoints"]:
        expected = "verified" if cp["text_origin"] == "native" else "needs_review"
        matched = [s["source_id"] for s in sources.values()
                   if s["verification"]["status"] == expected and
                   normalize(cp["text"]) in normalize(s["text"]) and
                   any(geometry_matches(loc, cp) for loc in s["locations"])]
        coverage.append({"checkpoint": cp["id"], "origin": cp["text_origin"],
                         "pdf_page": cp["pdf_page"], "expected_text": cp["text"],
                         "covered": bool(matched), "sources": matched,
                         "nearby_parser_text": [s["text"] for s in sources.values()
                             if any(geometry_matches(loc, cp) for loc in s["locations"])]})
    def metric(origin):
        items = [x for x in coverage if x["origin"] == origin]
        return {"total": len(items), "covered": sum(x["covered"] for x in items),
                "rate": sum(x["covered"] for x in items)/len(items) if items else None}
    return {"pdf": document["pdf"], "records": len(ledger["records"]),
            "record_status": dict(Counter(r["status"] for r in ledger["records"])),
            "source_status": dict(Counter(s["verification"]["status"] for s in sources.values())),
            "false_successes": false_successes, "native_region_points": metric("native"),
            "ocr_candidate_points": metric("ocr"), "coverage": coverage,
            "warning": "OCR candidate coverage is not production verification or general accuracy"}
